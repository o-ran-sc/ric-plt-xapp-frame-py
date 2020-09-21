#ifndef	_WRAPPER_H_
#define	_WRAPPER_H_

#include "RICsubscriptionRequest.h"
#include "RICsubscriptionResponse.h"
#include "RICsubscriptionDeleteRequest.h"
#include "RICsubscriptionDeleteResponse.h"
#include "RICcontrolRequest.h"
#include "RICindication.h"
#include "E2AP-PDU.h"
#include "InitiatingMessage.h"
#include "SuccessfulOutcome.h"
#include "UnsuccessfulOutcome.h"
#include "ProtocolIE-Container.h"
#include "ProtocolIE-Field.h"
#include "RICactionDefinition.h"
#include "RICsubsequentAction.h"
#include "CauseRIC.h"

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

typedef struct RICcauseItem {
	int ricCauseType;
	long ricCauseID;
} RICcauseItem;

typedef struct RICactionAdmittedList {
	long ricActionID[16];
	int count;
} RICactionAdmittedList;

typedef struct RICactionNotAdmittedList {
	long ricActionID[16];
	RICcauseItem ricCause[16];
	int count;
} RICactionNotAdmittedList;

typedef struct RICsubscriptionResponseMessage {
	long requestorID;
	long requestSequenceNumber;
	long ranfunctionID;
	RICactionAdmittedList ricActionAdmittedList;
	RICactionNotAdmittedList ricActionNotAdmittedList;
} RICsubscriptionResponseMsg;

typedef struct RICactionDefinition {
	uint8_t *actionDefinition;
	int size;
} RICactionDefinition;

typedef struct RICSubsequentAction {
	int isValid;
	long subsequentActionType;
	long timeToWait;
} RICSubsequentAction;

size_t encode_E2AP_PDU(E2AP_PDU_t* pdu, void* buffer, size_t buf_size);
E2AP_PDU_t* decode_E2AP_PDU(const void* buffer, size_t buf_size);

/* RICsubscriptionRequest */
ssize_t e2ap_encode_ric_subscription_request_message(void *buffer, size_t buf_size, long ricRequestorID, long ricRequestSequenceNumber, long ranFunctionID, void *eventTriggerDefinition, size_t eventTriggerDefinitionSize, int actionCount, long *actionIds, long* actionTypes, RICactionDefinition *actionDefinitions, RICSubsequentAction *subsequentActionTypes);

/* RICsubscriptionResponse */
RICsubscriptionResponseMsg* e2ap_decode_ric_subscription_response_message(void *buffer, size_t buf_size);

/* RICindication */
RICindicationMsg* e2ap_decode_ric_indication_message(void *buffer, size_t buf_size);
void e2ap_free_decoded_ric_indication_message(RICindicationMsg* msg);

/* RICControl */
ssize_t e2ap_encode_ric_control_request_message(void *buffer, size_t buf_size, long ricRequestorID, long ricRequestSequenceNumber, long ranFunctionID, void *callProcessIDBuffer, size_t callProcessIDSize, void *controlHeaderBuffer, size_t controlHeaderSize, void *controlMessageBuffer, size_t controlMessageSize, long controlAckRequest); 

#endif /* _WRAPPER_H_ */
