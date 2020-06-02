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
    managedObjectId: str
        The name of the managed object that is the cause of the fault

    applicationId: str
        The name of the process that raised the alarm

    specificProblem: int
        The problem that is the cause of the alarm

    perceivedSeverity: AlarmSeverity
        The severity of the alarm, a value from the enum.

    additionalInfo: str
        Additional information given by the application

    identifyingInfo: str
        Identifying additional information, which is part of alarm identity
    """
    def __init__(self,
                 managedObjectId: str,
                 applicationId: str,
                 specificProblem: int,
                 perceivedSeverity: AlarmSeverity,
                 additionalInfo: str,
                 identifyingInfo: str):
        """
        Creates an object with the specified details.
        """
        dict.__init__(self, managedObjectId=managedObjectId, applicationId=applicationId,
                      specificProblem=specificProblem, perceivedSeverity=perceivedSeverity.name,
                      additionalInfo=additionalInfo, identifyingInfo=identifyingInfo)


class AlarmManager:
    """
    Provides the API for an Xapp to raise and clear alarms to the Alarm Adapter.

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context obtained by initializing RMR.
        The context is used to allocate space and send messages.
        The RMR routing table must have a destination for message
        type RIC_ALARM_UPDATE as defined in this module.

    managedObjectId: str
        The name of the managed object that raises alarms

    applicationId: str
        The name of the process that raises alarms
    """
    def __init__(self,
                 vctx: c_void_p,
                 managedObjectId: str,
                 applicationId: str):
        """
        Creates an alarm manager.
        """
        self.vctx = vctx
        self.managedObjectId = managedObjectId
        self.applicationId = applicationId

    def setManagedObjectId(self, managedObjectId: str):
        """
        Parameters
        ----------
        managedObjectId: str
            The name of the managed object that raises alarms
        """
        self.managedObjectId = managedObjectId

    def setApplicationId(self, applicationId: str):
        """
        Parameters
        ----------
        applicationId: str
            The name of the process that raises alarms
        """
        self.applicationId = applicationId

    def create_alarm(self,
                     specificProblem: int,
                     perceivedSeverity: AlarmSeverity,
                     additionalInfo: str,
                     identifyingInfo: str):
        """
        Convenience method that creates an alarm instance, an AlarmDetail object,
        using cached values for managed object ID and application ID.

        Parameters
        ----------
        specificProblem: int
            The problem that is the cause of the alarm

        perceivedSeverity: AlarmSeverity
            The severity of the alarm, a value from the enum.

        additionalInfo: str
            Additional information given by the application

        identifyingInfo: str
            Identifying additional information, which is part of alarm identity

        Returns
        -------
        AlarmDetail
        """
        return AlarmDetail(self.managedObjectId, self.applicationId,
                           specificProblem, perceivedSeverity, additionalInfo, identifyingInfo)

    def _create_alarm_message(self, alarm: AlarmDetail, action: AlarmAction):
        """
        Creates a dict with the specified alarm detail and action string.
        Uses the current system time, measured in milliseconds since the Epoch.

        Parameters
        ----------
        detail: AlarmDetail
            The alarm details.

        action: AlarmAction
            The action to perform at the Alarm Adapter on this alarm.
        """
        msg = {}
        msg['alarm'] = alarm
        msg['action'] = action.name
        msg['alarmTime'] = int(round(time.time() * 1000))
        return msg

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
        sbuf = rmr.rmr_alloc_msg(vctx=self.vctx, size=len(payload), payload=payload, mtype=RIC_ALARM_UPDATE, gen_transaction_id=True)

        for _ in range(0, RETRIES):
            mdc_logger.debug("_rmr_send_alarm: sending: {}".format(payload))
            sbuf = rmr.rmr_send_msg(self.vctx, sbuf)
            post_send_summary = rmr.message_summary(sbuf)
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
        mdc_logger.debug("raise_alarm: message is {}".format(msg))
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
        mdc_logger.debug("clear_alarm: message is {}".format(msg))
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
        mdc_logger.debug("clear_all_alarms: message is {}".format(msg))
        return self._rmr_send_alarm(msg)
