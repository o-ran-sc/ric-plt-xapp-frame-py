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
from mdclogpy import Logger, Level

class Config(object):
    def __init__(self, xapp_name, config_file):
        self.config_file = config_file
        self.xapp_name = xapp_name
        self.cfg = None
        self.keys = dict()
        self.config()

    def config(self):
        with open(self.config_file, 'r') as file:
            cfg = file.read()
            if cfg != None:
                self.cfg = json.loads(cfg)
                if self.cfg is not None:
                    self.controls = self.cfg['controls']

    def get_key_item(self, key):
        data = None
        if self.keys.get(key) is not None:
            data = self.keys[key]
        return data

    def get_config(self):
        data = None
        with open(self.config_file, 'r') as file:
            cfg = file.read()
            if cfg != None:
                self.cfg = json.loads(cfg)
                # following is required by the appmgr -  don't know why.
                cfgescaped = cfg.replace('"', '\\"').replace('\n', '\\n')
                data = '[{ "config": "' + cfgescaped + '", "metadata":{"configType":"json","xappName":"' + self.xapp_name + '"}}]'
        if data == None:
            logging.error("Config file %s empty or does not exists" % (self.config_file))
        return data

def read_file(filename):
    try:
        with open(filename, 'r') as f:
            data = f.read()
            if len(data) == 0:
                return None
            return data
    except IOError as error:
        return None


