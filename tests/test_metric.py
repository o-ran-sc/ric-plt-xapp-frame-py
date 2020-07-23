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
from mdclogpy import Logger
from ricxappframe.metric import metric
from ricxappframe.metric.exceptions import EmptyReport
from ricxappframe.metric.metric import MetricData, MetricsReport, MetricsManager
from ricxappframe.rmr import rmr

mdc_logger = Logger(name=__name__)
MRC_SEND = None
MRC_RCV = None
SIZE = 256


def setup_module():
    """
    test metric module setup
    """
    global MRC_SEND
    MRC_SEND = rmr.rmr_init(b"4568", rmr.RMR_MAX_RCV_BYTES, 0x00)
    while rmr.rmr_ready(MRC_SEND) == 0:
        time.sleep(1)

    global MRC_RCV
    MRC_RCV = rmr.rmr_init(b"4569", rmr.RMR_MAX_RCV_BYTES, 0x00)
    while rmr.rmr_ready(MRC_RCV) == 0:
        time.sleep(1)

    # let all the RMR output appear
    time.sleep(2)
    mdc_logger.debug("RMR instances initialized")


def teardown_module():
    """
    test metric module teardown
    """
    mdc_logger.debug("Closing RMR instances")
    rmr.rmr_close(MRC_SEND)
    rmr.rmr_close(MRC_RCV)


def test_metric_set_get(monkeypatch):
    mdc_logger.debug("Testing set functions")
    md = MetricData("id", "value", "type")
    assert md[metric.KEY_DATA_ID] == "id"
    assert md[metric.KEY_DATA_VALUE] == "value"
    assert md[metric.KEY_DATA_TYPE] == "type"

    mr = MetricsReport("reporter", "generator", [md])
    assert mr[metric.KEY_REPORTER] == "reporter"
    assert mr[metric.KEY_GENERATOR] == "generator"
    assert len(mr[metric.KEY_DATA]) == 1
    assert mr[metric.KEY_DATA][0] == md

    mgr = metric.MetricsManager(MRC_SEND, "reporter", "generator")
    assert mgr is not None
    assert mgr.reporter == "reporter"
    assert mgr.generator == "generator"

    mr = MetricsReport("empty", "empty", [])
    with pytest.raises(EmptyReport):
        mgr.send_report(mr)


def _receive_metric_rpt(rptr: str):
    """
    delays briefly, receives a message, checks the message type and reporter
    """
    time.sleep(0.5)
    sbuf_rcv = rmr.rmr_alloc_msg(MRC_RCV, SIZE)
    sbuf_rcv = rmr.rmr_torcv_msg(MRC_RCV, sbuf_rcv, 2000)
    rcv_summary = rmr.message_summary(sbuf_rcv)
    mdc_logger.debug("Receive result is {}".format(rcv_summary[rmr.RMR_MS_MSG_STATE]))
    assert rcv_summary[rmr.RMR_MS_MSG_STATE] == rmr.RMR_OK
    assert rcv_summary[rmr.RMR_MS_MSG_TYPE] == metric.RIC_METRICS
    # parse JSON
    data = json.loads(rcv_summary[rmr.RMR_MS_PAYLOAD].decode())
    mdc_logger.debug("Received reporter {}".format(data[metric.KEY_REPORTER]))
    assert data[metric.KEY_REPORTER] == rptr


def test_metrics_manager():
    """
    test send functions and ensure a message arrives
    """
    mdc_logger.debug("Testing metrics-send functions")
    rptr = "metr"

    mgr = MetricsManager(MRC_SEND, rptr, "generator")
    assert mgr is not None

    md = MetricData("id", "value", "type")
    assert md is not None

    success = mgr.send_metrics([md])
    assert success
    _receive_metric_rpt(rptr)
