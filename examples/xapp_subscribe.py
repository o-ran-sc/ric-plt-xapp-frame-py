#!/usr/bin/env python3
# ==================================================================================
#       Copyright (c) 2022 Nokia
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
import os
import sys
import time
import json
import logging
import datetime
import argparse
import threading
import http.server
import signal
import struct
import socket
import urllib.parse
from io import open
from time import gmtime, strftime

#sys.path.insert(0, os.path.abspath("./"))
#sys.path.insert(0, os.path.abspath("./ricxappframe"))
sys.path.append(os.getcwd())
from ricxappframe.xapp_frame import RMRXapp, rmr
from ricxappframe.xapp_sdl import SDLWrapper
from ricxappframe.xapp_symptomdata import Symptomdata
import ricxappframe.xapp_subscribe as subscribe
import ricxappframe.xapp_rest as ricrest

# rmr init mode - when set to port 4561 then will wait for the rtmgr to connect
# otherwise will connect to rtmgr like set below
RMR_INIT_SVC = b"4560"
MRC = None
xapp = None

def signal_handler(sig, frame):
    global server
    global MRC
    
    server.stop()
    rmr.rmr_close(MRC)
    sys.exit(0)

def RMR_init_xapp(initbind):
    global RMR_INIT_SVC
    # Init rmr
    MRC = mrc = rmr.rmr_init(initbind, rmr.RMR_MAX_RCV_BYTES, 0x00)
    while rmr.rmr_ready(mrc) == 0:
        time.sleep(1)
        print('[%d]::RMR not yet ready')
    rmr.rmr_set_stimeout(mrc, 1)
    sbuf = rmr.rmr_alloc_msg(mrc, 500)
    rmr.rmr_set_vlevel(5)
    print('[%d]::RMR ready')
    return mrc, sbuf

def Subscribe(subscriber):
    # setup the subscription data
    subEndPoint = subscriber.SubscriptionParamsClientEndpoint("localhost", 8091, 4061)
    subsDirective = subscriber.SubscriptionParamsE2SubscriptionDirectives(10, 2, False)
    subsequentAction = subscriber.SubsequentAction("continue", "w10ms")
    actionDefinitionList = subscriber.ActionToBeSetup(1, "policy", (11,12,13,14,15), subsequentAction)
    subsDetail = subscriber.SubscriptionDetail(12110, (1,2,3,4,5), actionDefinitionList)
    # subscription data ready, make the subscription
    subObj = subscriber.SubscriptionParams("sub10", subEndPoint,"gnb123456",1231, subsDirective, subsDetail)
    print(subObj.to_dict())
    # subscribe
    data, reason, status  = subscriber.Subscribe(subObj)
    # returns the json data, make it dictionary
    print(json.loads(data))

    #data, st, hdrs   = api_instance.call_api(method="POST", resource_path="/ric/v1", body=subObj.to_dict())
    #print(hdrs)
    #print(data)

    #response = api_instance.request(method="POST", url="http://127.0.0.1:8088/ric/v1", headers=None, body=subObj.to_dict())
    #print(response.getheaders())
    #print(respdict['SubscriptionResponse'])

def Unsubscribe(subscriber):
    reason, status  = subscriber.UnSubscribe("ygwefwebw")
    print(data)
    print(reason)
    print(status)

def QuerySubscribtions(subscriber):
    data, reason, status  = subscriber.QuerySubscriptions()
    print(data)
    print(reason)
    print(status)

def read_file(filename):
    try:
        with open(filename, 'r') as f:
            data = f.read()
            if len(data) == 0:
                return None
            return data
    except IOError as error:
        return None

def getSymptomData(symptomHndl, uriparams):
    paramlist = urllib.parse.parse_qs(uriparams)
    [x.upper() for x in paramlist]
    fromtime = 0
    totime = 0
    print(paramlist)
    if paramlist.get('fromTime'):
        fromtime = getSeconds(paramlist.get('fromTime')[0])
    if paramlist.get('toTime'):
        totime = getSeconds(paramlist.get('toTime')[0])
    zipfile = symptomHndl.collect("symptomdata"+'-%Y-%m-%d-%H-%M-%S.zip', ('examples/.*.py',), fromtime, totime)
    if zipfile != None:
        (zipfile, size, data) = symptomHndl.read()
        return (zipfile, size, data)
    return (None, 0, None)
       
