# ==================================================================================
#       Copyright (c) 2020 Nokia
#       Copyright (c) 2020 AT&T Intellectual Property.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# ==================================================================================
import json
import time
from contextlib import suppress
import requests
from unittest.mock import Mock
from ricxappframe.util.constants import Constants
from ricxappframe.xapp_frame import _BaseXapp, Xapp, RMRXapp
from ricxappframe.constants import sdl_namespaces

import ricxappframe.entities.rnib.nb_identity_pb2 as pb_nb

rmr_xapp = None
rmr_xapp_health = None
gen_xapp = None
rnib_xapp = None


mock_post_200 = Mock(return_value=Mock(status_code=200, text='Mocked response'))
mock_post_204 = Mock(return_value=Mock(status_code=204, text='Mocked response'))


def test_rmr_init(monkeypatch):

    # test variables
    def_pay = None
    sixty_pay = None

    # create rmr app

    def default_handler(self, summary, sbuf):
        nonlocal def_pay
        def_pay = json.loads(summary["payload"])
        self.rmr_free(sbuf)

    def sixtythou_handler(self, summary, sbuf):
        nonlocal sixty_pay
        sixty_pay = json.loads(summary["payload"])
        self.rmr_free(sbuf)

    global rmr_xapp
    monkeypatch.setattr(requests.Session, 'post', mock_post_200)
    rmr_xapp = RMRXapp(default_handler, rmr_port=4564, use_fake_sdl=True)
    rmr_xapp.register_callback(sixtythou_handler, 60000)
    rmr_xapp.run(thread=True)  # in unit tests we need to thread here or else execution is not returned!

    time.sleep(1)

    # create a general xapp that will demonstrate some SDL functionality and launch some requests against the rmr xapp

    def entry(self):
        self.sdl_set("testns", "mykey", 6)
        assert self.sdl_get("testns", "mykey") == 6
        assert self.sdl_find_and_get("testns", "myk") == {"mykey": 6}
        assert self.healthcheck()

        val = json.dumps({"test send 60000": 1}).encode()
        self.rmr_send(val, 60000)

        val = json.dumps({"test send 60001": 2}).encode()
        self.rmr_send(val, 60001)

        self.sdl_delete("testns", "bogus")

    global gen_xapp
    gen_xapp = Xapp(xapp_ready_cb=entry, use_fake_sdl=True)
    gen_xapp.run()

    time.sleep(1)

    assert def_pay == {"test send 60001": 2}
    assert sixty_pay == {"test send 60000": 1}


def test_rmr_healthcheck(monkeypatch):
    # thanos uses the rmr xapp to healthcheck the rmr xapp

    # test variables
    health_pay = None

    def post_init(self):
        self.rmr_send(b"", Constants.RIC_HEALTH_CHECK_REQ)

    def default_handler(self, summary, sbuf):
        pass

    global rmr_xapp_health
    monkeypatch.setattr(requests.Session, 'post', mock_post_200)
    rmr_xapp_health = RMRXapp(default_handler, post_init=post_init, rmr_port=4666, use_fake_sdl=True)

    def health_handler(self, summary, sbuf):
        nonlocal health_pay
        health_pay = summary["payload"]
        self.rmr_free(sbuf)

    rmr_xapp_health.register_callback(health_handler, Constants.RIC_HEALTH_CHECK_RESP)
    rmr_xapp_health.run(thread=True)  # in unit tests we need to thread here or else execution is not returned!

    time.sleep(1)

    assert health_pay == b"OK\n"


def test_rnib_get_list_nodeb(rnib_information, monkeypatch):
    global rnib_xapp
    monkeypatch.setattr(requests.Session, 'post', mock_post_200)
    rnib_xapp = _BaseXapp(rmr_port=4777, use_fake_sdl=True)

    # Test there is no rnib information.
    gnb_list = rnib_xapp.get_list_gnb_ids()
    enb_list = rnib_xapp.get_list_enb_ids()
    assert len(gnb_list) == 0
    assert len(enb_list) == 0

    # Add rnib information directly.
    for rnib in rnib_information:
        rnib_xapp.sdl.add_member(sdl_namespaces.E2_MANAGER, "ENB", rnib, usemsgpack=False)
        rnib_xapp.sdl.add_member(sdl_namespaces.E2_MANAGER, "GNB", rnib, usemsgpack=False)

    gnb_list = rnib_xapp.get_list_gnb_ids()
    assert len(gnb_list) == len(rnib_information)
    for gnb in gnb_list:
        assert gnb.SerializeToString() in rnib_information

    enb_list = rnib_xapp.get_list_enb_ids()
    assert len(enb_list) == len(rnib_information)
    for enb in enb_list:
        assert enb.SerializeToString() in rnib_information

    monkeypatch.setattr(requests.Session, 'post', mock_post_204)
    rnib_xapp.stop()


