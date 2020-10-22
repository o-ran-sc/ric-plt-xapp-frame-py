# *******************************************************************************
#  * Copyright 2020 Samsung Electronics All Rights Reserved.
#  *
#  * Licensed under the Apache License, Version 2.0 (the "License");
#  * you may not use this file except in compliance with the License.
#  * You may obtain a copy of the License at
#  *
#  * http://www.apache.org/licenses/LICENSE-2.0
#  *
#  * Unless required by applicable law or agreed to in writing, software
#  * distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.
#  *
#  *******************************************************************************
from ctypes import POINTER, Structure
from ctypes import c_long, c_size_t, c_int, c_uint8

class indication_msg_t(Structure):
    """
    A class that mirrored E2AP's RICIndicationMessage with python

    c-type struct of RICIndicationMessage
    ---------------------------------------
    typedef struct RICindicationMessage {
        long requestorID;
        long requestSequenceNumber;
        long ranfunctionID;
        long actionID;
        long indicationSN;
        long indicationType;
        uint8_t *indicationHeader;
        size_t indicationHeaderSize;
        uint8_t *indicationMessage;
        size_t indicationMessageSize;
        uint8_t *callProcessID;
        size_t callProcessIDSize;
    } RICindicationMsg;
    ---------------------------------------
    """
    _fields_ = [
        ("request_id", c_long),
        ("request_sequence_number", c_long),
        ("function_id", c_long),
        ("action_id", c_long),
        ("indication_sequence_number", c_long),
        ("indication_type", c_long),
        ("indication_header", POINTER(c_uint8)),
        ("indication_header_length", c_size_t),
        ("indication_message", POINTER(c_uint8)),
        ("indication_message_length", c_size_t),
        ("call_process_id", POINTER(c_uint8)),
        ("call_process_id_length", c_size_t),
    ]


class causeItem_msg_t(Structure):
    """
    A class that mirrored E2AP's RICcauseItem with python

    c-type struct of RICcauseItem
    -----------------------------
    typedef struct RICcauseItem {
        int ricCauseType;
        long ricCauseID;
    } RICcauseItem;
    -----------------------------
    """
    _fields_ = [
        ("cause_type", c_int),
        ("cause_id", c_long),
    ]


class actionAdmittedList_msg_t(Structure):
    """
    A class that mirrored E2AP's RICactionAdmittedList with python

    c-type struct of RICactionAdmittedList
    --------------------------------------
    typedef struct RICactionAdmittedList {
        long ricActionID[16];
        int count;
    } RICactionAdmittedList;
    --------------------------------------
    """
    _fields_ = [
        ("request_id", c_long * 16),
        ("count", c_int),
    ]


class actionNotAdmittedList_msg_t(Structure):
    """
    A class that mirrored E2AP's RICactionNotAdmittedList with python

    c-type struct of RICactionNotAdmittedList
    -------------------------------------------------------
    typedef struct RICactionNotAdmittedList {
        long ricActionID[16];
        RICcauseItem ricCause[16];
        int count;
    } RICactionNotAdmittedList;
    -------------------------------------------------------
    """
    _fields_ = [
        ("request_id", c_long * 16),
        ("cause", causeItem_msg_t * 16),
        ("count", c_int),
    ]


class subResp_msg_t(Structure):
    """
    A class that mirrored E2AP's subscriptionResponseMessage with python

    c-type struct of subscriptionResponseMessage
    -------------------------------------------------------
    typedef struct RICsubscriptionResponseMessage {
        long requestorID;
        long requestSequenceNumber;
        long ranfunctionID;
        RICactionAdmittedList ricActionAdmittedList;
        RICactionNotAdmittedList ricActionNotAdmittedList;
    } RICsubscriptionResponseMsg;
    -------------------------------------------------------
    """
    _fields_ = [
        ("request_id", c_long),
        ("request_sequence_number", c_long),
        ("function_id", c_long),
        ("action_admitted_list", actionAdmittedList_msg_t),
        ("action_not_admitted_list", actionNotAdmittedList_msg_t),
    ]


class ric_action_definition_t(Structure):
    """
    A class that mirrored E2AP's RICactionDefinition with python

    c-type struct of RICactionDefinition
    -------------------------------------------------------
    typedef struct RICactionDefinition {
        uint8_t *actionDefinition;
        int size;
    } RICactionDefinition;
    -------------------------------------------------------
    """
    _fields_ = [
        ("action_definition", POINTER(c_uint8)),
        ("size", c_int),
    ]


class ric_subsequent_action_t(Structure):
    """
    A class that mirrored E2AP's RICSubsequentAction with python

    c-type struct of RICSubsequentAction
    -------------------------------------------------------
    typedef struct RICSubsequentAction {
        int isValid;
        long subsequentActionType;
        long timeToWait;
    } RICSubsequentAction;
    -------------------------------------------------------
    """
    _fields_ = [
        ("is_valid", c_int),
        ("subsequent_action_type", c_long),
        ("time_to_wait", c_long),
    ]
