# ==================================================================================
#       Copyright (c) 2020 Nokia
#       Copyright (c) 2020 AT&T Intellectual Property.
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
"""
This framework for Python Xapps provides classes that Xapp writers
should instantiate and/or subclass depending on their needs.
"""

import json
import os
import queue
import time
from threading import Thread
from typing import List, Set

import inotify_simple
from mdclogpy import Logger

from ricxappframe import xapp_rmr
from ricxappframe.constants import sdl_namespaces
from ricxappframe.entities.rnib.nb_identity_pb2 import NbIdentity
from ricxappframe.entities.rnib.nodeb_info_pb2 import Node
from ricxappframe.rmr import rmr
from ricxappframe.util.constants import Constants
from ricxappframe.xapp_sdl import SDLWrapper
import requests

# message-type constants
RIC_HEALTH_CHECK_REQ = 100
RIC_HEALTH_CHECK_RESP = 101

# environment variable with path to configuration file
CONFIG_FILE_ENV = "CONFIG_FILE"


class _BaseXapp:
    """
    This class initializes RMR, starts a thread that checks for incoming
    messages, provisions an SDL object and optionally creates a
    config-file watcher.  This private base class should not be
    instantiated by clients directly, but it defines many public methods
    that may be used by clients.

    If environment variable CONFIG_FILE is defined, and that variable
    contains a path to an existing file, a watcher is defined to monitor
    modifications (writes) to that file using the Linux kernel's inotify
    feature. The watcher must be polled by calling method
    config_check().

    Parameters
    ----------
    rmr_port: int (optional, default is 4562)
        Port on which the RMR library listens for incoming messages.

    rmr_wait_for_ready: bool (optional, default is True)
        If this is True, then init waits until RMR is ready to send,
        which includes having a valid routing file. This can be set
        to False if the client wants to *receive only*.

    use_fake_sdl: bool (optional, default is False)
        if this is True, it uses the DBaaS "fake dict backend" instead
        of Redis or other backends. Set this to True when developing
        an xapp or during unit testing to eliminate the need for DBaaS.

    post_init: function (optional, default is None)
        Runs this user-provided function at the end of the init method;
        its signature should be post_init(self)
    """

    def __init__(self, rmr_port=4562, rmr_wait_for_ready=True, use_fake_sdl=False, post_init=None):
        """
        Documented in the class comment.
        """
        # PUBLIC, can be used by xapps using self.(name):
        self.logger = Logger(name=__name__)

        # Start rmr rcv thread
        self._rmr_loop = xapp_rmr.RmrLoop(port=rmr_port, wait_for_ready=rmr_wait_for_ready)
        self._mrc = self._rmr_loop.mrc  # for convenience

        # SDL
        self.sdl = SDLWrapper(use_fake_sdl)

        # Config
        # The environment variable specifies the path to the Xapp config file
        self._config_path = os.environ.get(CONFIG_FILE_ENV, None)
        if self._config_path and os.path.isfile(self._config_path):
            self._inotify = inotify_simple.INotify()
            self._inotify.add_watch(self._config_path, inotify_simple.flags.MODIFY)
            self.logger.debug("__init__: watching config file {}".format(self._config_path))
        else:
            self._inotify = None
            self.logger.warning("__init__: NOT watching any config file")

        # used for thread control of Registration of Xapp
        self._keep_registration = True

        # configuration data  for xapp registration and deregistration
        self._config_data = None
        if self._config_path and os.path.isfile(self._config_path):
            with open(self._config_path) as json_file:
                self._config_data = json.load(json_file)
        else:
            self._keep_registration = False
            self.logger.error("__init__: Cannot Read config file for xapp Registration")
            self._config_data = {}


        Thread(target=self.registerXapp).start()

        # run the optionally provided user post init
        if post_init:
            post_init(self)

    def get_service(self, host, service):
        """
        To find the url for connecting to the service

        Parameters
        ----------
        host: string
            defines the hostname in the url
        service: string
            defines the servicename in the url

        Returns
        -------
        string
            url for the service
        """
        app_namespace = self._config_data.get("APP_NAMESPACE")
        if app_namespace is None:
            app_namespace = Constants.DEFAULT_XAPP_NS
        self.logger.debug("service : {} host : {},appnamespace : {}".format(service,host,app_namespace))
        svc = service.format(app_namespace.upper(), host.upper())
        urlkey = svc.replace("-", "_")
        url = os.environ.get(urlkey).split("//")
        self.logger.debug("Service urlkey : {} and url: {}".format(urlkey,url))
        if len(url) > 1:
            return url[1]
        return ""


    def do_post(self, plt_namespace, url, msg):
        """
        registration of the xapp using the url and json msg

        Parameters
        ----------
        plt_namespace: string
            platform namespace where the xapp is running
        url: string
            url for xapp registration
        msg: string
            json msg containing the xapp details

        Returns
        -------
        bool
            whether or not the xapp is registered
        """
        try:
            request_url = url.format(plt_namespace, plt_namespace)
            resp = requests.post(request_url, json=msg)
            self.logger.debug("Post to '{}' done, status : {}".format(request_url, resp.status_code))
            self.logger.debug("Response Text : {}".format(resp.text))
            return resp.status_code == 200 or resp.status_code == 201
        except requests.exceptions.RequestException as err:
            self.logger.error("Error : {}".format(err))
            return format(err)
        except requests.exceptions.HTTPError as errh:
            self.logger.error("Http Error: {}".format(errh))
            return errh
        except requests.exceptions.ConnectionError as errc:
            self.logger.error("Error Connecting: {}".format(errc))
            return errc
        except requests.exceptions.Timeout as errt:
            self.logger.error("Timeout Error: {}".format(errt))
            return errt

    @property
    def register(self):
        """
            function to registers the xapp

        Returns
        -------
        bool
            whether or not the xapp is registered
        """
        hostname = os.environ.get("HOSTNAME")
        xappname = self._config_data.get("name")
        xappversion = self._config_data.get("version")
        pltnamespace = os.environ.get("PLT_NAMESPACE")
        if pltnamespace is None:
            pltnamespace = Constants.DEFAULT_PLT_NS
        self.logger.debug("config details hostname : {} xappname: {} xappversion : {} pltnamespace : {}".format(hostname, xappname,
                                                                                                  xappversion,
                                                                                                  pltnamespace))

        http_endpoint = self.get_service(hostname, Constants.SERVICE_HTTP)
        rmr_endpoint = self.get_service(hostname, Constants.SERVICE_RMR)
        if http_endpoint == "" or rmr_endpoint == "":
            self.logger.error(
                "Couldn't resolve service endpoints: http_endpoint={} rmr_endpoint={}".format(http_endpoint,
                                                                                              rmr_endpoint))
            return False
        self.logger.debug(
            "config details hostname : {} xappname: {} xappversion : {} pltnamespace : {} http_endpoint : {} rmr_endpoint : {} configpath : {}".format(
                hostname, xappname, xappversion, pltnamespace, http_endpoint, rmr_endpoint,
                self._config_data.get("CONFIG_PATH")))
        request_string = {
            "appName": hostname,
            "appVersion": xappversion,
            "configPath": "",
            "appInstanceName": xappname,
            "httpEndpoint": http_endpoint,
            "rmrEndpoint": rmr_endpoint,
            "config": json.dumps(self._config_data)
        }
        self.logger.info("REQUEST STRING :{}".format((request_string)))
        return self.do_post(pltnamespace, Constants.REGISTER_PATH, request_string)

    def registerXapp(self):
        """
            registers the xapp
        """
        while self._keep_registration:
            time.sleep(5)
            # checking for rmr/sdl/xapp health
            healthy = self.healthcheck()
            if not healthy:
                self.logger.warning(
                    "Application='{}' is not ready yet, waiting ...".format(self._config_data.get("name")))
                continue

            self.logger.debug("Application='{}'  is now up and ready, continue with registration ...".format(
                self._config_data.get("name")))
            if self.register():
                self.logger.debug("Registration done, proceeding with startup ...")
                break

    def deregister(self):
        """
            Deregisters the xapp

        Returns
        -------
        bool
            whether or not the xapp is registered
        """
        healthy = self.healthcheck()
        if not healthy:
            self.logger.error("RMR or SDL or xapp == Not Healthy")
            return None
        if self._config_data is None:
            return None
        name = os.environ.get("HOSTNAME")
        xappname = self._config_data.get("name")
        pltnamespace = os.environ.get("PLT_NAMESPACE")
        if pltnamespace is None:
            pltnamespace = Constants.DEFAULT_PLT_NS
        request_string = {
                "appName": name,
                "appInstanceName": xappname,
        }

        return self.do_post(pltnamespace, Constants.DEREGISTER_PATH, request_string)

    def xapp_shutdown(self):
        """
             Deregisters the xapp while shutting down
        """
        self.deregister()
        self.logger.debug("Wait for xapp to get unregistered")
        time.sleep(10)

    # Public rmr methods

    def rmr_get_messages(self):
        """
        Returns a generator iterable over all items in the queue that
        have not yet been read by the client xapp. Each item is a tuple
        (S, sbuf) where S is a message summary dict and sbuf is the raw
        message. The caller MUST call rmr.rmr_free_msg(sbuf) when
        finished with each sbuf to prevent memory leaks!
        """
        while not self._rmr_loop.rcv_queue.empty():
            (summary, sbuf) = self._rmr_loop.rcv_queue.get()
            yield (summary, sbuf)

    def rmr_send(self, payload, mtype, retries=100):
        """
        Allocates a buffer, sets payload and mtype, and sends

        Parameters
        ----------
        payload: bytes
            payload to set
        mtype: int
            message type
        retries: int (optional)
            Number of times to retry at the application level before excepting RMRFailure

        Returns
        -------
        bool
            whether or not the send worked after retries attempts
        """
        sbuf = rmr.rmr_alloc_msg(vctx=self._mrc, size=len(payload), payload=payload, gen_transaction_id=True,
                                 mtype=mtype)

        for _ in range(retries):
            sbuf = rmr.rmr_send_msg(self._mrc, sbuf)
            if sbuf.contents.state == 0:
                self.rmr_free(sbuf)
                return True

        self.rmr_free(sbuf)
        return False

    def rmr_rts(self, sbuf, new_payload=None, new_mtype=None, retries=100):
        """
        Allows the xapp to return to sender, possibly adjusting the
        payload and message type before doing so.  This does NOT free
        the sbuf for the caller as the caller may wish to perform
        multiple rts per buffer. The client needs to free.

        Parameters
        ----------
        sbuf: ctypes c_void_p
             Pointer to an rmr message buffer
        new_payload: bytes (optional)
            New payload to set
        new_mtype: int (optional)
            New message type (replaces the received message)
        retries: int (optional, default 100)
            Number of times to retry at the application level

        Returns
        -------
        bool
            whether or not the send worked after retries attempts
        """
        for _ in range(retries):
            sbuf = rmr.rmr_rts_msg(self._mrc, sbuf, payload=new_payload, mtype=new_mtype)
            if sbuf.contents.state == 0:
                return True

        self.logger.warning("RTS Failed! Summary: {}".format(rmr.message_summary(sbuf)))
        return False

    def rmr_free(self, sbuf):
        """
        Frees an rmr message buffer after use

        Note: this does not need to be a class method, self is not
        used. However if we break it out as a function we need a home
        for it.

        Parameters
        ----------
        sbuf: ctypes c_void_p
             Pointer to an rmr message buffer
        """
        rmr.rmr_free_msg(sbuf)

    # Convenience (pass-thru) function for invoking SDL.

    def sdl_set(self, namespace, key, value, usemsgpack=True):
        """
        ** Deprecate Warning **
        ** Will be removed in a future function **

        Stores a key-value pair to SDL, optionally serializing the value
        to bytes using msgpack.

        Parameters
        ----------
        namespace: string
            SDL namespace
        key: string
            SDL key
        value:
            Object or byte array to store.  See the `usemsgpack` parameter.
        usemsgpack: boolean (optional, default is True)
            Determines whether the value is serialized using msgpack before storing.
            If usemsgpack is True, the msgpack function `packb` is invoked
            on the value to yield a byte array that is then sent to SDL.
            Stated differently, if usemsgpack is True, the value can be anything
            that is serializable by msgpack.
            If usemsgpack is False, the value must be bytes.
        """
        self.sdl.set(namespace, key, value, usemsgpack)

    def sdl_get(self, namespace, key, usemsgpack=True):
        """
        ** Deprecate Warning **
        ** Will be removed in a future function **

        Gets the value for the specified namespace and key from SDL,
        optionally deserializing stored bytes using msgpack.

        Parameters
        ----------
        namespace: string
            SDL namespace
        key: string
            SDL key
        usemsgpack: boolean (optional, default is True)
            If usemsgpack is True, the byte array stored by SDL is deserialized
            using msgpack to yield the original object that was stored.
            If usemsgpack is False, the byte array stored by SDL is returned
            without further processing.

        Returns
        -------
        Value
            See the usemsgpack parameter for an explanation of the returned value type.
            Answers None if the key is not found.
        """
        return self.sdl.get(namespace, key, usemsgpack)

    def sdl_find_and_get(self, namespace, prefix, usemsgpack=True):
        """
        ** Deprecate Warning **
        ** Will be removed in a future function **

        Gets all key-value pairs in the specified namespace
        with keys that start with the specified prefix,
        optionally deserializing stored bytes using msgpack.

        Parameters
        ----------
        nnamespaces: string
           SDL namespace
        prefix: string
            the key prefix
        usemsgpack: boolean (optional, default is True)
            If usemsgpack is True, the byte array stored by SDL is deserialized
            using msgpack to yield the original value that was stored.
            If usemsgpack is False, the byte array stored by SDL is returned
            without further processing.

        Returns
        -------
        Dictionary of key-value pairs
            Each key has the specified prefix.
            The value object (its type) depends on the usemsgpack parameter,
            but is either a Python object or raw bytes as discussed above.
            Answers an empty dictionary if no keys matched the prefix.
        """
        return self.sdl.find_and_get(namespace, prefix, usemsgpack)

    def sdl_delete(self, namespace, key):
        """
        ** Deprecate Warning **
        ** Will be removed in a future function **

        Deletes the key-value pair with the specified key in the specified namespace.

        Parameters
        ----------
        namespace: string
           SDL namespace
        key: string
            SDL key
        """
        self.sdl.delete(namespace, key)

    def _get_rnib_info(self, node_type):
        """
        Since the difference between get_list_gnb_ids and get_list_enb_ids is only note-type,
        this function extracted from the duplicated logic.

        Parameters
        ----------
        node_type: string
           Type of node. This is EnumDescriptor.
           Available node types
           - UNKNOWN
           - ENG
           - GNB

        Returns
        -------
            List: (NbIdentity)

        Raises
        -------
            SdlTypeError: If function's argument is of an inappropriate type.
            NotConnected: If SDL is not connected to the backend data storage.
            RejectedByBackend: If backend data storage rejects the request.
            BackendError: If the backend data storage fails to process the request.
        """
        nbid_strings: Set[bytes] = self.sdl.get_members(sdl_namespaces.E2_MANAGER, node_type, usemsgpack=False)
        ret: List[NbIdentity] = []
        for nbid_string in nbid_strings:
            nbid = NbIdentity()
            nbid.ParseFromString(nbid_string)
            ret.append(nbid)
        return ret

    def get_list_gnb_ids(self):
        """
        Retrieves the list of gNodeb identity entities

        gNodeb information is stored in SDL by E2Manager. Therefore, gNode information
        is stored in SDL's `e2Manager` namespace as protobuf serialized.

        Returns
        -------
            List: (NbIdentity)

        Raises
        -------
            SdlTypeError: If function's argument is of an inappropriate type.
            NotConnected: If SDL is not connected to the backend data storage.
            RejectedByBackend: If backend data storage rejects the request.
            BackendError: If the backend data storage fails to process the request.
        """
        return self._get_rnib_info(Node.Type.Name(Node.Type.GNB))

    def get_list_enb_ids(self):
        """
        Retrieves the list of eNodeb identity entities

        eNodeb information is stored in SDL by E2Manager. Therefore, eNode information
        is stored in SDL's `e2Manager` namespace as protobuf serialized.

        Returns
        -------
            List: (NbIdentity)

        Raises
        ------
            SdlTypeError: If function's argument is of an inappropriate type.
            NotConnected: If SDL is not connected to the backend data storage.
            RejectedByBackend: If backend data storage rejects the request.
            BackendError: If the backend data storage fails to process the request.
        """
        return self._get_rnib_info(Node.Type.Name(Node.Type.ENB))

    # Health

    def healthcheck(self):
        """
        this needs to be understood how this is supposed to work
        """
        return self._rmr_loop.healthcheck() and self.sdl.healthcheck()

    # Convenience function for discovering config change events

    def config_check(self, timeout=0):
        """
        Checks the watcher for configuration-file events. The watcher
        prerequisites and event mask are documented in __init__().

        Parameters
        ----------
        timeout: int (optional)
            Number of seconds to wait for a configuration-file event, default 0.

        Returns
        -------
        List of Events, possibly empty
            An event is a tuple with objects wd, mask, cookie and name.
            For example::

                Event(wd=1, mask=1073742080, cookie=0, name='foo')

        """
        if not self._inotify:
            return []
        events = self._inotify.read(timeout=timeout)
        return list(events)

    def stop(self):
        """
        cleans up and stops the xapp rmr thread (currently). This is
        critical for unit testing as pytest will never return if the
        thread is running.

        TODO: can we register a ctrl-c handler so this gets called on
        ctrl-c? Because currently two ctrl-c are needed to stop.
        """

        self.xapp_shutdown()

        self._rmr_loop.stop()


