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
from sys import getsizeof
from typing import List, Tuple
from array import array
from ctypes import POINTER, Structure, ARRAY
from ctypes import c_ulong, c_void_p, c_long, c_size_t, c_ubyte, c_int, c_ssize_t, c_uint, c_uint8
from asn1.asn1clib.asn1clib import asn1_c_lib
from asn1.asn1clib.types import *

def _wrap_asn1_function(funcname, restype, argtypes):
    """
    Simplify wrapping ctypes functions.

    Parameters
    ----------
    funcname: str
        Name of library method
    restype: class
        Name of ctypes class; e.g., c_char_p
    argtypes: list
        List of ctypes classes; e.g., [ c_char_p, int ]

    Returns
    -------
    _FuncPointer:
        Pointer to C library function
    """
    func = asn1_c_lib.__getattr__(funcname)
    func.restype = restype
    func.argtypes = argtypes
    return func

_asn1_decode_indicationMsg = _wrap_asn1_function('e2ap_decode_ric_indication_message', POINTER(indication_msg_t), [c_void_p, c_ulong])
_asn1_free_indicationMsg = _wrap_asn1_function('e2ap_free_decoded_ric_indication_message', c_void_p, [POINTER(indication_msg_t)])
class IndicationMsg:
    """
    A class of E2AP's RICIndicationMessage
    """
    __slots__ = ('__request_id', '__request_sequence_number', '__function_id', '__action_id',
    '__indication_sequence_number', '__indication_type', '__indication_header', '__indication_message',
    '__call_process_id')
    __request_id: int
    __request_sequence_number: int
    __function_id: int
    __action_id: int
    __indication_sequence_number: int
    __indication_type: int
    __indication_header: bytes
    __indication_message: bytes
    __call_process_id: bytes

    def __init__(self):
        return

    @property
    def request_id(self):
        return self.__request_id

    @property
    def request_sequence_number(self):
        return self.__request_sequence_number

    @property
    def function_id(self):
        return self.__function_id

    @property
    def action_id(self):
        return self.__action_id

    @property
    def indication_sequence_number(self):
        return self.__indication_sequence_number

    @property
    def indication_type(self):
        return self.__indication_type

    @property
    def indication_header(self):
        return self.__indication_header

    @property
    def indication_message(self):
        return self.__indication_message

    @property
    def call_process_id(self):
        return self.__call_process_id

    def decode(self, payload: c_void_p):
        """
        Function that sets fields of IndicationMsg class
        through msg payload (bytes) of RICIndication type.

        Raise Exception when payload is not RICIndication.

        Parameters
        ----------
        payload: c_void_p
            RICIndication type payload received via rmr
        
        Returns
        -------
        """
        indication: indication_msg_t = _asn1_decode_indicationMsg(payload, getsizeof(payload))

        if indication is None:
            raise Exception("Payload is not matched with RICIndication")
        indication.contents.request_id = 1
        self.__request_id = indication.contents.request_id
        self.__request_sequence_number = indication.contents.request_sequence_number
        self.__function_id = indication.contents.function_id
        self.__action_id = indication.contents.action_id
        self.__indication_sequence_number = indication.contents.indication_sequence_number
        self.__indication_type = indication.contents.indication_type
        self.__indication_header = bytes(indication.contents.indication_header[:indication.contents.indication_header_length])
        self.__indication_message = bytes(indication.contents.indication_message[:indication.contents.indication_message_length])
        self.__call_process_id = bytes(indication.contents.call_process_id[:indication.contents.call_process_id_length])

        # _asn1_free_indicationMsg(indication)
        return

class CauseItem:
    __slots__ = ('__cause_type', '__cause_id')
    __cause_type: int
    __cause_id: int

    def __init__(self, causeType: int, causeID: int):
        self.__cause_type = causeType
        self.__cause_id = causeID
        return

    @property
    def cause_type(self):
        return self.__cause_type

    @property
    def cause_id(self):
        return self.__cause_id

class ActionAdmittedList:
    __slots__ = ('__request_id', '__count')
    __request_id: List[int]
    __count: int

    def __init__(self, request_id: List[int], count: int):
        self.__request_id = request_id
        self.__count = count
        return

    @property
    def request_id(self):
        return self.__request_id

    @property
    def count(self):
        return self.__count

class ActionNotAdmittedList:
    __slots__ = ('__request_id', '__cause', '__count')
    __request_id: List[int]
    __cause: List[CauseItem]
    __count: int

    def __init__(self, request_id: List[int], cause: List[CauseItem], count: int):
        self.__request_id = request_id
        self.__cause = cause
        self.__count = count
        return

    @property
    def request_id(self):
        return self.__request_id

    @property
    def cause(self):
        return self.__cause

    @property
    def count(self):
        return self.__count

