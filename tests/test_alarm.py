# =================================================================================2
#       Copyright (c) 2020 AT&T Intellectual Property.
#       Copyright (c) 2020 Nokia
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
import pytest
import time
from ricxappframe.alarm import alarm
from ricxappframe.alarm.alarm import AlarmAction, AlarmDetail, AlarmManager, AlarmSeverity, ALARM_MGR_SERVICE_NAME_ENV, ALARM_MGR_SERVICE_PORT_ENV
from ricxappframe.alarm.exceptions import InitFailed
from ricxappframe.rmr import rmr

MRC_SEND = None
MRC_RCV = None
SIZE = 256


def setup_module():
    """
    test alarm module setup
    """
    global MRC_SEND
    MRC_SEND = rmr.rmr_init(b"4566", rmr.RMR_MAX_RCV_BYTES, 0x00)
    while rmr.rmr_ready(MRC_SEND) == 0:
        time.sleep(1)

    global MRC_RCV
    MRC_RCV = rmr.rmr_init(b"4567", rmr.RMR_MAX_RCV_BYTES, 0x00)
    while rmr.rmr_ready(MRC_RCV) == 0:
        time.sleep(1)


def teardown_module():
    """
    test alarm module teardown
    """
    rmr.rmr_close(MRC_SEND)


def test_alarm_set_get(monkeypatch):
    """
    test set functions
    """
    act = AlarmAction.RAISE
    assert act is not None

    sev = AlarmSeverity.CRITICAL
    assert sev is not None

    det = AlarmDetail("1", "2", 3, AlarmSeverity.MINOR, "4", "5")
    assert det[alarm.KEY_MANAGED_OBJECT_ID] == "1"
    assert det[alarm.KEY_APPLICATION_ID] == "2"
    assert det[alarm.KEY_SPECIFIC_PROBLEM] == 3
    assert det[alarm.KEY_PERCEIVED_SEVERITY] == AlarmSeverity.MINOR.name
    assert det[alarm.KEY_IDENTIFYING_INFO] == "4"
    assert det[alarm.KEY_ADDITIONAL_INFO] == "5"

    # missing environment variables
    with pytest.raises(InitFailed):
        alarm.AlarmManager(MRC_SEND, "missing", "envvars")

    # invalid environment variables
    monkeypatch.setenv(ALARM_MGR_SERVICE_NAME_ENV, "0")
    monkeypatch.setenv(ALARM_MGR_SERVICE_PORT_ENV, "a")
    with pytest.raises(InitFailed):
        alarm.AlarmManager(MRC_SEND, "bogus", "envvars")

    # good environment variables
    monkeypatch.setenv(ALARM_MGR_SERVICE_NAME_ENV, "localhost")
    monkeypatch.setenv(ALARM_MGR_SERVICE_PORT_ENV, "4567")  # any int is ok here
    mgr = alarm.AlarmManager(MRC_SEND, "moid2", "appid2")
    assert mgr is not None
    assert mgr.managed_object_id == "moid2"
    assert mgr.application_id == "appid2"


def _receive_alarm_msg(action: AlarmAction):
    """
    delays briefly, receives a message, checks the message type and action
    """
    time.sleep(0.5)
    sbuf_rcv = rmr.rmr_alloc_msg(MRC_RCV, SIZE)
    sbuf_rcv = rmr.rmr_torcv_msg(MRC_RCV, sbuf_rcv, 2000)
    rcv_summary = rmr.message_summary(sbuf_rcv)
    assert rcv_summary[rmr.RMR_MS_MSG_STATE] == rmr.RMR_OK
    assert rcv_summary[rmr.RMR_MS_MSG_TYPE] == alarm.RIC_ALARM_UPDATE
    # parse JSON
    data = json.loads(rcv_summary[rmr.RMR_MS_PAYLOAD].decode())
    assert data[alarm.KEY_ALARM_ACTION] == action.name


def test_alarm_manager(monkeypatch):
    """
    test send functions and ensure a message arrives
    """
    monkeypatch.setenv(ALARM_MGR_SERVICE_NAME_ENV, "localhost")
    monkeypatch.setenv(ALARM_MGR_SERVICE_PORT_ENV, "4567")  # must match rcv port above
    mgr = AlarmManager(MRC_SEND, "moid", "appid")
    assert mgr is not None

    det = mgr.create_alarm(3, AlarmSeverity.DEFAULT, "identifying", "additional")
    assert det is not None

    success = mgr.raise_alarm(det)
    assert success
    _receive_alarm_msg(AlarmAction.RAISE)

    success = mgr.clear_alarm(det)
    assert success
    _receive_alarm_msg(AlarmAction.CLEAR)

    success = mgr.reraise_alarm(det)
    assert success
    _receive_alarm_msg(AlarmAction.CLEAR)
    _receive_alarm_msg(AlarmAction.RAISE)

    success = mgr.clear_all_alarms()
    assert success
    _receive_alarm_msg(AlarmAction.CLEARALL)