def test_rnib_get_list_all_nodeb(rnib_information, monkeypatch):
    global rnib_xapp
    monkeypatch.setattr(requests.Session, 'post', mock_post_200)
    rnib_xapp = _BaseXapp(rmr_port=4777, use_fake_sdl=True)

    # Add rnib information directly.
    for rnib in rnib_information:
        rnib_xapp.sdl.add_member(sdl_namespaces.E2_MANAGER, "GNB", rnib, usemsgpack=False)

    nb_list = rnib_xapp.GetListNodebIds()
    assert len(nb_list) == 2

    for rnib in rnib_information:
        rnib_xapp.sdl.add_member(sdl_namespaces.E2_MANAGER, "ENB", rnib, usemsgpack=False)

    nb_list = rnib_xapp.GetListNodebIds()
    assert len(nb_list) == 4

    monkeypatch.setattr(requests.Session, 'post', mock_post_204)
    rnib_xapp.stop()


def test_rnib_get_list_cells(rnib_cellinformation, monkeypatch):
    global rnib_xapp
    monkeypatch.setattr(requests.Session, 'post', mock_post_200)
    rnib_xapp = _BaseXapp(rmr_port=4777, use_fake_sdl=True)

    mynb = pb_nb.NbIdentity()
    mynb.inventory_name = "nodeb_1234"
    mynb.global_nb_id.plmn_id = "plmn_1234"
    mynb.global_nb_id.nb_id = "nb_1234"
    mynb.connection_status = 1
    rnib_xapp.sdl.add_member(sdl_namespaces.E2_MANAGER, "ENB", mynb.SerializeToString(), usemsgpack=False)

    # Add rnib information directly.
    for rnib in rnib_cellinformation:
        rnib_xapp.sdl.add_member(sdl_namespaces.E2_MANAGER, "ENBCELL1", rnib, usemsgpack=False)
        rnib_xapp.sdl.add_member(sdl_namespaces.E2_MANAGER, "ENBCELL2", rnib, usemsgpack=False)

    monkeypatch.setattr(requests.Session, 'post', mock_post_204)
    rnib_xapp.stop()


def test_rnib_get_nodeb(rnib_helpers, monkeypatch):
    global rnib_xapp
    monkeypatch.setattr(requests.Session, 'post', mock_post_200)
    rnib_xapp = _BaseXapp(rmr_port=4777, use_fake_sdl=True)
    nb1 = rnib_helpers.createNodebInfo('nodeb_1234', 'GNB', '192.168.1.1', 8088)
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "RAN:" + 'nodeb_1234', nb1.SerializeToString(), usemsgpack=False)
    nb2 = rnib_helpers.createNodebInfo('nodeb_1234', 'ENB', '192.168.1.2', 8088)
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "RAN:" + 'nodeb_1235', nb2.SerializeToString(), usemsgpack=False)

    gnb = rnib_xapp.GetNodeb('nodeb_1235')
    assert gnb == nb2
    gnb = rnib_xapp.GetNodeb('nodeb_1234')
    assert gnb == nb1
    gnb = rnib_xapp.GetNodeb('nodeb_1230')
    assert gnb is None

    monkeypatch.setattr(requests.Session, 'post', mock_post_204)
    rnib_xapp.stop()


def test_rnib_get_cell(rnib_helpers, monkeypatch):
    global rnib_xapp
    monkeypatch.setattr(requests.Session, 'post', mock_post_200)
    rnib_xapp = _BaseXapp(rmr_port=4777, use_fake_sdl=True)
    c1 = rnib_helpers.createCell('c1234', 8)
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "PCI:c1234:08", c1.SerializeToString(), usemsgpack=False)
    c2 = rnib_helpers.createCell('c1235', 11)
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "PCI:c1235:0b", c2.SerializeToString(), usemsgpack=False)

    cell = rnib_xapp.GetCell('c1235', 11)
    assert cell == c2
    cell = rnib_xapp.GetCell('c1234', 8)
    assert cell == c1
    cell = rnib_xapp.GetCell('c1236', 11)
    assert cell is None

    monkeypatch.setattr(requests.Session, 'post', mock_post_204)
    rnib_xapp.stop()


def test_rnib_get_cell_by_id(rnib_helpers, monkeypatch):
    global rnib_xapp
    monkeypatch.setattr(requests.Session, 'post', mock_post_200)
    rnib_xapp = _BaseXapp(rmr_port=4777, use_fake_sdl=True)
    c1 = rnib_helpers.createCell('c1234', 8)
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "CELL:c1234", c1.SerializeToString(), usemsgpack=False)
    c2 = rnib_helpers.createCell('c1235', 11)
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "CELL:c1235", c2.SerializeToString(), usemsgpack=False)

    cell = rnib_xapp.GetCellById('LTE_CELL', 'c1235')
    assert cell == c2
    cell = rnib_xapp.GetCellById('LTE_CELL', 'c1234')
    assert cell == c1
    cell = rnib_xapp.GetCellById('LTE_CELL', 'c1236')
    assert cell is None

    monkeypatch.setattr(requests.Session, 'post', mock_post_204)
    rnib_xapp.stop()