_asn1_decode_subRespMsg = _wrap_asn1_function('e2ap_decode_ric_subscription_response_message', POINTER(subResp_msg_t), [c_void_p, c_ulong])
class SubResponseMsg:
    """
    A class of E2AP's RICsubscriptionResponseMessage
    """
    __slots__ = ('__request_id', '__request_sequence_number', '__function_id',
                 '__action_admitted_list', '__action_not_admitted_list')
    __request_id: int
    __request_sequence_number: int
    __function_id: int
    __action_admitted_list: ActionAdmittedList
    __action_not_admitted_list: ActionNotAdmittedList

    @property
    def request_id(self):
        return self.__request_id

    @property
    def request_sequence_number(self):
        return self.__request_sequence_number

    @property
    def function_id(self):
        return self.__function_id

    @property
    def action_admitted_list(self):
        return self.__action_admitted_list

    @property
    def action_not_admitted_list(self):
        return self.__action_not_admitted_list

    def __init__(self):
        return

    def decode(self, payload: c_void_p):
        """
        Function that sets fields of SubRespMsg class
        through msg payload (bytes) of RICsubscriptionResponseMessage type.

        Raise Exception when payload is not RICsubscriptionResponseMessage.

        Parameters
        ----------
        payload: c_void_p
            RICsubscriptionResponseMessage type payload received via rmr
        
        Returns
        -------
        """
        subResp: subResp_msg_t = _asn1_decode_subRespMsg(payload, getsizeof(payload))

        if subResp is None:
            raise Exception("Payload is not matched with RICsubscriptionResponseMessage")

        self.__request_id = subResp.contents.request_id
        self.__request_sequence_number = subResp.contents.request_sequence_number
        self.__function_id = subResp.contents.function_id
        self.__action_admitted_list = ActionAdmittedList(subResp.contents.action_admitted_list.request_id,
                                                         subResp.contents.action_admitted_list.count)
        causeList = [CauseItem(item.cause_type, item.cause_id) for item in subResp.contents.action_not_admitted_list.cause]
        self.__action_not_admitted_list = ActionNotAdmittedList(subResp.contents.action_not_admitted_list.request_id, causeList,
                                                                subResp.contents.action_not_admitted_list.count)
        return

class ActionDefinition:
    """
    A class that mirrored E2AP's RICactionDefinition with python
    """
    __slots__ = ('action_definition', 'size')

    action_definition: bytes
    size: int

    def __init__(self):
        self.action_definition = []
        self.size = 0
        return

class SubsequentAction:
    """
    A class that mirrored E2AP's RICSubsequentAction with python
    """
    __slots__ = ('is_valid', 'subsequent_action_type', 'time_to_wait')

    is_valid: int
    subsequent_action_type: int
    time_to_wait: int

    def __init__(self):
        self.is_valid = 0
        self.subsequent_action_type = 0
        self.time_to_wait = 0
        return    

_asn1_encode_subReqMsg = _wrap_asn1_function('e2ap_encode_ric_subscription_request_message', c_ssize_t, [c_void_p, c_size_t, c_long, c_long,
                                             c_long, c_void_p, c_size_t, c_size_t, POINTER(c_long), POINTER(c_long),
                                             POINTER(ric_action_definition_t), POINTER(ric_subsequent_action_t)])