class MyXapp(object):

    def __init__(self, name, service, address, port, config, loglevel):
        signal.signal(signal.SIGQUIT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        self.running = False
        
        self.configData = Config(name, config)

        if self.configData.controls.get('logger'):
            level = self.configData.controls['logger'].get('level')

        if port == None and self.configData.cfg['messaging'].get('ports'):
            for item in self.configData.cfg['messaging'].get('ports'):
                if item['name'] == http:
                    port = int(item['port'])
        if address == None and self.configData.cfg.get('name'):
            address = self.configData.cfg.get('name')
            
        # save the listen address and port for later use
        self.port = port
        self.address = address
        
        self.logger = Logger(name, loglevel)
        # setup the symptomdata
        symptomCfg = self.GetSymptomConfig()
        self.symptomHndl = Symptomdata(service, name, "/tmp/", symptomCfg['url'], symptomCfg['timeout'])

        # create the thread HTTP server and set the uri handler callbacks
        self.server = ricrest.ThreadedHTTPServer(address, port)
        # trick to get the own handler with defined 
        self.server.handler.add_handler(self.server.handler, "GET", "config", "/ric/v1/config", self.configGetHandler)
        self.server.handler.add_handler(self.server.handler, "GET", "healthAlive", "/ric/v1/health/alive", self.healthyGetAliveHandler)
        self.server.handler.add_handler(self.server.handler, "GET", "healthReady", "/ric/v1/health/ready", self.healthyGetReadyHandler)
        self.server.handler.add_handler(self.server.handler, "GET", "symptomdata", "/ric/v1/symptomdata", self.symptomdataGetHandler)
        # start rest server
        self.server.start()
        # start RMR
        self.startRMR(service, 4)
        self.running = True
        # now we can subscribe
        self.Subscribe()

    def startRMR(self, service, level):
        # handle the RMR_SEED_RT and RMR_RTG_SVC which is different in mcxapp
        data = None
        os.environ["RMR_SRC_ID"] = service
        os.environ["RMR_LOG_VLEVEL"] = str(level)
        os.environ["RMR_RTG_SVC"] = "4561"
        rmrseed = os.environ.get('RMR_SEED_RT')
        if rmrseed is not None:
            data = read_file(rmrseed)
            if data is None:
                self.logger.warning("RMR seed file %s does not exists or is empty" % (rmrseed))
        else:
            self.logger.info("RMR_SEED_RT seed file not set in environment")
            data = read_file('uta-rtg.rt')
            if data is not None:
                os.environ['RMR_SEED_RT'] = "./uta-rtg.rt"
                self.logger.info("Setting the default RMR_SEED_RT=uta-rtg.rt - content:")
            else:
                self.logger.info("Try to export the RMR_SEED_RT file if your RMR is not getting ready")
        self.rmrInit(b"4560")

    def signal_handler(self, sig, frame):
        if self.running is True:
            self.server.stop()
            rmr.rmr_close(self.rmr_mrc)
        self.running = False
        sys.exit(0)

    def rmrInit(self, initbind):
        # Init rmr
        self.rmr_mrc = rmr.rmr_init(initbind, rmr.RMR_MAX_RCV_BYTES, 0x00)
        while rmr.rmr_ready(self.rmr_mrc) == 0:
            time.sleep(1)
            self.logger.info('RMR not yet ready')
        rmr.rmr_set_stimeout(self.rmr_mrc, 1)
        rmr.rmr_set_vlevel(5)
        self.logger.info('RMR ready')

    def GetSymptomConfig(self):
        if self.configData.cfg['controls'].get('symptomdata').get('lwsd'):
            return self.configData.cfg['controls'].get('symptomdata').get('lwsd')

    def GetSubsConfig(self):
        if self.configData.cfg['controls'].get('subscription'):
            return self.configData.cfg['controls'].get('subscription')

    def Subscribe(self):
        self.subsCfgDetail = self.GetSubsConfig()
        if self.subsCfgDetail != None:
            # this is example subscription, for your use case fill the attributes according to your needs
            self.subscriber = subscribe.NewSubscriber(self.subsCfgDetail['url'] + 'ric/v1')
            # add as well the own subscription response callback handler
            if self.subscriber.ResponseHandler(self.subsResponseCB, self.server) is not True:
                self.logger.error("Error when trying to set the subscription reponse callback")
            # setup the subscription data
            subEndPoint = self.subscriber.SubscriptionParamsClientEndpoint(self.subsCfgDetail['clientEndpoint'], self.port, 4061)
            subsDirective = self.subscriber.SubscriptionParamsE2SubscriptionDirectives(10, 2, False)
            subsequentAction = self.subscriber.SubsequentAction("continue", "w10ms")
            actionDefinitionList = self.subscriber.ActionToBeSetup(1, "policy", (11,12,13,14,15), subsequentAction)
            subsDetail = self.subscriber.SubscriptionDetail(12110, (1,2,3,4,5), actionDefinitionList)
            # subscription data ready, make the subscription
            subObj = self.subscriber.SubscriptionParams("sub10", subEndPoint,"gnb123456",1231, subsDirective, subsDetail)
            self.logger.info("Sending the subscription to %s" %(self.subsCfgDetail['url'] + 'ric/v1'))
            self.logger.info(subObj.to_dict())
            # subscribe
            data, reason, status  = self.subscriber.Subscribe(subObj)
            # returns the json data, make it dictionary
            self.logger.info("Getting the subscription reponse")
            self.logger.info(json.loads(data))

    def Unsubscribe(self):
        reason, status  = self.subscriber.UnSubscribe("ygwefwebw")

    def QuerySubscribtions(self):
        data, reason, status  = self.subscriber.QuerySubscriptions()

    def healthyGetReadyHandler(self, name, path, data, ctype):
        response = server.initResponse()
        response['payload'] = ("{'status': 'ready'}")
        return response

    def healthyGetAliveHandler(self, name, path, data, ctype):
        response = server.initResponse()
        response['payload'] = ("{'status': 'alive'}")
        return response
            
    def subsResponseCB(self, name, path, data, ctype):
        response = server.initResponse()
        response['payload'] = ("{}")
        return response

    def getSymptomData(self, uriparams):
        paramlist = urllib.parse.parse_qs(uriparams)
        [x.upper() for x in paramlist]
        fromtime = 0
        totime = 0
        print(paramlist)
        if paramlist.get('fromTime'):
            fromtime = getSeconds(paramlist.get('fromTime')[0])
        if paramlist.get('toTime'):
            totime = getSeconds(paramlist.get('toTime')[0])
        zipfile = self.symptomHndl.collect("symptomdata"+'-%Y-%m-%d-%H-%M-%S.zip', ('examples/.*.py',), fromtime, totime)
        if zipfile != None:
            (zipfile, size, data) = self.symptomHndl.read()
            return (zipfile, size, data)
        return (None, 0, None)

    def symptomdataGetHandler(self, name, path, data, ctype):
        reponse = ricrest.initResponse()
        (zipfile, size, filedata) = self.getSymptomData(self.path[20:])
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

    def configGetHandler(self, name, path, data, ctype):
        response = server.initResponse()
        response['payload'] = (self.configData.get_config())
        return response

def removeEnvVar(evar):
    if evar in os.environ:
        del os.environ[evar]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-port', dest='port', help='HTTP server listen port, default 8088', required=False, type=int)
    parser.add_argument('-address', dest='address', help='IP listen address, default all interfaces', required=False, type=str)
    parser.add_argument('-config', dest='config', help='config file path name, default /opt/ric/config/config.json', required=False, type=str)
    parser.add_argument('-xapp', dest='xapp', help='xapp name', required=True, type=str)
    parser.add_argument('-service', dest='service', help='xapp service name (same as pod host name)', required=True, type=str)
    parser.add_argument('-verbose', dest='verbose', help='verbose logging level', required=False, type=int)
    
    args = parser.parse_args()
    
    if args.port is None:
        args.port = 8088 
    if args.address is None:
        args.address = "0.0.0.0"
    if args.config is None:
        args.config = '/opt/ric/config/config.json'

    # remove proxy so that it won't impact to rest calls
    removeEnvVar('HTTPS_PROXY')
    removeEnvVar('HTTP_PROXY')
    removeEnvVar('https_proxy')
    removeEnvVar('http_proxy')

    # starting argument option will overwrite the config settings
    if args.verbose is None:
        args.verbose = 2

    loglevel = Level.INFO
    if args.verbose == 0:
        loglevel = Level.ERROR
    if args.verbose == 1:
        loglevel = Level.WARNING
    elif args.verbose == 2:
        loglevel = Level.INFO
    elif args.verbose >= 3:
        loglevel = Level.DEBUG

    myxapp = MyXapp(args.xapp, args.service, args.address, args.port, args.config, loglevel)

    while True:
        print("Waiting for a message, will timeout after 10s")
        rmr_sbuf = rmr.rmr_torcv_msg(myxapp.rmr_mrc, None, 10000)
        summary = rmr.message_summary(rmr_sbuf)
        if summary[rmr.RMR_MS_MSG_STATE] == 12:
            print("Nothing received")
        else:
            print("Message received!: {}".format(summary))
            data = rmr.get_payload(rmr_sbuf)
        rmr.rmr_free_msg(rmr_sbuf)

if __name__ == '__main__':
    main()


