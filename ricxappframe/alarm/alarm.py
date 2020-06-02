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
Provides classes and methods to define, raise, reraise and clear alarms.
All actions are implemented by sending RMR messages to the Alarm Adapter.
"""

from ctypes import c_void_p
from enum import Enum, auto
import json
import time
from mdclogpy import Logger
from ricxappframe.rmr import rmr

##############
# PRIVATE API
##############

mdc_logger = Logger(name=__name__)
RETRIES = 4

##############
# PUBLIC API
##############

# constants
RIC_ALARM_UPDATE = 13111
# RIC_ALARM_QUERY = 13112 # TBD

# Publish dict keys as constants for convenience of client code.
# Mixed lower/upper casing to comply with the Adapter JSON requirements.
KEY_ALARM = "alarm"
KEY_MANAGED_OBJECT_ID = "managedObjectId"
KEY_APPLICATION_ID = "applicationId"
KEY_SPECIFIC_PROBLEM = "specificProblem"
KEY_PERCEIVED_SEVERITY = "perceivedSeverity"
KEY_ADDITIONAL_INFO = "additionalInfo"
KEY_IDENTIFYING_INFO = "identifyingInfo"
KEY_ALARM_ACTION = "AlarmAction"
KEY_ALARM_TIME = "AlarmTime"


class AlarmAction(Enum):
    """
    Action to perform at the Alarm Adapter
    """
    RAISE = auto()
    CLEAR = auto()
    CLEARALL = auto()


class AlarmSeverity(Enum):
    """
    Severity of an alarm
    """
    UNSPECIFIED = auto()
    CRITICAL = auto()
    MAJOR = auto()
    MINOR = auto()
    WARNING = auto()
    CLEARED = auto()
    DEFAULT = auto()


class AlarmDetail(dict):
    """
    An alarm that can be raised or cleared.

    Parameters
    ----------
    managed_object_id: str
        The name of the managed object that is the cause of the fault (required)

    application_id: str
        The name of the process that raised the alarm (required)

    specific_problem: int
        The problem that is the cause of the alarm

    perceived_severity: AlarmSeverity
        The severity of the alarm, a value from the enum.

    identifying_info: str
        Identifying additional information, which is part of alarm identity

    additional_info: str
        Additional information given by the application (optional)
    """
    # pylint: disable=too-many-arguments
    def __init__(self,
                 managed_object_id: str,
                 application_id: str,
                 specific_problem: int,
                 perceived_severity: AlarmSeverity,
                 identifying_info: str,
                 additional_info: str = ""):
        """
        Creates an object with the specified items.
        """
        dict.__init__(self)
        self[KEY_MANAGED_OBJECT_ID] = managed_object_id
        self[KEY_APPLICATION_ID] = application_id
        self[KEY_SPECIFIC_PROBLEM] = specific_problem
        self[KEY_PERCEIVED_SEVERITY] = perceived_severity.name
        self[KEY_IDENTIFYING_INFO] = identifying_info
        self[KEY_ADDITIONAL_INFO] = additional_info


class AlarmManager:
    """
    Provides an API for an Xapp to raise and clear alarms by sending messages
    via RMR, which should route the messages to an Alarm Adapter.

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context obtained by initializing RMR.
        The context is used to allocate space and send messages.
        The RMR routing table must have a destination for message
        type RIC_ALARM_UPDATE as defined in this module.

    managed_object_id: str
        The name of the managed object that raises alarms

    application_id: str
        The name of the process that raises alarms
    """
    def __init__(self,
                 vctx: c_void_p,
                 managed_object_id: str,
                 application_id: str):
        """
        Creates an alarm manager.
        """
        self.vctx = vctx
        self.managed_object_id = managed_object_id
        self.application_id = application_id

    def create_alarm(self,
                     specific_problem: int,
                     perceived_severity: AlarmSeverity,
                     identifying_info: str,
                     additional_info: str = ""):
        """
        Convenience method that creates an alarm instance, an AlarmDetail object,
        using cached values for managed object ID and application ID.

        Parameters
        ----------
        specific_problem: int
            The problem that is the cause of the alarm

        perceived_severity: AlarmSeverity
            The severity of the alarm, a value from the enum.

        identifying_info: str
            Identifying additional information, which is part of alarm identity

        additional_info: str
            Additional information given by the application (optional)

        Returns
        -------
        AlarmDetail
        """
        return AlarmDetail(managed_object_id=self.managed_object_id,
                           application_id=self.application_id,
                           specific_problem=specific_problem, perceived_severity=perceived_severity,
                           identifying_info=identifying_info, additional_info=additional_info)

    @staticmethod
    def _create_alarm_message(alarm: AlarmDetail, action: AlarmAction):
        """
        Creates a dict with the specified alarm detail plus action and time.
        Uses the current system time in milliseconds since the Epoch.

        Parameters
        ----------
        detail: AlarmDetail
            The alarm details.

        action: AlarmAction
            The action to perform at the Alarm Adapter on this alarm.
        """
        return {
            **alarm,
            KEY_ALARM_ACTION: action.name,
            KEY_ALARM_TIME: int(round(time.time() * 1000))
        }

    def _rmr_send_alarm(self, msg: dict):
        """
        Serializes the dict and sends the result via RMR using a predefined message type.

        Parameters
        ----------
        msg: dict
            Dictionary with alarm message to encode and send

        Returns
        -------
        bool
            True if the send succeeded (possibly with retries), False otherwise
        """
        payload = json.dumps(msg).encode()
        mdc_logger.debug("_rmr_send_alarm: payload is {}".format(payload))
        sbuf = rmr.rmr_alloc_msg(vctx=self.vctx, size=len(payload), payload=payload,
                                 mtype=RIC_ALARM_UPDATE, gen_transaction_id=True)

        for _ in range(0, RETRIES):
            sbuf = rmr.rmr_send_msg(self.vctx, sbuf)
            post_send_summary = rmr.message_summary(sbuf)
            mdc_logger.debug("_rmr_send_alarm: try {0} result is {1}".format(_, post_send_summary[rmr.RMR_MS_MSG_STATE]))
            # stop trying if RMR does not indicate retry
            if post_send_summary[rmr.RMR_MS_MSG_STATE] != rmr.RMR_ERR_RETRY:
                break

        rmr.rmr_free_msg(sbuf)
        if post_send_summary[rmr.RMR_MS_MSG_STATE] != rmr.RMR_OK:
            mdc_logger.warning("_rmr_send_alarm: failed after {} retries".format(RETRIES))
            return False

        return True

    def raise_alarm(self, detail: AlarmDetail):
        """
        Builds and sends a message to the AlarmAdapter to raise an alarm
        with the specified detail.

        Parameters
        ----------
        detail: AlarmDetail
            Alarm to raise

        Returns
        -------
        bool
            True if the send succeeded (possibly with retries), False otherwise
        """
        msg = self._create_alarm_message(detail, AlarmAction.RAISE)
        return self._rmr_send_alarm(msg)

    def clear_alarm(self, detail: AlarmDetail):
        """
        Builds and sends a message to the AlarmAdapter to clear the alarm
        with the specified detail.

        Parameters
        ----------
        detail: AlarmDetail
            Alarm to clear

        Returns
        -------
        bool
            True if the send succeeded (possibly with retries), False otherwise
        """
        msg = self._create_alarm_message(detail, AlarmAction.CLEAR)
        return self._rmr_send_alarm(msg)

    def reraise_alarm(self, detail: AlarmDetail):
        """
        Builds and sends a message to the AlarmAdapter to clear the alarm with the
        the specified detail, then builds and sends a message to raise the alarm again.

        Parameters
        ----------
        detail: AlarmDetail
            Alarm to clear and raise again.

        Returns
        -------
        bool
            True if the send succeeded (possibly with retries), False otherwise
        """
        success = self.clear_alarm(detail)
        if success:
            success = self.raise_alarm(detail)
        return success

    def clear_all_alarms(self):
        """
        Builds and sends a message to the AlarmAdapter to clear all alarms.

        Returns
        -------
        bool
            True if the send succeeded (possibly with retries), False otherwise
        """
        detail = self.create_alarm(0, AlarmSeverity.DEFAULT, "", "")
        msg = self._create_alarm_message(detail, AlarmAction.CLEARALL)
        return self._rmr_send_alarm(msg)