class SubRequestMsg:
    """
    A class that provides a function to make payload of e2ap RICSubscriptionRequestMessage.
    """    
    def __init__(self):
        return

    def encode(self, requestor_id: int, request_sequence_number: int, 
               ran_function_id: int, event_trigger_definition: bytes, action_ids: List[int],
               action_types: List[int], action_definitions: List[ActionDefinition],
               sub_sequent_actions: List[SubsequentAction]) -> Tuple[int, bytes]:
        """
        Function that creates and returns a payload
        according to e2ap's RICSubscriptionRequestMessage.

        Raise Exception when the payload of RICSubscriptionRequestMessage cannot be created.

        Parameters
        ----------
        requestor_id: int
        request_sequence_number: int
        ran_function_id: int
        event_trigger_definition: bytes
        action_ids: List[int]
        action_types: List[int]
        action_definitions: List[ActionDefinition]
        sub_sequent_actions: List[SubsequentAction]

        Returns
        Tuple[int, bytes]
          int :
            RICSubscriptionRequestMessage type payload length
          bytes :
            RICSubscriptionRequestMessage type payload
        -------
        """
        action_count = len(action_ids)
        action_id_array = ARRAY(c_long, action_count)()
        for idx in range(action_count):
            action_id_array[idx] = c_long(action_ids[idx])

        action_type_count = len(action_types)
        action_type_array = ARRAY(c_long, action_type_count)()
        for idx in range(action_type_count):
            action_type_array[idx] = c_long(action_types[idx])

        event_definition_count = len(event_trigger_definition)
        event_trigger_definition_array = ARRAY(c_uint8, event_definition_count)()
        for idx in range(event_definition_count):
            event_trigger_definition_array[idx] = c_uint8(event_trigger_definition[idx])

        action_definition_count = len(action_definitions)
        acttion_definition_array = ARRAY(ric_action_definition_t, action_definition_count)()
        for idx in range(action_definition_count):
            action_definition_buffer = ARRAY(c_uint8, action_definitions[idx].size)()
            for buf_idx in range(action_definitions[idx].size):
                action_definition_buffer[buf_idx] = c_uint8(action_definitions[idx].action_definition[buf_idx])
            acttion_definition_array[idx].action_definition = action_definition_buffer
            acttion_definition_array[idx].size = c_int(action_definitions[idx].size)

        subsequent_action_count = len(sub_sequent_actions)        
        subsequent_action_array = ARRAY(ric_subsequent_action_t, subsequent_action_count)()
        for idx in range(subsequent_action_count):
            subsequent_action_array[idx].is_valid = sub_sequent_actions[idx].is_valid
            subsequent_action_array[idx].subsequent_action_type = sub_sequent_actions[idx].subsequent_action_type
            subsequent_action_array[idx].time_to_wait = sub_sequent_actions[idx].time_to_wait
        
        buf = ARRAY(c_uint8, 1024)()
        size: int = _asn1_encode_subReqMsg(buf, c_size_t(1024), c_long(requestor_id), c_long(request_sequence_number),
                                c_long(ran_function_id), event_trigger_definition_array, c_size_t(event_definition_count), c_size_t(action_count), action_id_array,
                                action_type_array, acttion_definition_array, subsequent_action_array)
        if size < 0 :
            raise Exception("Could not create payload.")

        return size, bytes(buf)

_asn1_encode_controlReqMsg = _wrap_asn1_function('e2ap_encode_ric_control_request_message', c_ssize_t, [c_void_p, c_size_t, c_long, c_long,
                                                 c_long, c_void_p, c_size_t, c_void_p, c_size_t, c_void_p, c_size_t, c_long])
class ControlRequestMsg:
    """
    A class that provides a function to make payload of e2ap RICControlRequestMessage.
    """
    def __init__(self):
        return

    def encode(self, requestor_id: int, request_sequence_number: int,
               ran_function_id: int, call_process_id: bytes,
               control_header: bytes, control_message: bytes,
               control_ack_request: int) -> Tuple[int, bytes]:
        """
        Function that creates and returns a payload
        according to e2ap's RICControlRequestMessage.

        Raise Exception when the payload of RICControlRequestMessage cannot be created.

        Parameters
        ----------
        requestor_id: int
        request_sequence_number: int
        ran_function_id: int
        call_process_id: bytes
        control_header: bytes
        control_message: bytes
        control_ack_request: int

        Returns
        Tuple[int, bytes]
          int :
            RICControlRequestMessage type payload length
          bytes :
            RICControlRequestMessage type payload
        -------
        """
        call_process_id_buffer = ARRAY(c_uint8, len(call_process_id))()
        for idx in range(len(call_process_id)):
            call_process_id_buffer[idx] = c_uint8(call_process_id[idx])

        call_header_buffer = ARRAY(c_uint8, len(control_header))()
        for idx in range(len(control_header)):
            call_header_buffer[idx] = c_uint8(control_header[idx])

        call_message_buffer = ARRAY(c_uint8, len(control_message))()
        for idx in range(len(control_message)):
            call_message_buffer[idx] = c_uint8(control_message[idx])

        buf = ARRAY(c_uint8, 1024)()
        size: int = _asn1_encode_controlReqMsg(buf, c_size_t(1024), c_long(requestor_id), c_long(request_sequence_number),
                                c_long(ran_function_id), call_process_id_buffer, c_size_t(len(call_process_id_buffer)), call_header_buffer, c_size_t(len(call_header_buffer)),
                                call_message_buffer, c_size_t(len(call_message_buffer)), c_long(control_ack_request))
        if size < 0 :
            raise Exception("Could not create payload.")

        return size, bytes(buf)
