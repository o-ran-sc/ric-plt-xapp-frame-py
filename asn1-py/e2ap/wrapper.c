#include <errno.h>
#include "wrapper.h"

size_t encode_E2AP_PDU(E2AP_PDU_t *pdu, void *buffer, size_t buf_size)
{
    asn_enc_rval_t encode_result;
    encode_result = aper_encode_to_buffer(&asn_DEF_E2AP_PDU, NULL, pdu, buffer, buf_size);
    ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, pdu);
    if (encode_result.encoded == -1)
    {
        fprintf(stderr, "Cannot encode %s: %s\n", encode_result.failed_type->name, strerror(errno));
        return -1;
    }
    else
    {
        return encode_result.encoded;
    }
}

E2AP_PDU_t *decode_E2AP_PDU(const void *buffer, size_t buf_size)
{
    asn_dec_rval_t decode_result;
    E2AP_PDU_t *pdu = 0;
    decode_result = aper_decode_complete(NULL, &asn_DEF_E2AP_PDU, (void **)&pdu, buffer, buf_size);
    if (decode_result.code == RC_OK)
    {
        return pdu;
    }
    else
    {
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, pdu);
        return 0;
    }
}

/* RICsubscriptionRequest */
ssize_t e2ap_encode_ric_subscription_request_message(void *buffer, size_t buf_size, long ricRequestorID, long ricRequestSequenceNumber, long ranFunctionID, void *eventTriggerDefinition, size_t eventTriggerDefinitionSize, int actionCount, long *actionIds, long *actionTypes, RICactionDefinition *actionDefinitions, RICSubsequentAction *subsequentActionTypes)
{
    E2AP_PDU_t *init = (E2AP_PDU_t *)calloc(1, sizeof(E2AP_PDU_t));
    if (!init)
    {
        fprintf(stderr, "alloc E2AP_PDU failed\n");
        return -1;
    }

    InitiatingMessage_t *initiatingMsg = (InitiatingMessage_t *)calloc(1, sizeof(InitiatingMessage_t));
    if (!initiatingMsg)
    {
        fprintf(stderr, "alloc InitiatingMessage failed\n");
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
        return -1;
    }

    init->choice.initiatingMessage = initiatingMsg;
    init->present = E2AP_PDU_PR_initiatingMessage;

    initiatingMsg->procedureCode = ProcedureCode_id_RICsubscription;
    initiatingMsg->criticality = Criticality_reject;
    initiatingMsg->value.present = InitiatingMessage__value_PR_RICsubscriptionRequest;

    RICsubscriptionRequest_t *subscription_request = &initiatingMsg->value.choice.RICsubscriptionRequest;

    // request contains 5 IEs

    // RICrequestID
    RICsubscriptionRequest_IEs_t *ies_reqID = (RICsubscriptionRequest_IEs_t *)calloc(1, sizeof(RICsubscriptionRequest_IEs_t));
    if (!ies_reqID)
    {
        fprintf(stderr, "alloc RICrequestID failed\n");
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
        return -1;
    }

    ies_reqID->criticality = Criticality_reject;
    ies_reqID->id = ProtocolIE_ID_id_RICrequestID;
    ies_reqID->value.present = RICsubscriptionRequest_IEs__value_PR_RICrequestID;
    RICrequestID_t *ricrequest_ie = &ies_reqID->value.choice.RICrequestID;
    ricrequest_ie->ricRequestorID = ricRequestorID;
    ricrequest_ie->ricInstanceID = ricRequestSequenceNumber;
    ASN_SEQUENCE_ADD(&subscription_request->protocolIEs.list, ies_reqID);

    // RICfunctionID
    RICsubscriptionRequest_IEs_t *ies_ranfunc = (RICsubscriptionRequest_IEs_t *)calloc(1, sizeof(RICsubscriptionRequest_IEs_t));
    if (!ies_ranfunc)
    {
        fprintf(stderr, "alloc RICfunctionID failed\n");
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
        return -1;
    }

    ies_ranfunc->criticality = Criticality_reject;
    ies_ranfunc->id = ProtocolIE_ID_id_RANfunctionID;
    ies_ranfunc->value.present = RICsubscriptionRequest_IEs__value_PR_RANfunctionID;
    RANfunctionID_t *ranfunction_ie = &ies_ranfunc->value.choice.RANfunctionID;
    *ranfunction_ie = ranFunctionID;
    ASN_SEQUENCE_ADD(&subscription_request->protocolIEs.list, ies_ranfunc);

    // RICsubscription
    RICsubscriptionRequest_IEs_t *ies_subscription = (RICsubscriptionRequest_IEs_t *)calloc(1, sizeof(RICsubscriptionRequest_IEs_t));
    if (!ies_subscription)
    {
        fprintf(stderr, "alloc RICsubscription failed\n");
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
        return -1;
    }

    ies_subscription->criticality = Criticality_reject;
    ies_subscription->id = ProtocolIE_ID_id_RICsubscriptionDetails;
    ies_subscription->value.present = RICsubscriptionRequest_IEs__value_PR_RICsubscriptionDetails;
    RICsubscriptionDetails_t *ricsubscription_ie = &ies_subscription->value.choice.RICsubscriptionDetails;

    // RICeventTriggerDefinition
    RICeventTriggerDefinition_t *eventTrigger = &ricsubscription_ie->ricEventTriggerDefinition;
    eventTrigger->buf = (uint8_t *)calloc(1, eventTriggerDefinitionSize);
    if (!eventTrigger->buf)
    {
        fprintf(stderr, "alloc eventTrigger failed\n");
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
        return -1;
    }
    memcpy(eventTrigger->buf, eventTriggerDefinition, eventTriggerDefinitionSize);
    eventTrigger->size = eventTriggerDefinitionSize;

    // RICactions-ToBeSetup-List
    RICactions_ToBeSetup_List_t *ricActions = &ricsubscription_ie->ricAction_ToBeSetup_List;
    int index = 0;
    while (index < actionCount)
    {
        RICaction_ToBeSetup_ItemIEs_t *ies_action = (RICaction_ToBeSetup_ItemIEs_t *)calloc(1, sizeof(RICaction_ToBeSetup_ItemIEs_t));
        if (!ies_action)
        {
            fprintf(stderr, "alloc RICaction failed\n");
            ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
            return -1;
        }

        ies_action->criticality = Criticality_reject;
        ies_action->id = ProtocolIE_ID_id_RICaction_ToBeSetup_Item;
        ies_action->value.present = RICaction_ToBeSetup_ItemIEs__value_PR_RICaction_ToBeSetup_Item;
        RICaction_ToBeSetup_Item_t *ricaction_ie = &ies_action->value.choice.RICaction_ToBeSetup_Item;
        ricaction_ie->ricActionID = actionIds[index];
        ricaction_ie->ricActionType = actionTypes[index];
        int actionDefinitionSize = actionDefinitions[index].size;

        if(actionDefinitionSize != 0) {
            ricaction_ie->ricActionDefinition = (RICactionDefinition_t* )calloc(1, sizeof(RICactionDefinition_t));
            RICactionDefinition_t *actionDefinition = ricaction_ie->ricActionDefinition;
            actionDefinition->buf = (uint8_t *)calloc(1, sizeof(uint8_t) * actionDefinitionSize);
            if (!actionDefinition->buf)
            {
                fprintf(stderr, "alloc actionDefinition[%d] failed\n", index);
                ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
                return -1;
            }
            memcpy(actionDefinition->buf, actionDefinitions[index].actionDefinition, actionDefinitionSize);
            actionDefinition->size = actionDefinitionSize;
        }

        if(subsequentActionTypes[index].isValid != 0) {
            ricaction_ie->ricSubsequentAction = (RICsubsequentAction_t *)calloc(1, sizeof(RICsubsequentAction_t));
            RICsubsequentAction_t *subsequentAction = ricaction_ie->ricSubsequentAction;
            subsequentAction->ricSubsequentActionType = subsequentActionTypes[index].subsequentActionType;
            subsequentAction->ricTimeToWait = subsequentActionTypes[index].timeToWait;
        }

        int result = ASN_SEQUENCE_ADD(&ricActions->list, ies_action);
        if(result != 0){
            fprintf(stderr, "ASN_SEQUENCE_ADD result : %d\n", result);
        }
        index++;
    }
    int result = ASN_SEQUENCE_ADD(&subscription_request->protocolIEs.list, ies_subscription);
    if(result != 0){
            fprintf(stderr, "ASN_SEQUENCE_ADD result : %d\n", result);
    }
    return encode_E2AP_PDU(init, buffer, buf_size);
}

