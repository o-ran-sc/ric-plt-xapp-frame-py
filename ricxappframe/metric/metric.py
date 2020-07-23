# ==================================================================================
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
"""
Provides classes and methods to define and send metrics as RMR messages to a
central collector. Message destination(s) are controlled by the RMR routing table.
Message contents must comply with the JSON schema in file metric-schema.json.
"""

from ctypes import c_void_p
import json
import time
from mdclogpy import Logger
from ricxappframe.rmr import rmr
from ricxappframe.metric.exceptions import EmptyReport

##############
# PRIVATE API
##############

mdc_logger = Logger(name=__name__)
RETRIES = 4

##############
# PUBLIC API
##############

# constants
RIC_METRICS = 120  # message type

# Publish dict keys as constants for convenience of client code.
KEY_REPORTER = "reporter"
KEY_GENERATOR = "generator"
KEY_TIMESTAMP = "timestamp"
KEY_DATA = "data"
KEY_DATA_ID = "id"
KEY_DATA_TYPE = "type"
KEY_DATA_VALUE = "value"


class MetricData(dict):
    """
    A single measurement with ID, value and (optionally) type.
    """
    def __init__(self,
                 id: str,
                 value: str,
                 type: str = None):
        """
        Creates a data item with the specified members.

        Parameters
        ----------
        id: str (required)
            Metric ID

        value: str (required)
            Metric value; e.g., 1.

        type: str (optional)
            Metric type; e.g., "counter".
        """
        dict.__init__(self)
        self[KEY_DATA_ID] = id
        self[KEY_DATA_VALUE] = value
        self[KEY_DATA_TYPE] = type


class MetricsReport(dict):
    """
    A list of metric data items with identifying information.
    At init sets the timestamp to the current system time in
    milliseconds since the Epoch.

    Parameters
    ----------
    reporter: str (optional)
        The system that reports the data

    generator: str (optional)
        The generator that reports the data

    items: List of MetricData (optional)
        The data items for the report
    """
    def __init__(self,
                 reporter: str = None,
                 generator: str = None,
                 items: list = None):
        """
        Creates an object with the specified details and items.
        """
        dict.__init__(self)
        self[KEY_REPORTER] = reporter
        self[KEY_GENERATOR] = generator
        self[KEY_TIMESTAMP] = int(round(time.time() * 1000))
        self[KEY_DATA] = [] if items is None else items

    def add_metric(self,
                   data: MetricData):
        """
        Convenience method that adds a data item to the report.

        Parameters
        ----------
        data: MetricData
            A measurement to add to the report
        """
        self[KEY_DATA].append(data)


class MetricsManager:
    """
    Provides an API for an Xapp to build and send measurement reports
    by sending messages via RMR routing to a metrics adapter/collector.

    Parameters
    ----------
    vctx: ctypes c_void_p (required)
        Pointer to RMR context obtained by initializing RMR.
        The context is used to allocate space and send messages.

    reporter: str (optional)
        The source of the measurement; e.g., a temperature probe

    generator: str (optional)
        The system that collected and sent the measurement; e.g., an environment monitor.
    """
    def __init__(self,
                 vctx: c_void_p,
                 reporter: str = None,
                 generator: str = None):
        """
        Creates a metrics manager.
        """
        self.vctx = vctx
        self.reporter = reporter
        self.generator = generator

    def create_report(self,
                      items: list = None):
        """
        Creates a MetricsReport object with the specified metrics data items.

        Parameters
        ----------
        items: list (optional)
            List of MetricData items

        Returns
        -------
        MetricsReport
        """
        return MetricsReport(self.reporter, self.generator, items)

    def send_report(self, msg: MetricsReport):
        """
        Serializes the MetricsReport dict to JSON and sends the result via RMR.
        Raises an exception if the report has no MetricsData items.

        Parameters
        ----------
        msg: MetricsReport (required)
            Dictionary with measurement data to encode and send

        Returns
        -------
        bool
            True if the send succeeded (possibly with retries), False otherwise
        """
        if KEY_DATA not in msg or len(msg[KEY_DATA]) == 0:
            raise EmptyReport
        payload = json.dumps(msg).encode()
        mdc_logger.debug("send_report: payload is {}".format(payload))
        sbuf = rmr.rmr_alloc_msg(vctx=self.vctx, size=len(payload), payload=payload,
                                 mtype=RIC_METRICS, gen_transaction_id=True)

        for _ in range(0, RETRIES):
            sbuf = rmr.rmr_send_msg(self.vctx, sbuf)
            post_send_summary = rmr.message_summary(sbuf)
            mdc_logger.debug("send_report: try {0} result is {1}".format(_, post_send_summary[rmr.RMR_MS_MSG_STATE]))
            # stop trying if RMR does not indicate retry
            if post_send_summary[rmr.RMR_MS_MSG_STATE] != rmr.RMR_ERR_RETRY:
                break

        rmr.rmr_free_msg(sbuf)
        if post_send_summary[rmr.RMR_MS_MSG_STATE] != rmr.RMR_OK:
            mdc_logger.warning("send_report: failed after {} retries".format(RETRIES))
            return False

        return True

    def send_metrics(self, items: list):
        """
        Convenience method that creates a MetricsReport object with the specified
        metrics data items and sends it to the metrics adapter/collector.

        Parameters
        ----------
        items: list (required)
            List of MetricData items

        Returns
        -------
        bool
            True if the send succeeded (possibly with retries), False otherwise
        """
        return self.send_report(self.create_report(items))
