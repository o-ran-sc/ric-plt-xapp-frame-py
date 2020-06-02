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
import time
from ricxappframe.alarm import alarm
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


def test_alarm_set_get():
    """
    test set functions
    """
    act = alarm.AlarmAction.RAISE
    assert act is not None

    sev = alarm.AlarmSeverity.CRITICAL
    assert sev is not None

    det = alarm.AlarmDetail("1", "2", 3, alarm.AlarmSeverity.MINOR, "4", "5")
    assert det['managedObjectId'] == "1"
    assert det['applicationId'] == "2"
    assert det['specificProblem'] == 3
    assert det['perceivedSeverity'] == alarm.AlarmSeverity.MINOR.name
    assert det['additionalInfo'] == "4"
    assert det['identifyingInfo'] == "5"

    mgr = alarm.AlarmManager(MRC_SEND, "moid", "appid")
    assert mgr is not None
    appid = "appid2"
    mgr.setApplicationId(appid)
    assert mgr.applicationId == appid
    moid = "moid2"
    mgr.setManagedObjectId(moid)
    assert mgr.managedObjectId == moid


def _receive_alarm_msg():
    """
    delays briefly, receives a message, and asserts it's an alarm
    """
    time.sleep(0.5)
    sbuf_rcv = rmr.rmr_alloc_msg(MRC_RCV, SIZE)
    sbuf_rcv = rmr.rmr_torcv_msg(MRC_RCV, sbuf_rcv, 2000)
    rcv_summary = rmr.message_summary(sbuf_rcv)
    assert rcv_summary[rmr.RMR_MS_MSG_STATE] == rmr.RMR_OK
    assert rcv_summary[rmr.RMR_MS_MSG_TYPE] == alarm.RIC_ALARM_UPDATE


def test_alarm_manager():
    """
    test send functions and ensure a message arrives
    """
    mgr = alarm.AlarmManager(MRC_SEND, "moid", "appid")
    assert mgr is not None

    det = mgr.create_alarm(3, alarm.AlarmSeverity.DEFAULT, "additional", "identifying")
    assert det is not None

    success = mgr.raise_alarm(det)
    assert success is True
    _receive_alarm_msg()

    success = mgr.clear_alarm(det)
    assert success is True
    _receive_alarm_msg()

    success = mgr.reraise_alarm(det)
    assert success is True
    _receive_alarm_msg()
    _receive_alarm_msg()

    success = mgr.clear_all_alarms()
    assert success is True
    _receive_alarm_msg()