/* RICsubscriptionResponse */
RICsubscriptionResponseMsg *e2ap_decode_ric_subscription_response_message(void *buffer, size_t buf_size)
{
    E2AP_PDU_t *pdu = decode_E2AP_PDU(buffer, buf_size);
    if (pdu != NULL && pdu->present == E2AP_PDU_PR_successfulOutcome)
    {
        SuccessfulOutcome_t *successfulOutcome = pdu->choice.successfulOutcome;
        if (successfulOutcome->procedureCode == ProcedureCode_id_RICsubscription && successfulOutcome->value.present == SuccessfulOutcome__value_PR_RICsubscriptionResponse)
        {
            RICsubscriptionResponse_t *subscriptionResponse = &(successfulOutcome->value.choice.RICsubscriptionResponse);
            RICsubscriptionResponseMsg *msg = (RICsubscriptionResponseMsg *)calloc(1, sizeof(RICsubscriptionResponseMsg));
            for (int i = 0; i < subscriptionResponse->protocolIEs.list.count; ++i)
            {
                if (subscriptionResponse->protocolIEs.list.array[i]->id == ProtocolIE_ID_id_RICrequestID)
                {
                    msg->requestorID = subscriptionResponse->protocolIEs.list.array[i]->value.choice.RICrequestID.ricRequestorID;
                    msg->requestSequenceNumber = subscriptionResponse->protocolIEs.list.array[i]->value.choice.RICrequestID.ricInstanceID;
                }
                else if (subscriptionResponse->protocolIEs.list.array[i]->id == ProtocolIE_ID_id_RANfunctionID)
                {
                    msg->ranfunctionID = subscriptionResponse->protocolIEs.list.array[i]->value.choice.RANfunctionID;
                }
                else if (subscriptionResponse->protocolIEs.list.array[i]->id == ProtocolIE_ID_id_RICactions_Admitted)
                {
                    RICaction_Admitted_List_t *ricActionAdmittedList = &(subscriptionResponse->protocolIEs.list.array[i]->value.choice.RICaction_Admitted_List);
                    int index = 0;
                    while (index < ricActionAdmittedList->list.count)
                    {
                        RICaction_Admitted_ItemIEs_t *ricActionAdmittedItem = (RICaction_Admitted_ItemIEs_t *)ricActionAdmittedList->list.array[index];
                        if (ricActionAdmittedItem->id == ProtocolIE_ID_id_RICaction_Admitted_Item)
                        {
                            msg->ricActionAdmittedList.ricActionID[index] = ricActionAdmittedItem->value.choice.RICaction_Admitted_Item.ricActionID;
                        }
                        index++;
                    }
                    msg->ricActionAdmittedList.count = index;
                }
                else if (subscriptionResponse->protocolIEs.list.array[i]->id == ProtocolIE_ID_id_RICactions_NotAdmitted)
                {
                    RICaction_NotAdmitted_List_t *ricActionNotAdmittedList = &(subscriptionResponse->protocolIEs.list.array[i]->value.choice.RICaction_NotAdmitted_List);
                    int index = 0;
                    while (index < ricActionNotAdmittedList->list.count)
                    {
                        RICaction_NotAdmitted_ItemIEs_t *ricActionNotAdmittedItem = (RICaction_NotAdmitted_ItemIEs_t *)ricActionNotAdmittedList->list.array[index];
                        if (ricActionNotAdmittedItem->id == ProtocolIE_ID_id_RICaction_NotAdmitted_Item)
                        {
                            msg->ricActionNotAdmittedList.ricActionID[index] = ricActionNotAdmittedItem->value.choice.RICaction_NotAdmitted_Item.ricActionID;
                            int RICcauseType = ricActionNotAdmittedItem->value.choice.RICaction_NotAdmitted_Item.cause.present;
                            switch (RICcauseType)
                            {
                            case Cause_PR_ricRequest:
                                msg->ricActionNotAdmittedList.ricCause[index].ricCauseType = Cause_PR_ricRequest;
                                msg->ricActionNotAdmittedList.ricCause[index].ricCauseID = ricActionNotAdmittedItem->value.choice.RICaction_NotAdmitted_Item.cause.choice.ricRequest;
                                break;
                            case Cause_PR_ricService:
                                msg->ricActionNotAdmittedList.ricCause[index].ricCauseType = Cause_PR_ricService;
                                msg->ricActionNotAdmittedList.ricCause[index].ricCauseID = ricActionNotAdmittedItem->value.choice.RICaction_NotAdmitted_Item.cause.choice.ricService;
                                break;
                            case Cause_PR_transport:
                                msg->ricActionNotAdmittedList.ricCause[index].ricCauseType = Cause_PR_transport;
                                msg->ricActionNotAdmittedList.ricCause[index].ricCauseID = ricActionNotAdmittedItem->value.choice.RICaction_NotAdmitted_Item.cause.choice.transport;
                                break;
                            case Cause_PR_protocol:
                                msg->ricActionNotAdmittedList.ricCause[index].ricCauseType = Cause_PR_protocol;
                                msg->ricActionNotAdmittedList.ricCause[index].ricCauseID = ricActionNotAdmittedItem->value.choice.RICaction_NotAdmitted_Item.cause.choice.protocol;
                                break;
                            case Cause_PR_misc:
                                msg->ricActionNotAdmittedList.ricCause[index].ricCauseType = Cause_PR_misc;
                                msg->ricActionNotAdmittedList.ricCause[index].ricCauseID = ricActionNotAdmittedItem->value.choice.RICaction_NotAdmitted_Item.cause.choice.misc;
                                break;
                            }
                        }
                        index++;
                    }
                    msg->ricActionNotAdmittedList.count = index;
                }
            }
            return msg;
        }
    }
    return NULL;
}