# Public classes that Xapp writers should instantiate or subclass
# to implement an Xapp.


class RMRXapp(_BaseXapp):
    """
    Represents an Xapp that reacts only to RMR messages; i.e., the Xapp
    only performs an action when a message is received.  Clients should
    invoke the run method, which has a loop that waits for RMR messages
    and calls the appropriate client-registered consume callback on each.

    If environment variable CONFIG_FILE is defined, and that variable
    contains a path to an existing file, this class polls a watcher
    defined on that file to detect file-write events, and invokes a
    configuration-change handler on each event. The handler is also
    invoked at startup.  If no handler function is supplied to the
    constructor, this class defines a default handler that only logs a
    message.

    Parameters
    ----------
    default_handler: function
        A function with the signature (summary, sbuf) to be called when a
        message type is received for which no other handler is registered.
    default_handler argument summary: dict
        The RMR message summary, a dict of key-value pairs
    default_handler argument sbuf: ctypes c_void_p
        Pointer to an RMR message buffer. The user must call free on this when done.
    config_handler: function (optional, default is documented above)
        A function with the signature (json) to be called at startup and each time
        a configuration-file change event is detected. The JSON object is read from
        the configuration file, if the prerequisites are met.
    config_handler argument json: dict
        The contents of the configuration file, parsed as JSON.
    rmr_port: integer (optional, default is 4562)
        Initialize RMR to listen on this port
    rmr_wait_for_ready: boolean (optional, default is True)
        Wait for RMR to signal ready before starting the dispatch loop
    use_fake_sdl: boolean (optional, default is False)
        Use an in-memory store instead of the real SDL service
    post_init: function (optional, default None)
        Run this function after the app initializes and before the dispatch loop starts;
        its signature should be post_init(self)
    """

    def __init__(self, default_handler, config_handler=None, rmr_port=4562, rmr_wait_for_ready=True, use_fake_sdl=False,
                 post_init=None):
        """
        Also see _BaseXapp
        """
        # init base
        super().__init__(
            rmr_port=rmr_port, rmr_wait_for_ready=rmr_wait_for_ready, use_fake_sdl=use_fake_sdl, post_init=post_init
        )

        # setup callbacks
        self._default_handler = default_handler
        self._config_handler = config_handler
        self._dispatch = {}

        # used for thread control
        self._keep_going = True

        # register a default healthcheck handler
        # this default checks that rmr is working and SDL is working
        # the user can override this and register their own handler
        # if they wish since the "last registered callback wins".
        def handle_healthcheck(self, summary, sbuf):
            healthy = self.healthcheck()
            payload = b"OK\n" if healthy else b"ERROR [RMR or SDL is unhealthy]\n"
            self.rmr_rts(sbuf, new_payload=payload, new_mtype=RIC_HEALTH_CHECK_RESP)
            self.rmr_free(sbuf)

        self.register_callback(handle_healthcheck, RIC_HEALTH_CHECK_REQ)

        # define a default configuration-change handler if none was provided.
        if not config_handler:
            def handle_config_change(self, config):
                self.logger.debug("xapp_frame: default config handler invoked")

            self._config_handler = handle_config_change

        # call the config handler at startup if prereqs were met
        if self._inotify:
            with open(self._config_path) as json_file:
                data = json.load(json_file)
            self.logger.debug("run: invoking config handler at start")
            self._config_handler(self, data)

    def register_callback(self, handler, message_type):
        """
        registers this xapp to call handler(summary, buf) when an rmr message is received of type message_type

        Parameters
        ----------
        handler: function
            a function with the signature (summary, sbuf) to be called
            when a message of type message_type is received
        summary: dict
            the rmr message summary
        sbuf: ctypes c_void_p
            Pointer to an rmr message buffer. The user must call free on this when done.

        message:type: int
            the message type to look for

        Note if this method is called multiple times for a single message type, the "last one wins".
        """
        self._dispatch[message_type] = handler

    def run(self, thread=False, rmr_timeout=5, inotify_timeout=0):
        """
        This function should be called when the reactive Xapp is ready to start.
        After start, the Xapp's handlers will be called on received messages.

        Parameters
        ----------
        thread: bool (optional, default is False)
            If False, execution is not returned and the framework loops forever.
            If True, a thread is started to run the queue read/dispatch loop
            and execution is returned to caller; the thread can be stopped
            by calling the .stop() method.

        rmr_timeout: integer (optional, default is 5 seconds)
            Length of time to wait for an RMR message to arrive.

        inotify_timeout: integer (optional, default is 0 seconds)
            Length of time to wait for an inotify event to arrive.
        """

        def loop():
            while self._keep_going:

                # poll RMR
                try:
                    (summary, sbuf) = self._rmr_loop.rcv_queue.get(block=True, timeout=rmr_timeout)
                    # dispatch
                    func = self._dispatch.get(summary[rmr.RMR_MS_MSG_TYPE], None)
                    if not func:
                        func = self._default_handler
                    self.logger.debug("run: invoking msg handler on type {}".format(summary[rmr.RMR_MS_MSG_TYPE]))
                    func(self, summary, sbuf)
                except queue.Empty:
                    # the get timed out
                    pass

                # poll configuration file watcher
                try:
                    events = self.config_check(timeout=inotify_timeout)
                    for event in events:
                        with open(self._config_path) as json_file:
                            data = json.load(json_file)
                        self.logger.debug("run: invoking config handler on change event {}".format(event))
                        self._config_handler(self, data)
                except Exception as error:
                    self.logger.error("run: configuration handler failed: {}".format(error))

        if thread:
            Thread(target=loop).start()
        else:
            loop()

    def stop(self):
        """
        Sets the flag to end the dispatch loop.
        """
        super().stop()
        self.logger.debug("Setting flag to end framework work loop.")
        self._keep_going = False


