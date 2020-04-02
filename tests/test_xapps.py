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
from ricxappframe.xapp_frame import Xapp, RMRXapp, RIC_HEALTH_CHECK_REQ, RIC_HEALTH_CHECK_RESP

rmr_xapp = None
rmr_xapp_health = None
gen_xapp = None


def test_rmr_init():

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
    rmr_xapp = RMRXapp(default_handler, rmr_port=4564, use_fake_sdl=True)
    rmr_xapp.register_callback(sixtythou_handler, 60000)
    rmr_xapp.run(thread=True)  # in unit tests we need to thread here or else execution is not returned!

    time.sleep(1)

    # create a general xapp that will demonstrate some SDL functionality and launch some requests against the rmr xapp

    def entry(self):

        time.sleep(1)

        self.sdl_set("testns", "mykey", 6)
        assert self.sdl_get("testns", "mykey") == 6
        assert self.sdl_find_and_get("testns", "myk") == {"mykey": 6}
        assert self.healthcheck()

        val = json.dumps({"test send 60000": 1}).encode()
        self.rmr_send(val, 60000)

        val = json.dumps({"test send 60001": 2}).encode()
        self.rmr_send(val, 60001)

    global gen_xapp
    gen_xapp = Xapp(entrypoint=entry, use_fake_sdl=True)
    gen_xapp.run()

    time.sleep(1)

    assert def_pay == {"test send 60001": 2}
    assert sixty_pay == {"test send 60000": 1}


def test_rmr_healthcheck():
    # thanos uses the rmr xapp to healthcheck the rmr xapp

    # test variables
    health_pay = None

    def post_init(self):
        self.rmr_send(b"", RIC_HEALTH_CHECK_REQ)

    def default_handler(self, summary, sbuf):
        pass

    global rmr_xapp_health
    rmr_xapp_health = RMRXapp(default_handler, post_init=post_init, rmr_port=4666, use_fake_sdl=True)

    def health_handler(self, summary, sbuf):
        nonlocal health_pay
        health_pay = summary["payload"]
        self.rmr_free(sbuf)

    rmr_xapp_health.register_callback(health_handler, RIC_HEALTH_CHECK_RESP)
    rmr_xapp_health.run(thread=True)  # in unit tests we need to thread here or else execution is not returned!

    time.sleep(1)

    assert health_pay == b"OK\n"


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
