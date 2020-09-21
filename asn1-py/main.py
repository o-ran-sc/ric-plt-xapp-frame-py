import os, sys
from asn1.asn1 import IndicationMsg, SubResponseMsg, SubRequestMsg, ActionDefinition, SubsequentAction, ControlRequestMsg

def decode_indication_message() -> None :
    try:
        indication_payload: bytes = b'\x00\x05\x40\x62\x00\x00\x08\x00\x1d\x00\x05\x00\x00\x7b\x00\x01\x00\x05\x00\x02\x00\x00\x00\x0f\x00\x01\x50\x00\x1b\x00\x02\x00\x2d\x00\x1c\x00\x01\x00\x00\x19\x00\x0d\x0c\x72\x65\x70\x6f\x72\x74\x68\x65\x61\x64\x65\x72\x00\x1a\x00\x22\x21\x40\x00\x00\x52\x07\x47\x4e\x42\x43\x55\x55\x50\x35\x08\x08\x37\x34\x37\x00\x00\x00\x4d\x00\x53\x44\x31\x01\x80\x09\x00\x40\x00\x50\x00\x14\x00\x05\x04\x63\x70\x69\x64'
        indication = IndicationMsg()
        indication.decode(indication_payload)

        print("===========RICINDICATION===========")
        print("request_id : " ,indication.request_id)
        print("request_sequence_number : " ,indication.request_sequence_number)
        print("function_id : " ,indication.function_id)
        print("action_id : " ,indication.action_id)
        print("indication_type : " ,indication.indication_type)
        print("indication_header : ", indication.indication_header)
        print("indication_message : ", indication.indication_message)
        print("indication_sequence_number : ", indication.indication_sequence_number)
        print("call_process_id : ", indication.call_process_id)
        print("===================================")
    except BaseException as e:
        print("BaseException: ", e)

def decode_subscription_response_message() -> None :
    try:
        sub_response_payload: bytes = b'\x20\x08\x00\x1d\x00\x00\x03\x00\x1d\x00\x05\x00\x00\x7b\x00\x02\x00\x05\x00\x02\x00\x00\x00\x11\x00\x07\x00\x00\x0e\x00\x02\x00\x05'
        sub_response = SubResponseMsg()
        sub_response.decode(sub_response_payload)
        print("============SUBRESPONSE============")
        print("request_id : " , sub_response.request_id)
        print("request_sequence_number : " , sub_response.request_sequence_number)
        print("function_id : " , sub_response.function_id)
        print("action_admitted_list.count : " , sub_response.action_admitted_list.count)
        for idx in range(sub_response.action_admitted_list.count):
            print("\taction_admitted_list.request_id : " , sub_response.action_admitted_list.request_id[idx])
        print("action_not_admitted_list.count : " , sub_response.action_not_admitted_list.count)
        for idx in range(sub_response.action_not_admitted_list.count):
            print("\taction_not_admitted_list.request_id : " , sub_response.action_not_admitted_list.request_id[idx])
            print("\t\taction_not_admitted_list.cause_id : " , sub_response.action_not_admitted_list.cause[idx].cause_id)
            print("\t\taction_not_admitted_list.cause_type : " , sub_response.action_not_admitted_list.cause[idx].cause_type)
        print("====================================")
    except BaseException as e:
        print("BaseException: ", e)

def encode_subscription_request_message() -> None :
    try:
        action_definitions = list()

        action_definition = ActionDefinition()
        action_definition.action_definition = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07])
        action_definition.size = len(action_definition.action_definition)

        action_definition2 = ActionDefinition()
        action_definition2.action_definition = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
        action_definition2.size = len(action_definition2.action_definition)

        action_definitions.append(action_definition)
        action_definitions.append(action_definition2)

        subsequent_actions = list()

        subsequent_action = SubsequentAction()
        subsequent_action.is_valid = 1
        subsequent_action.subsequent_action_type =1
        subsequent_action.time_to_wait = 1

        subsequent_action2 = SubsequentAction()
        subsequent_action.is_valid = 1
        subsequent_action2.subsequent_action_type = 2
        subsequent_action2.time_to_wait = 2

        subsequent_actions.append(subsequent_action)
        subsequent_actions.append(subsequent_action2)

        payload = bytes(1024)
        eventTriggerDefinition = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
        actIDs = list()
        actIDs.append(1)
        actIDs.append(2)

        actTypes = list()
        actTypes.append(1)
        actTypes.append(2)

        sub_request = SubRequestMsg()
        returnValue = sub_request.encode(0, 0, 0, eventTriggerDefinition, actIDs, actTypes, action_definitions, subsequent_actions)
        print("===========RICSUBREQUEST===========")
        print("size: ",  returnValue[0])
        print("payload: ", returnValue[1][0:returnValue[0]])
        print("===================================")

    except BaseException as e:
        print("BaseException: ", e)

def encode_control_request_message() -> None :
    try:
        controlReq = ControlRequestMsg()
        callProcessIDBuffer = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
        controlHeaderBuffer = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
        controlMessageBuffer = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
        returnValue = controlReq.encode(0, 0, 0, callProcessIDBuffer, controlHeaderBuffer, controlMessageBuffer, -1)
        print("===========RICCONREQUEST===========")
        print("size: ",  returnValue[0])
        print("payload: ", returnValue[1][0:returnValue[0]])
        print("===================================")

    except BaseException as e:
        print("BaseException: ", e)

def process(message_type) -> None:
    if message_type is 'i':
        decode_indication_message()
    elif message_type is 'p':
        decode_subscription_response_message()
    elif message_type is 'q':
        encode_subscription_request_message()
    elif message_type is 'c':
        encode_control_request_message()

def print_option() -> None :
    print("===================================================")
    print("Option description for example")
    print("python main.py [option]")
    print(" option : ")
    print("   'i' : decode sample indication message")
    print("   'p' : decode sample subscription response message")
    print("   'q' : encode sample subscription request message")
    print("   'c' : encode sample control request message")
    print("===================================================")

if __name__ == '__main__' :
    if len(sys.argv) is 1 :
        print_option()
        exit()

    process(sys.argv[1])