/* RICindication */
RICindicationMsg *e2ap_decode_ric_indication_message(void *buffer, size_t buf_size)
{
    E2AP_PDU_t *pdu = decode_E2AP_PDU(buffer, buf_size);
    if (pdu == NULL)
        fprintf(stderr, "pdu is NULL\n");

    if (pdu->present != E2AP_PDU_PR_initiatingMessage)
        fprintf(stderr, "pdu->present : %d\n", pdu->present);

    if (pdu != NULL && pdu->present == E2AP_PDU_PR_initiatingMessage)
    {
        InitiatingMessage_t *initiatingMessage = pdu->choice.initiatingMessage;
        if (initiatingMessage->procedureCode == ProcedureCode_id_RICindication && initiatingMessage->value.present == InitiatingMessage__value_PR_RICindication)
        {
            RICindication_t *indication = &(initiatingMessage->value.choice.RICindication);
            RICindicationMsg *msg = (RICindicationMsg *)calloc(1, sizeof(RICindicationMsg));
            for (int i = 0; i < indication->protocolIEs.list.count; ++i)
            {
                if (indication->protocolIEs.list.array[i]->id == ProtocolIE_ID_id_RICrequestID)
                {
                    msg->requestorID = indication->protocolIEs.list.array[i]->value.choice.RICrequestID.ricRequestorID;
                    msg->requestSequenceNumber = indication->protocolIEs.list.array[i]->value.choice.RICrequestID.ricInstanceID;
                }
                else if (indication->protocolIEs.list.array[i]->id == ProtocolIE_ID_id_RANfunctionID)
                {
                    msg->ranfunctionID = indication->protocolIEs.list.array[i]->value.choice.RANfunctionID;
                }
                else if (indication->protocolIEs.list.array[i]->id == ProtocolIE_ID_id_RICactionID)
                {
                    msg->actionID = indication->protocolIEs.list.array[i]->value.choice.RICactionID;
                }
                else if (indication->protocolIEs.list.array[i]->id == ProtocolIE_ID_id_RICindicationSN)
                {
                    msg->indicationSN = indication->protocolIEs.list.array[i]->value.choice.RICindicationSN;
                }
                else if (indication->protocolIEs.list.array[i]->id == ProtocolIE_ID_id_RICindicationType)
                {
                    msg->indicationType = indication->protocolIEs.list.array[i]->value.choice.RICindicationType;
                }
                else if (indication->protocolIEs.list.array[i]->id == ProtocolIE_ID_id_RICindicationHeader)
                {
                    size_t headerSize = indication->protocolIEs.list.array[i]->value.choice.RICindicationHeader.size;
                    msg->indicationHeader = calloc(1, headerSize);
                    if (!msg->indicationHeader)
                    {
                        fprintf(stderr, "alloc RICindicationHeader failed\n");
                        e2ap_free_decoded_ric_indication_message(msg);
                        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, pdu);
                        return NULL;
                    }

                    memcpy(msg->indicationHeader, indication->protocolIEs.list.array[i]->value.choice.RICindicationHeader.buf, headerSize);
                    msg->indicationHeaderSize = headerSize;
                }
                else if (indication->protocolIEs.list.array[i]->id == ProtocolIE_ID_id_RICindicationMessage)
                {
                    size_t messsageSize = indication->protocolIEs.list.array[i]->value.choice.RICindicationMessage.size;
                    msg->indicationMessage = calloc(1, messsageSize);
                    if (!msg->indicationMessage)
                    {
                        fprintf(stderr, "alloc RICindicationMessage failed\n");
                        e2ap_free_decoded_ric_indication_message(msg);
                        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, pdu);
                        return NULL;
                    }

                    memcpy(msg->indicationMessage, indication->protocolIEs.list.array[i]->value.choice.RICindicationMessage.buf, messsageSize);
                    msg->indicationMessageSize = messsageSize;
                }
                else if (indication->protocolIEs.list.array[i]->id == ProtocolIE_ID_id_RICcallProcessID)
                {
                    size_t callProcessIDSize = indication->protocolIEs.list.array[i]->value.choice.RICcallProcessID.size;
                    msg->callProcessID = calloc(1, callProcessIDSize);
                    if (!msg->callProcessID)
                    {
                        fprintf(stderr, "alloc RICcallProcessID failed\n");
                        e2ap_free_decoded_ric_indication_message(msg);
                        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, pdu);
                        return NULL;
                    }

                    memcpy(msg->callProcessID, indication->protocolIEs.list.array[i]->value.choice.RICcallProcessID.buf, callProcessIDSize);
                    msg->callProcessIDSize = callProcessIDSize;
                }
            }
            return msg;
        }
    }
    if (pdu != NULL)
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, pdu);
    return NULL;
}