class Xapp(_BaseXapp):
    """
    Represents a generic Xapp where the client provides a single function
    for the framework to call at startup time (instead of providing callback
    functions by message type). The Xapp writer must implement and provide a
    function with a loop-forever construct similar to the `run` function in
    the `RMRXapp` class.  That function should poll to retrieve RMR messages
    and dispatch them appropriately, poll for configuration changes, etc.

    Parameters
    ----------
    entrypoint: function
        This function is called when the Xapp class's run method is invoked.
        The function signature must be just function(self)
    rmr_port: integer (optional, default is 4562)
        Initialize RMR to listen on this port
    rmr_wait_for_ready: boolean (optional, default is True)
        Wait for RMR to signal ready before starting the dispatch loop
    use_fake_sdl: boolean (optional, default is False)
        Use an in-memory store instead of the real SDL service
    """

    def __init__(self, entrypoint, rmr_port=4562, rmr_wait_for_ready=True, use_fake_sdl=False):
        """
        Parameters
        ----------

        For the other parameters, see class _BaseXapp.
        """
        # init base
        super().__init__(rmr_port=rmr_port, rmr_wait_for_ready=rmr_wait_for_ready, use_fake_sdl=use_fake_sdl)
        self._entrypoint = entrypoint

    def run(self):
        """
        This function should be called when the general Xapp is ready to start.
        """
        self._entrypoint(self)

    # there is no need for stop currently here (base has, and nothing
    # special to do here)
