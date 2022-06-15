import sys
import time
import json
import argparse

sys.path.insert(0, './')

import ricxappframe.xapp_rest as ricrest

def respPostHandler(name, path, data, ctype):
    print(name)
    print(path)
    print(data)
    response = ricrest.initResponse()
    response['payload'] = ('{ "SubscriptionResponse": {'
        '"SubscriptionId": "testing",'
        '"SubscriptionInstances": [{'
            '"XappEventInstanceID": "16253",'
            '"E2EventInstanceID": "1241"'
            '}]'
        '}'
    '}')
    return response


def respSymptomGetHandler(name, path, data, ctype):
    print(name)
    print(path)
    response = ricrest.initResponse()
    response['payload'] = ('[{"service" : "xapp-test"}]')
    print(json.loads(response['payload']))
    return response

def respGetHandler(name, path, data, ctype):
    print(name)
    print(path)
    response = ricrest.initResponse()
    response['payload'] = ('{ "SubscriptionList": [{'
            '"SubscriptionId": "12345",'
            '"Meid": "gnb123456",'
			'"ClientEndpoint": ["127.0.0.1:4056"],'
            '"SubscriptionInstances": [{'
                '"XappEventInstanceID": "16253",'
                '"E2EventInstanceID": "1241"'
                '}]'
            '}]'
        '}')
    return response

def respDeleteHandler(name, path, data, ctype):
    print(name)
    print(path)
    response = ricrest.initResponse()
    response['payload'] = ('{}')
    return response

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-port', dest='port', help='HTTP rest server listen port', required=False, type=int)
    parser.add_argument('-address', dest='address', help='HTTP rest IP listen address, default all interfaces', required=False, type=str)
    
    args = parser.parse_args()
    
    if args.port is None:
        args.port = 8088 
    if args.address is None:
        args.address = "0.0.0.0"

    # create the thread HTTP server
    server = ricrest.ThreadedHTTPServer(args.address, args.port)
    # trick to get the own handler with defined 
    server.handler.add_handler(server.handler, "GET", "response", "/ric/v1/subscriptions", respGetHandler)
    server.handler.add_handler(server.handler, "DELETE", "delete", "/ric/v1/subscriptions/", respDeleteHandler)
    server.handler.add_handler(server.handler, "GET", "lwsdget", "/ric/v1/lwsd", respSymptomGetHandler)
    server.handler.add_handler(server.handler, "POST", "lwsdpost", "/ric/v1/lwsd", respSymptomGetHandler)
    server.handler.add_handler(server.handler, "POST", "responsepost", "/ric/v1", respPostHandler)
    # for symptomdata subscription

    server.start()
    while True:
        time.sleep(60)
    server.stop()
