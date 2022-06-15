import json
import ricxappframe.xapp_subscribe
import ricxappframe.subsclient
import ricxappframe.xapp_rest


class MockApiClientResponse:
    def __init__(self, data, reason, status):
        self.data = data
        self.status = status
        self.reason = reason


class MockApiClientLoader(ricxappframe.subsclient.ApiClient):
    def __init__(self, config):
        return

    def __del__(self):
        return

    def request(self, method, url, headers, body=None):
        if method == 'POST':
            data = (
                '{ "SubscriptionResponse": {'
                '"SubscriptionId": "testing",'
                '"SubscriptionInstances": [{'
                '"XappEventInstanceID": "16253",'
                '"E2EventInstanceID": "1241"'
                '}]'
                '}}'
            )
            return MockApiClientResponse(data, 'OK', 200)
        elif method == 'DELETE':
            return MockApiClientResponse(None, 'OK', 204)
        elif method == 'GET':
            data = (
                '{ "SubscriptionList": [{'
                '"SubscriptionId": "12345",'
                '"Meid": "gnb123456",'
                '"ClientEndpoint": ["127.0.0.1:4056"],'
                '"SubscriptionInstances": [{'
                '"XappEventInstanceID": "16253",'
                '"E2EventInstanceID": "1241"'
                '}]'
                '}]'
                '}'
            )
            return MockApiClientResponse(data, 'OK', 200)


def test_subscribe(monkeypatch):

    monkeypatch.setattr("ricxappframe.subsclient.ApiClient", MockApiClientLoader)

    subscriber = ricxappframe.xapp_subscribe.NewSubscriber("http://127.0.0.1:8088/ric/v1", local_port=9099)
    # setup the subscription
    subEndPoint = subscriber.SubscriptionParamsClientEndpoint("localhost", 8091, 4061)
    assert subEndPoint.to_dict() == {'host': 'localhost', 'http_port': 8091, 'rmr_port': 4061}

    subsDirective = subscriber.SubscriptionParamsE2SubscriptionDirectives(10, 2, False)
    assert subsDirective.to_dict() == {'e2_retry_count': 2, 'e2_timeout_timer_value': 10, 'rmr_routing_needed': False}

    subsequentAction = subscriber.SubsequentAction("continue", "w10ms")
    assert subsequentAction.to_dict() == {'subsequent_action_type': 'continue', 'time_to_wait': 'w10ms'}

    actionDefinitionList = subscriber.ActionToBeSetup(1, "policy", (11, 12, 13, 14, 15), subsequentAction)
    assert actionDefinitionList.to_dict() == {
                                                'action_definition': (11, 12, 13, 14, 15),
                                                'action_id': 1, 'action_type': 'policy',
                                                'subsequent_action': {
                                                    'subsequent_action_type': 'continue',
                                                    'time_to_wait': 'w10ms'
                                                }
                                             }

    subsDetail = subscriber.SubscriptionDetail(12110, (1, 2, 3, 4, 5), actionDefinitionList)
    assert subsDetail.to_dict() == {
                                        'action_to_be_setup_list': {
                                            'action_definition': (11, 12, 13, 14, 15),
                                            'action_id': 1, 'action_type': 'policy',
                                            'subsequent_action': {
                                                'subsequent_action_type': 'continue',
                                                'time_to_wait': 'w10ms'
                                            }
                                        },
                                        'event_triggers': (1, 2, 3, 4, 5),
                                        'xapp_event_instance_id': 12110
                                    }

    # subscription data ready, make the subscription
    subObj = subscriber.SubscriptionParams("sub10", subEndPoint, "gnb123456", 1231, subsDirective, subsDetail)
    assert subObj.to_dict() == {
                                    'client_endpoint': {
                                        'host': 'localhost', 'http_port': 8091, 'rmr_port': 4061
                                    },
                                    'e2_subscription_directives': {
                                        'e2_retry_count': 2, 'e2_timeout_timer_value': 10,
                                        'rmr_routing_needed': False
                                    },
                                    'meid': 'gnb123456', 'ran_function_id': 1231, 'subscription_details': {
                                        'action_to_be_setup_list': {
                                            'action_definition': (11, 12, 13, 14, 15),
                                            'action_id': 1, 'action_type': 'policy', 'subsequent_action': {
                                                'subsequent_action_type': 'continue', 'time_to_wait': 'w10ms'
                                            }
                                        },
                                        'event_triggers': (1, 2, 3, 4, 5), 'xapp_event_instance_id': 12110
                                    },
                                    'subscription_id': 'sub10'
                                }

    data, resp, status = subscriber.Subscribe(subObj)
    assert json.loads(data) == {"SubscriptionResponse": {
                                    "SubscriptionId": "testing", "SubscriptionInstances": [{
                                        "XappEventInstanceID": "16253", "E2EventInstanceID": "1241"
                                    }]
                                }}
    assert resp == 'OK'
    assert status == 200


def test_unsubscribe(monkeypatch):

    monkeypatch.setattr("ricxappframe.subsclient.ApiClient", MockApiClientLoader)

    subscriber = ricxappframe.xapp_subscribe.NewSubscriber("http://127.0.0.1:8088/ric/v1", local_port=9099)
    data, resp, status = subscriber.UnSubscribe('1654236')
    assert resp == 'OK'
    assert status == 204


def test_QuerySubscriptions(monkeypatch):

    monkeypatch.setattr("ricxappframe.subsclient.ApiClient", MockApiClientLoader)

    subscriber = ricxappframe.xapp_subscribe.NewSubscriber("http://127.0.0.1:8088/ric/v1", local_port=9099)
    data, resp, status = subscriber.QuerySubscriptions()
    assert json.loads(data) == {'SubscriptionList': [{'SubscriptionId': '12345', 'Meid': 'gnb123456',
                                'ClientEndpoint': ['127.0.0.1:4056'], 'SubscriptionInstances':
                                [{'XappEventInstanceID': '16253', 'E2EventInstanceID': '1241'}]}]}
    assert resp == 'OK'
    assert status == 200


def test_ResponseHandler(monkeypatch):

    def subsResponseCB(name, path, data, ctype):
        response = ricxappframe.xapp_rest.initResponse()
        response['payload'] = ("{}")
        return response

    monkeypatch.setattr("ricxappframe.subsclient.ApiClient", MockApiClientLoader)

    subscriber = ricxappframe.xapp_subscribe.NewSubscriber("http://127.0.0.1:8088/ric/v1", local_port=9099)
    ret = subscriber.ResponseHandler(subsResponseCB)

    assert ret is True
