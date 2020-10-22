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
from ricxappframe.e2ap.asn1 import IndicationMsg, SubResponseMsg, SubRequestMsg, ControlRequestMsg, ActionDefinition, SubsequentAction, ARRAY, c_uint8

"""
fake class for c-type Structure
"""


class indication_msg_type:
    def __init__(self):
        self.contents = _indication_contents()


class _indication_contents:
    def __init__(self):
        self.request_id = 0
        self.request_sequence_number = 0
        self.function_id = 0
        self.action_id = 0
        self.indication_sequence_number = 0
        self.indication_type = 0
        self.indication_header = ARRAY(c_uint8, 1)()
        self.indication_header_length = 1
        self.indication_message = ARRAY(c_uint8, 1)()
        self.indication_message_length = 1
        self.call_process_id = ARRAY(c_uint8, 1)()
        self.call_process_id_length = 1


class actionAdmittedList_msg_type:
    def __init__(self):
        self.request_id = []
        self.count = 0


class causeItem_msg_type:
    def __init__(self):
        self.cause_type = 0
        self.cause_id = 0


class actionNotAdmittedList_msg_type:
    def __init__(self):
        self.request_id = []
        self.cause = []
        self.count = 0


class subResp_msg_type:
    def __init__(self):
        self.contents = _subResp_contents()


class _subResp_contents:

    def __init__(self):
        self.request_id = 0
        self.request_sequence_number = 0
        self.function_id = 0
        self.action_admitted_list = actionAdmittedList_msg_type()
        self.action_not_admitted_list = actionNotAdmittedList_msg_type()


def test_call_decode_indication_and_clib_return_none_expect_error_raise(monkeypatch):
    '''
    test the decode of IndicationMsg class with invalid payload from rmr
    '''
    def mock_decode_return_none(payload: bytes, size):
        return None

    monkeypatch.setattr("ricxappframe.e2ap.asn1._asn1_decode_indicationMsg",
                        mock_decode_return_none)

    indication = IndicationMsg()

    try:
        indication.decode(bytes(0))
        assert False
    except BaseException:
        assert True


def test_call_decode_indication_expect_success(monkeypatch):
    '''
    test the decode of IndicationMsg class
    '''
    def mock_decode_return_valid_indication(payload: bytes, size: int):
        indication_msg = indication_msg_type()
        indication_msg.contents.request_id = 1
        indication_msg.contents.request_sequence_number = 1
        indication_msg.contents.function_id = 1
        indication_msg.contents.action_id = 1
        indication_msg.contents.indication_sequence_number = 1
        indication_msg.contents.indication_type = 1

        indication_header = ARRAY(c_uint8, 1)()
        indication_message = ARRAY(c_uint8, 1)()
        call_process_id = ARRAY(c_uint8, 1)()

        indication_msg.contents.indication_header = indication_header
        indication_msg.contents.indication_message = indication_message
        indication_msg.contents.call_process_id = call_process_id
        return indication_msg

    monkeypatch.setattr("ricxappframe.e2ap.asn1._asn1_decode_indicationMsg",
                        mock_decode_return_valid_indication)

    indication = IndicationMsg()
    try:
        indication.decode(bytes(0))
        assert indication.request_id == 1
        assert indication.request_sequence_number == 1
        assert indication.indication_type == 1
        assert indication.function_id == 1
        assert indication.action_id == 1
        assert indication.indication_sequence_number == 1
        assert indication.indication_header == bytes(b'\x00')
        assert indication.indication_message == bytes(b'\x00')
        assert indication.call_process_id == bytes(b'\x00')
    except BaseException:
        assert False


def test_call_decode_sub_response_and_clib_return_none_expect_error_raise(monkeypatch):
    '''
    test the decode of SubResponseMsg class with invalid payload from rmr
    '''
    def mock_decode_return_none(payload: bytes, size):
        return None

    monkeypatch.setattr("ricxappframe.e2ap.asn1._asn1_decode_subRespMsg",
                        mock_decode_return_none)

    sub_response = SubResponseMsg()
    try:
        sub_response.decode(bytes(0))
        assert False
    except BaseException:
        assert True


def test_call_decode_sub_response_expect_success(monkeypatch):
    '''
    test the decode of SubResponseMsg class
    '''
    def mock_decode_return_valid_sub_response(payload: bytes, size: int):
        subResp_msg = subResp_msg_type()
        subResp_msg.contents.request_id = 1
        subResp_msg.contents.request_sequence_number = 1
        subResp_msg.contents.function_id = 1

        action_admitted_list_msg = actionAdmittedList_msg_type()
        action_admitted_list_msg.request_id = [1]
        action_admitted_list_msg.count = 1

        casue_item_msg = causeItem_msg_type()
        casue_item_msg.cause_id = 1
        casue_item_msg.cause_type = 1

        action_not_admitted_list_msg = actionNotAdmittedList_msg_type()
        action_not_admitted_list_msg.request_id = [1]
        action_not_admitted_list_msg.count = 1
        action_not_admitted_list_msg.cause = [casue_item_msg]

        subResp_msg.contents.action_admitted_list = action_admitted_list_msg
        subResp_msg.contents.action_not_admitted_list = action_not_admitted_list_msg

        return subResp_msg

    monkeypatch.setattr("ricxappframe.e2ap.asn1._asn1_decode_subRespMsg",
                        mock_decode_return_valid_sub_response)

    sub_response = SubResponseMsg()
    try:
        sub_response.decode(bytes(0))
        assert sub_response.request_id == 1
        assert sub_response.request_sequence_number == 1
        assert sub_response.function_id == 1
        assert sub_response.action_admitted_list.request_id[0] == 1
        assert sub_response.action_admitted_list.count == 1
        assert sub_response.action_not_admitted_list.request_id[0] == 1
        assert sub_response.action_not_admitted_list.count == 1
        assert sub_response.action_not_admitted_list.cause[0].cause_id == 1
        assert sub_response.action_not_admitted_list.cause[0].cause_type == 1
    except BaseException:
        assert False


