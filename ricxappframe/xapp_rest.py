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
import socket
import http.server
import threading


def initResponse(status=200, response="OK"):

    """
    initResponse
        init the reponse data for handler to get all details defined

    Parameters
    ----------
    status: int
        http status code
    response: string
        http response text
    Returns
    -------
    response - http response text
    status - http status code
    payload - payload data for the client (response data text or attachment file data)
    attachment - file name of the attached payload data
    mode text (utf-8) or binary data
    """
    return {'response': response, 'status': status, 'payload': None, 'ctype': 'application/json', 'attachment': None, 'mode': 'plain'}


class RestHandler(http.server.BaseHTTPRequestHandler):

    def _findUrihandler(self, uri, keys):
        for key in keys:
            value = keys[key]
            if uri.find(value['uri']) >= 0:
                return key, value
        return None, None

    def _sendResponse(self, response):
        # sends the reponse according to the initResponse() response data
        self.send_response(response['status'])
        self.send_header("Server-name", "XAPP REST SERVER 0.9")
        self.send_header('Content-type', response['ctype'])

        if response['payload'] is not None:
            # payload has been set
            length = len(response['payload'])
            if length != 0:
                self.send_header('Content-length', length)
            if response['attachment'] is not None:
                self.send_header('Content-Disposition', "attachment; filename=" + response['attachment'])
        self.end_headers()
        if response['payload'] is not None:
            if response['mode'] == 'plain':
                # ascii mode
                self.wfile.write(response['payload'].encode('utf-8'))
            elif response['mode'] == 'binary':
                # binary mode
                self.wfile.write(response['payload'])

    def add_handler(self, method=None, name=None, uri=None, callback=None):
        """
        Adds the function handler for given uri. The function callback is matched in first matching
        uri. So prepare your handlers setup in such a way that those won't override each other. For example you can setup
        usual xapp handler in this list:

            server = ricrest.ThreadedHTTPServer(address, port)
            server.handler.add_handler(self.server.handler, "GET", "config", "/ric/v1/config", self.configGetHandler)
            server.handler.add_handler(self.server.handler, "GET", "healthAlive", "/ric/v1/health/alive", self.healthyGetAliveHandler)
            server.handler.add_handler(self.server.handler, "GET", "healthReady", "/ric/v1/health/ready", self.healthyGetReadyHandler)
            server.handler.add_handler(self.server.handler, "GET", "symptomdata", "/ric/v1/symptomdata", self.symptomdataGetHandler)

        Parameters
        ----------
        method string
            http method GET, POST, DELETE
        name string
            unique name - used for map name
        uri string
            http uri part which triggers the callback function
        cb  function
            function to be used for http method processing
        """
        if not hasattr(self, 'handlers'):
            # init method can't be used becuase it has been inherited from base object
            # so check the handlers existence and create if not defined
            self.lock = threading.Lock()
            self.handlers = dict()
            self.handlers["get"] = dict()
            self.handlers["post"] = dict()
            self.handlers["delete"] = dict()
        self.lock.acquire()
        if method == "GET":
            self.handlers["get"][name] = dict()
            self.handlers["get"][name]['uri'] = uri
            self.handlers["get"][name]['cb'] = callback
        elif method == "POST":
            self.handlers["post"][name] = dict()
            self.handlers["post"][name]['uri'] = uri
            self.handlers["post"][name]['cb'] = callback
        elif method == "DELETE":
            self.handlers["delete"][name] = dict()
            self.handlers["delete"][name]['uri'] = uri
            self.handlers["delete"][name]['cb'] = callback
        self.lock.release()

    def do_GET(self):
        try:
            response = initResponse(status=404, response='Not Found')
            cbname, hndl = self._findUrihandler(self.path, self.handlers['get'])
            if hndl is not None:
                # call the defined callback handler
                response = hndl['cb'](cbname, self.path, None, self.headers['Content-Type'])
            self._sendResponse(response)

        except (socket.error, IOError):
            pass

    def do_DELETE(self):
        try:
            response = initResponse(status=404, response='Not Found')
            cbname, hndl = self._findUrihandler(self.path, self.handlers['delete'])
            if hndl is not None:
                # call the defined callback handler
                response = hndl['cb'](cbname, self.path, None, self.headers['Content-Type'])
            self._sendResponse(response)
        except (socket.error, IOError):
            pass

    def do_POST(self):
        try:
            response = initResponse(status=404, response='Not Found')
            cbname, hndl = self._findUrihandler(self.path, self.handlers['post'])
            if hndl is not None:
                data = self.rfile.read(int(self.headers['Content-Length']))
                # call the defined callback handler
                response = hndl['cb'](cbname, self.path, data, self.headers['Content-Type'])
                print(response)
            self._sendResponse(response)
        except (socket.error, IOError):
            pass


class ThreadedHTTPServer(object):

    handler = RestHandler
    server_class = http.server.HTTPServer

    def __init__(self, host, port):
        """
        init

        Parameters
        ----------
        host string
            http listen interface ip ("0.0.0.0" binds all interfaces)
        port int
            listen service port
        """
        self.server = self.server_class((host, port), self.handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True

    def start(self):
        """
        start
            starts the thread serving http requests
        """
        self.server_thread.start()

    def stop(self):
        """
        stop
            stops thread serving http requests
        """
        self.server.socket.close()
        self.server.server_close()
        self.server.shutdown()