void e2ap_free_decoded_ric_indication_message(RICindicationMsg *msg)
{
    if (msg == NULL)
    {
        return;
    }

    if (msg->indicationHeader != NULL)
    {
        free(msg->indicationHeader);
        msg->indicationHeader = NULL;
    }
    if (msg->indicationMessage != NULL)
    {
        free(msg->indicationMessage);
        msg->indicationMessage = NULL;
    }
    if (msg->callProcessID != NULL)
    {
        free(msg->callProcessID);
        msg->callProcessID = NULL;
    }
    free(msg);
    msg = NULL;
}

ssize_t e2ap_encode_ric_control_request_message(void *buffer, size_t buf_size, long ricRequestorID, long ricRequestSequenceNumber, long ranFunctionID, void *callProcessIDBuffer, size_t callProcessIDSize, void *controlHeaderBuffer, size_t controlHeaderSize, void *controlMessageBuffer, size_t controlMessageSize, long controlAckRequest)
{
    E2AP_PDU_t *init = (E2AP_PDU_t *)calloc(1, sizeof(E2AP_PDU_t));
    if (!init)
    {
        fprintf(stderr, "alloc E2AP_PDU failed\n");
        return -1;
    }

    InitiatingMessage_t *initiatingMsg = (InitiatingMessage_t *)calloc(1, sizeof(InitiatingMessage_t));
    if (!initiatingMsg)
    {
        fprintf(stderr, "alloc InitiatingMessage failed\n");
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
        return -1;
    }

    init->choice.initiatingMessage = initiatingMsg;
    init->present = E2AP_PDU_PR_initiatingMessage;

    initiatingMsg->procedureCode = ProcedureCode_id_RICcontrol;
    initiatingMsg->criticality = Criticality_reject;
    initiatingMsg->value.present = InitiatingMessage__value_PR_RICcontrolRequest;

    RICcontrolRequest_t *control_request = &(initiatingMsg->value.choice.RICcontrolRequest);

    // request contains 6 IEs

    // RICrequestID
    RICcontrolRequest_IEs_t *ies_reqID = (RICcontrolRequest_IEs_t *)calloc(1, sizeof(RICcontrolRequest_IEs_t));
    if (!ies_reqID)
    {
        fprintf(stderr, "alloc RICrequestID failed\n");
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
        return -1;
    }

    ies_reqID->criticality = Criticality_reject;
    ies_reqID->id = ProtocolIE_ID_id_RICrequestID;
    ies_reqID->value.present = RICcontrolRequest_IEs__value_PR_RICrequestID;
    RICrequestID_t *ricrequest_ie = &ies_reqID->value.choice.RICrequestID;
    ricrequest_ie->ricRequestorID = ricRequestorID;
    ricrequest_ie->ricInstanceID = ricRequestSequenceNumber;
    ASN_SEQUENCE_ADD(&control_request->protocolIEs.list, ies_reqID);

    // RICfunctionID
    RICcontrolRequest_IEs_t *ies_ranfunc = (RICcontrolRequest_IEs_t *)calloc(1, sizeof(RICcontrolRequest_IEs_t));
    if (!ies_ranfunc)
    {
        fprintf(stderr, "alloc RICfunctionID failed\n");
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
        return -1;
    }

    ies_ranfunc->criticality = Criticality_reject;
    ies_ranfunc->id = ProtocolIE_ID_id_RANfunctionID;
    ies_ranfunc->value.present = RICcontrolRequest_IEs__value_PR_RANfunctionID;
    RANfunctionID_t *ranfunction_ie = &ies_ranfunc->value.choice.RANfunctionID;
    *ranfunction_ie = ranFunctionID;
    ASN_SEQUENCE_ADD(&control_request->protocolIEs.list, ies_ranfunc);

    // RICcallProcessID
    if (callProcessIDBuffer != NULL)
    {
        RICcontrolRequest_IEs_t *ies_callproc = (RICcontrolRequest_IEs_t *)calloc(1, sizeof(RICcontrolRequest_IEs_t));
        if (!ies_callproc)
        {
            fprintf(stderr, "alloc RICcallProcessID failed\n");
            ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
            return -1;
        }

        ies_callproc->criticality = Criticality_reject;
        ies_callproc->id = ProtocolIE_ID_id_RICcallProcessID;
        ies_callproc->value.present = RICcontrolRequest_IEs__value_PR_RICcallProcessID;
        RICcallProcessID_t *riccallprocess_ie = &ies_callproc->value.choice.RICcallProcessID;

        riccallprocess_ie->buf = (uint8_t *)calloc(1, callProcessIDSize);
        if (!riccallprocess_ie->buf)
        {
            fprintf(stderr, "alloc RICcallProcessID buf failed\n");
            ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
            return -1;
        }

        memcpy(riccallprocess_ie->buf, callProcessIDBuffer, callProcessIDSize);
        riccallprocess_ie->size = callProcessIDSize;

        ASN_SEQUENCE_ADD(&control_request->protocolIEs.list, ies_callproc);
    }

    // RICcontrolHeader
    RICcontrolRequest_IEs_t *ies_ctlheader = (RICcontrolRequest_IEs_t *)calloc(1, sizeof(RICcontrolRequest_IEs_t));
    if (!ies_ctlheader)
    {
        fprintf(stderr, "alloc RICcontrolHeader failed\n");
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
        return -1;
    }

    ies_ctlheader->criticality = Criticality_reject;
    ies_ctlheader->id = ProtocolIE_ID_id_RICcontrolHeader;
    ies_ctlheader->value.present = RICcontrolRequest_IEs__value_PR_RICcontrolHeader;
    RICcontrolHeader_t *ricctlheader_ie = &ies_ctlheader->value.choice.RICcontrolHeader;

    ricctlheader_ie->buf = (uint8_t *)calloc(1, controlHeaderSize);
    if (!ricctlheader_ie->buf)
    {
        fprintf(stderr, "alloc RICcontrolHeader buf failed\n");
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
        return -1;
    }

    memcpy(ricctlheader_ie->buf, controlHeaderBuffer, controlHeaderSize);
    ricctlheader_ie->size = controlHeaderSize;

    ASN_SEQUENCE_ADD(&control_request->protocolIEs.list, ies_ctlheader);

    // RICcontrolMessage
    RICcontrolRequest_IEs_t *ies_ctlmsg = (RICcontrolRequest_IEs_t *)calloc(1, sizeof(RICcontrolRequest_IEs_t));
    if (!ies_ctlmsg)
    {
        fprintf(stderr, "alloc RICcontrolMessage failed\n");
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
        return -1;
    }

    ies_ctlmsg->criticality = Criticality_reject;
    ies_ctlmsg->id = ProtocolIE_ID_id_RICcontrolMessage;
    ies_ctlmsg->value.present = RICcontrolRequest_IEs__value_PR_RICcontrolMessage;
    RICcontrolMessage_t *ricctlmsg_ie = &ies_ctlmsg->value.choice.RICcontrolMessage;

    ricctlmsg_ie->buf = (uint8_t *)calloc(1, controlMessageSize);
    if (!ricctlmsg_ie->buf)
    {
        fprintf(stderr, "alloc RICcontrolMessage buf failed\n");
        ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
        return -1;
    }

    memcpy(ricctlmsg_ie->buf, controlMessageBuffer, controlMessageSize);
    ricctlmsg_ie->size = controlMessageSize;

    ASN_SEQUENCE_ADD(&control_request->protocolIEs.list, ies_ctlmsg);

    // RICcontrolAckRequest
    if (controlAckRequest != -1)
    {
        RICcontrolRequest_IEs_t *ies_ctlackreq = (RICcontrolRequest_IEs_t *)calloc(1, sizeof(RICcontrolRequest_IEs_t));
        if (!ies_ctlackreq)
        {
            fprintf(stderr, "alloc RICcontrolAckRequest failed\n");
            ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, init);
            return -1;
        }

        ies_ctlackreq->criticality = Criticality_reject;
        ies_ctlackreq->id = ProtocolIE_ID_id_RICcontrolAckRequest;
        ies_ctlackreq->value.present = RICcontrolRequest_IEs__value_PR_RICcontrolAckRequest;
        RICcontrolAckRequest_t *ricctlackreq_ie = &ies_ctlackreq->value.choice.RICcontrolAckRequest;
        *ricctlackreq_ie = controlAckRequest;
        ASN_SEQUENCE_ADD(&control_request->protocolIEs.list, ies_ctlackreq);
    }

    return encode_E2AP_PDU(init, buffer, buf_size);
}