def healthyGetReadyHandler(name, path, data, ctype):
    print(name)
    print(path)
   
    response = server.initResponse()
    response['payload'] = ("{'status': 'ready'}")
    return response

def healthyGetAliveHandler(name, path, data, ctype):
    print(name)
    print(path)
   
    response = server.initResponse()
    response['payload'] = ("{'status': 'alive'}")
    return response
        
def subsResponseCB(name, path, data, ctype):
    print(name)
    print(path)
   
    response = server.initResponse()
    response['payload'] = ("{}")
    return response

def symptomdataGetHandler(name, path, data, ctype):
    reponse = ricrest.initResponse()
    (zipfile, size, filedata) = getSymptomData(symptomHndl, self.path[20:])
    if filedata != None:
        reponse['payload'] = filedata
        reponse['ctype'] = 'application/zip'
        reponse['attachment'] = "symptomdata.zip"
        reponse['mode'] = 'binary'
        return reponse
    logging.error("Symptom data does not exists")
    reponse['response'] = 'System error - symptomdata does not exists'
    reponse['status'] = 500
    return reponse


def main():
    global server
    global xapp
    global symptomHndl
    
    # init the default values
    ADDRESS = "0.0.0.0"     # bind to all interfaces
    PORT = 8080             # web server listen port
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-port', dest='port', help='HTTP server listen port, default 3000', required=False, type=int)
    parser.add_argument('-address', dest='address', help='IP listen address, default all interfaces', required=False, type=str)
    parser.add_argument('-xapp', dest='xapp', help='xapp name', required=True, type=str)
    parser.add_argument('-service', dest='service', help='xapp service name (same as pod host name)', required=True, type=str)
    args = parser.parse_args()
    
    if args.port is not None:
        PORT = args.port
    if args.address is not None:
        ADDRESS = args.address

    # handle the RMR_SEED_RT and RMR_RTG_SVC which is different in mcxapp
    data = None
    os.environ["RMR_SRC_ID"] = args.service
    os.environ["RMR_LOG_VLEVEL"] = '4'
    os.environ["RMR_RTG_SVC"] = "4561"
    rmrseed = os.environ.get('RMR_SEED_RT')
    if rmrseed is not None:
        data = read_file(rmrseed)
        if data is None:
            print("RMR seed file %s does not exists or is empty" % (rmrseed))
    else:
        print("RMR_SEED_RT seed file not set in environment")
        data = read_file('uta-rtg.rt')
        if data is not None:
            os.environ['RMR_SEED_RT'] = "./uta-rtg.rt"
            print("Setting the default RMR_SEED_RT=uta-rtg.rt - content:")
            print(data)
        else:
            print("Try to export the RMR_SEED_RT file if your RMR is not getting ready")

    symptomHndl = Symptomdata(args.service, args.xapp, "/tmp/", "http://service-ricplt-lwsd-http:8080/ric/v1/lwsd", 10)
    
    # setup the subscription
    subscriber = subscribe.NewSubscriber("http://127.0.0.1:8088/ric/v1")
    
    # create the thread HTTP server and set the uri handler callbacks
    server = ricrest.ThreadedHTTPServer(ADDRESS, PORT)
    # trick to get the own handler with defined 
    server.handler.add_handler(server.handler, "GET", "healthAlive", "/ric/v1/health/alive", healthyGetAliveHandler)
    server.handler.add_handler(server.handler, "GET", "healthReady", "/ric/v1/health/ready", healthyGetReadyHandler)
    server.handler.add_handler(server.handler, "GET", "symptomdata", "/ric/v1/symptomdata", symptomdataGetHandler)
    # add as well the own subscription response callback handler
    if subscriber.ResponseHandler(subsResponseCB, server) is not True:
        print("Error when trying to set the subscription reponse callback")
    server.start()

    mrc, sbuf = RMR_init_xapp(b"4560")

    Subscribe(subscriber)

    while True:
        print("Waiting for a message, will timeout after 2000ms")
        sbuf = rmr.rmr_torcv_msg(mrc, None, 2000)
        summary = rmr.message_summary(sbuf)
        if summary[rmr.RMR_MS_MSG_STATE] == 12:
            print("Nothing received =(")
        else:
            print("Message received!: {}".format(summary))
            data = rmr.get_payload(sbuf)
        rmr.rmr_free_msg(sbuf)

if __name__ == '__main__':
    signal.signal(signal.SIGQUIT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    main()