def test_rnib_get_cells(rnib_helpers, monkeypatch):
    global rnib_xapp
    monkeypatch.setattr(requests.Session, 'post', mock_post_200)
    rnib_xapp = _BaseXapp(rmr_port=4777, use_fake_sdl=True)
    nb1 = rnib_helpers.createNodebInfo('nodeb_1234', 'GNB', '192.168.1.1', 8088)
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "RAN:" + 'nodeb_1234', nb1.SerializeToString(), usemsgpack=False)
    nb2 = rnib_helpers.createNodebInfo('nodeb_1234', 'ENB', '192.168.1.2', 8088)
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "RAN:" + 'nodeb_1235', nb2.SerializeToString(), usemsgpack=False)

    sc = rnib_xapp.GetCellList('nodeb_1235')
    assert sc == nb2.enb.served_cells
    sc = rnib_xapp.GetCellList('nodeb_1234')
    assert sc == nb1.gnb.served_nr_cells
    sc = rnib_xapp.GetCellList('nodeb_1230')
    assert sc is None

    monkeypatch.setattr(requests.Session, 'post', mock_post_204)
    rnib_xapp.stop()


def test_rnib_get_global_nodeb(rnib_helpers, monkeypatch):
    global rnib_xapp
    monkeypatch.setattr(requests.Session, 'post', mock_post_200)
    rnib_xapp = _BaseXapp(rmr_port=4777, use_fake_sdl=True)
    nb1 = rnib_helpers.createNodeb('nodeb_1234', '358', 'nb_1234')
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "GNB:" + '358:' + 'nodeb_1234', nb1.SerializeToString(), usemsgpack=False)
    nb2 = rnib_helpers.createNodeb('nodeb_1235', '356', 'nb_1235')
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "GNB:" + '356:' + 'nodeb_1235', nb2.SerializeToString(), usemsgpack=False)

    gnb = rnib_xapp.GetNodebByGlobalNbId('GNB', '356', 'nodeb_1235')
    assert gnb == nb2
    gnb = rnib_xapp.GetNodebByGlobalNbId('GNB', '358', 'nodeb_1234')
    assert gnb == nb1
    gnb = rnib_xapp.GetNodebByGlobalNbId('GNB', '356', 'nodeb_1230')
    assert gnb is None

    monkeypatch.setattr(requests.Session, 'post', mock_post_204)
    rnib_xapp.stop()


def test_rnib_get_ranfunction(rnib_helpers, monkeypatch):
    global rnib_xapp
    monkeypatch.setattr(requests.Session, 'post', mock_post_200)
    rnib_xapp = _BaseXapp(rmr_port=4777, use_fake_sdl=True)
    nb1 = rnib_helpers.createNodebInfo('nodeb_1234', 'GNB', '192.168.1.1', 8088)
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "RAN:" + 'nodeb_1234', nb1.SerializeToString(), usemsgpack=False)
    nb2 = rnib_helpers.createNodebInfo('nodeb_1235', 'GNB', '192.168.1.2', 8088)
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "RAN:" + 'nodeb_1235', nb2.SerializeToString(), usemsgpack=False)
    nb3 = rnib_helpers.createNodebInfo('nodeb_1236', 'GNB', '192.168.1.2', 8088)
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "RAN:" + 'nodeb_1236', nb3.SerializeToString(), usemsgpack=False)
    nb4 = rnib_helpers.createNodebInfo('nodeb_1237', 'GNB', '192.168.1.2', 8088)
    rnib_xapp.sdl.set(sdl_namespaces.E2_MANAGER, "RAN:" + 'nodeb_1237', nb4.SerializeToString(), usemsgpack=False)

    sc = rnib_xapp.GetRanFunctionDefinition('nodeb_1235', "1.3.6.1.4.1.1.2.2.2")
    assert sc == ['te524367153']
    sc = rnib_xapp.GetRanFunctionDefinition('nodeb_1235', "1.3.6.1.4.1.1.2.2.5")
    assert sc == []

    monkeypatch.setattr(requests.Session, 'post', mock_post_204)
    rnib_xapp.stop()


def teardown_module():
    """
    this is like a "finally"; the name of this function is pytest magic
    safer to put down here since certain failures above can lead to pytest never returning
    for example if an exception gets raised before stop is called in any test function above, pytest will hang forever
    """
    with suppress(Exception):
        gen_xapp.stop()
    with suppress(Exception):
        rmr_xapp.stop()
    with suppress(Exception):
        rmr_xapp_health.stop()
