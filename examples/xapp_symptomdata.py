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

#sys.path.insert(0, '../ricxappframe/xapp-frame-py')
from ricxappframe.xapp_frame import RMRXapp, rmr
from ricxappframe.xapp_sdl import SDLWrapper
from ricxappframe.xapp_symptomdata import Symptomdata

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


class RestHandler(http.server.BaseHTTPRequestHandler):
    # responds to http request according to the process status
    global symptomHndl
    
    def _set_headers(self, status, length=0, ctype = 'application/json', attachment = None):
        self.send_response(status)
        self.send_header("Server-name", "XAPP REST SERVER 1.0")
        self.send_header('Content-type', ctype)
        if length != 0:
            self.send_header('Content-length', length)
        if attachment != None:
            self.send_header('Content-Disposition', "attachment; filename=" + attachment)
        self.end_headers()
        
    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        try:
            logging.debug("POST %s" % (self.path))
        except (socket.error, IOError):
            pass

    def do_DELETE(self):
        try:
            logging.debug("DELETE %s" % (self.path))
        except (socket.error, IOError):
            pass


    def do_GET(self):
        # default get handler
        try:
            data = None
            mode = 'plain'
            ctype = 'application/json'
            attachment = None
            if self.path == "/ric/v1/health/alive":
                data = json.dumps({'status': 'alive'})
            elif self.path == "/ric/v1/health/ready":
                data = json.dumps({'status': 'ready'})
            elif self.path.find("/ric/v1/symptomdata") >= 0:
                (zipfile, size, data) = getSymptomData(symptomHndl, self.path[20:])
                if data != None:
                    mode = 'binary'
                    ctype = 'application/zip'
                    attachment = "symptomdata.zip"
                else:
                    logging.error("Symptom data does not exists")
                    self._set_headers(404, 0)
                
            if data is not None:
                length = len(data)
                self._set_headers(200, length, ctype, attachment)
                if mode == 'plain':
                    # ascii mode
                    self.wfile.write(data.encode('utf-8'))
                else:
                    # binary mode
                    self.wfile.write(data)
            else:
                logging.error("Unknown uri %s" % (self.path))
                self._set_headers(404, 0)
        except (socket.error, IOError):
            pass
 
class ThreadedHTTPServer(object):
    handler = RestHandler
    server_class = http.server.HTTPServer
    def __init__(self, host, port):
        self.server = self.server_class((host, port), self.handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True

    def start(self):
        self.server_thread.start()

    def stop(self):
        self.server.socket.close()
        self.server.server_close()
        self.server.shutdown()

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
    
    # Start the threaded server, bind to address
    server = ThreadedHTTPServer(ADDRESS, PORT)
    server.start()

    mrc, sbuf = RMR_init_xapp(b"4560")

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