def test_call_encode_sub_request_and_clib_return_error_expect_error_raise(monkeypatch):
    '''
    test the encode of SubRequestMsg class with invalid param
    '''
    def mock_encode_return_error(buf, buf_size, requestor_id, request_sequence_number,
                                 ran_function_id, event_trigger_definition_array, event_definition_count,
                                 action_count, action_id_array, action_type_array, acttion_definition_array,
                                 subsequent_action_array):
        return -1

    monkeypatch.setattr("ricxappframe.e2ap.asn1._asn1_encode_subReqMsg",
                        mock_encode_return_error)

    sub_request = SubRequestMsg()
    try:
        sub_request.encode(1, 1, 1, bytes([1]), [1], [1], [], [])
        assert False
    except BaseException:
        assert True


def test_call_encode_sub_request_expect_success(monkeypatch):
    '''
    test the encode of SubRequestMsg class
    '''
    def mock_encode_return_success(buf, buf_size, requestor_id, request_sequence_number,
                                   ran_function_id, event_trigger_definition_array, event_definition_count,
                                   action_count, action_id_array, action_type_array, acttion_definition_array,
                                   subsequent_action_array):
        assert buf_size.value == 1024
        assert requestor_id.value == 1
        assert request_sequence_number.value == 1
        assert ran_function_id.value == 1
        assert event_trigger_definition_array[0] == 1
        assert event_definition_count.value == 1
        assert action_count.value == 1
        assert action_type_array[0] == 1
        assert acttion_definition_array[0].action_definition[0] == 1
        assert acttion_definition_array[0].size == 1
        assert subsequent_action_array[0].is_valid == 1
        assert subsequent_action_array[0].subsequent_action_type == 1
        assert subsequent_action_array[0].time_to_wait == 1
        return 1

    monkeypatch.setattr("ricxappframe.e2ap.asn1._asn1_encode_subReqMsg",
                        mock_encode_return_success)

    action_definitions = list()

    action_definition = ActionDefinition()
    action_definition.action_definition = bytes([1])
    action_definition.size = len(action_definition.action_definition)

    action_definitions.append(action_definition)

    subsequent_actions = list()

    subsequent_action = SubsequentAction()
    subsequent_action.is_valid = 1
    subsequent_action.subsequent_action_type = 1
    subsequent_action.time_to_wait = 1

    subsequent_actions.append(subsequent_action)
    sub_request = SubRequestMsg()
    try:
        sub_request.encode(1, 1, 1, bytes([1]), [1], [1],
                           action_definitions, subsequent_actions)
    except BaseException:
        assert False


def test_call_encode_control_request_and_clib_return_error_expect_error_raise(monkeypatch):
    '''
    test the encode of ControlRequestMsg class with invalid param
    '''
    def mock_encode_return_error(buf, buf_size, requestor_id, request_sequence_number,
                                 ran_function_id, event_trigger_definition_array, event_definition_count,
                                 action_count, action_id_array, action_type_array, acttion_definition_array,
                                 subsequent_action_array):
        return -1

    monkeypatch.setattr("ricxappframe.e2ap.asn1._asn1_encode_controlReqMsg",
                        mock_encode_return_error)

    control_request = ControlRequestMsg()
    try:
        control_request.encode(1, 1, 1, bytes([1]), bytes([1]), bytes([1]), 1)
        assert False
    except BaseException:
        assert True


def test_call_encode_control_request_expect_success(monkeypatch):
    '''
    test the encode of ControlRequestMsg class
    '''
    def mock_encode_return_success(buf, buf_size, requestor_id, request_sequence_number,
                                   ran_function_id, call_process_id_buffer, call_process_id_buffer_count,
                                   call_header_buffer, call_header_buffer_count, call_message_buffer, call_message_buffer_count,
                                   control_ack_request):
        assert buf_size.value == 1024
        assert requestor_id.value == 1
        assert request_sequence_number.value == 1
        assert ran_function_id.value == 1
        assert call_process_id_buffer[0] == 1
        assert call_process_id_buffer_count.value == 1
        assert call_header_buffer[0] == 1
        assert call_header_buffer_count.value == 1
        assert call_message_buffer[0] == 1
        assert call_message_buffer_count.value == 1
        assert control_ack_request.value == 1
        return 1

    monkeypatch.setattr("ricxappframe.e2ap.asn1._asn1_encode_controlReqMsg",
                        mock_encode_return_success)

    action_definitions = list()

    action_definition = ActionDefinition()
    action_definition.action_definition = bytes([1])
    action_definition.size = len(action_definition.action_definition)

    action_definitions.append(action_definition)

    subsequent_actions = list()

    subsequent_action = SubsequentAction()
    subsequent_action.is_valid = 1
    subsequent_action.subsequent_action_type = 1
    subsequent_action.time_to_wait = 1

    subsequent_actions.append(subsequent_action)
    control_request = ControlRequestMsg()
    try:
        control_request.encode(1, 1, 1, bytes([1]), bytes([1]), bytes([1]), 1)
    except BaseException:
        assert False
