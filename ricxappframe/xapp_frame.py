"""
Framework for python xapps
Framework here means Xapp classes that can be subclassed
"""
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
from threading import Thread
from ricxappframe import xapp_rmr
from ricxappframe.xapp_sdl import SDLWrapper
from ricxappframe.rmr import rmr
from mdclogpy import Logger

# constants
RIC_HEALTH_CHECK_REQ = 100
RIC_HEALTH_CHECK_RESP = 101


# Private base class; not for direct client use


class _BaseXapp:
    """
    Base xapp; not for client use directly
    """

    def __init__(self, rmr_port=4562, rmr_wait_for_ready=True, use_fake_sdl=False, post_init=None):
        """
        Init

        Parameters
        ----------
        rmr_port: int
            port to listen on

        rmr_wait_for_ready: bool (optional)
            if this is True, then init waits until rmr is ready to send, which includes having a valid routing file.
            this can be set to False if the client only wants to *receive only*

        use_fake_sdl: bool (optional)
            if this is True, it uses dbaas' "fake dict backend" instead of Redis or other backends.
            Set this to true when developing your xapp or during unit testing to completely avoid needing a dbaas running or any network at all

        post_init: function (optional)
            runs this user provided function after the base xapp is initialized
            it's signature should be post_init(self)
        """
        # PUBLIC, can be used by xapps using self.(name):
        self.logger = Logger(name=__name__)

        # Start rmr rcv thread
        self._rmr_loop = xapp_rmr.RmrLoop(port=rmr_port, wait_for_ready=rmr_wait_for_ready)
        self._mrc = self._rmr_loop.mrc  # for convenience

        # SDL
        self._sdl = SDLWrapper(use_fake_sdl)

        # run the optionally provided user post init
        if post_init:
            post_init(self)

    # Public rmr methods

    def rmr_get_messages(self):
        """
        returns a generator iterable over all current messages in the queue that have not yet been read by the client xapp
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
        sbuf = rmr.rmr_alloc_msg(vctx=self._mrc, size=len(payload), payload=payload, gen_transaction_id=True, mtype=mtype)

        for _ in range(retries):
            sbuf = rmr.rmr_send_msg(self._mrc, sbuf)
            if sbuf.contents.state == 0:
                self.rmr_free(sbuf)
                return True

        self.rmr_free(sbuf)
        return False

    def rmr_rts(self, sbuf, new_payload=None, new_mtype=None, retries=100):
        """
        Allows the xapp to return to sender, possibly adjusting the payload and message type before doing so

        This does NOT free the sbuf for the caller as the caller may wish to perform multiple rts per buffer.
        The client needs to free.

        Parameters
        ----------
        sbuf: ctypes c_void_p
             Pointer to an rmr message buffer
        new_payload: bytes (optional)
            New payload to set
        new_mtype: int (optional)
            New message type (replaces the received message)
        retries: int (optional)
            Number of times to retry at the application level before excepting RMRFailure

        Returns
        -------
        bool
            whether or not the send worked after retries attempts
        """
        for _ in range(retries):
            sbuf = rmr.rmr_rts_msg(self._mrc, sbuf, payload=new_payload, mtype=new_mtype)
            if sbuf.contents.state == 0:
                return True

        self.logger.info("RTS Failed! Summary: {}".format(rmr.message_summary(sbuf)))
        return False

    def rmr_free(self, sbuf):
        """
        Free an rmr message buffer after use

        Note: this does not need to be a class method, self is not used. However if we break it out as a function we need a home for it.
        Parameters
        ----------
        sbuf: ctypes c_void_p
             Pointer to an rmr message buffer
        """
        rmr.rmr_free_msg(sbuf)

    # SDL
    # NOTE, even though these are passthroughs, the seperate SDL wrapper is useful for other applications like A1.
    # Therefore, we don't embed that SDLWrapper functionality here so that it can be instantiated on it's own.

    def sdl_set(self, ns, key, value, usemsgpack=True):
        """
        set a key

        Parameters
        ----------
        ns: string
           the sdl namespace
        key: string
            the sdl key
        value:
            if usemsgpack is True, value can be anything serializable by msgpack
            if usemsgpack is False, value must be bytes
        usemsgpack: boolean (optional)
            determines whether the value is serialized using msgpack
        """
        self._sdl.set(ns, key, value, usemsgpack)

    def sdl_get(self, ns, key, usemsgpack=True):
        """
        get a key

        Parameters
        ----------
        ns: string
           the sdl namespace
        key: string
            the sdl key
        usemsgpack: boolean (optional)
            if usemsgpack is True, the value is deserialized using msgpack
            if usemsgpack is False, the value is returned as raw bytes

        Returns
        -------
        None (if not exist) or see above; depends on usemsgpack
        """
        return self._sdl.get(ns, key, usemsgpack)

    def sdl_find_and_get(self, ns, prefix, usemsgpack=True):
        """
        get all k v pairs that start with prefix

        Parameters
        ----------
        ns: string
           the sdl namespace
        key: string
            the sdl key
        prefix: string
            the prefix
        usemsgpack: boolean (optional)
            if usemsgpack is True, the value returned is a dict where each value has been deserialized using msgpack
            if usemsgpack is False, the value returned is as a dict mapping keys to raw bytes

        Returns
        -------
        {} (if no keys match) or see above; depends on usemsgpack
        """
        return self._sdl.find_and_get(ns, prefix, usemsgpack)

    def sdl_delete(self, ns, key):
        """
        delete a key

        Parameters
        ----------
        ns: string
           the sdl namespace
        key: string
            the sdl key
        """
        self._sdl.delete(ns, key)

    # Health

    def healthcheck(self):
        """
        this needs to be understood how this is supposed to work
        """
        return self._rmr_loop.healthcheck() and self._sdl.healthcheck()

    def stop(self):
        """
        cleans up and stops the xapp rmr thread (currently)
        This is critical for unit testing as pytest will never return if the thread is running.

        TODO: can we register a ctrl-c handler so this gets called on ctrl-c? Because currently two ctrl-c are needed to stop
        """
        self._rmr_loop.stop()


# Public Classes to subclass (these subclass _BaseXapp)


class RMRXapp(_BaseXapp):
    """
    Represents an xapp that is purely driven by rmr messages (i.e., when messages are received, the xapp does something
    When run is called, the xapp framework waits for rmr messages, and calls the client provided consume callback on every one
    """

    def __init__(self, default_handler, rmr_port=4562, rmr_wait_for_ready=True, use_fake_sdl=False, post_init=None):
        """
        Parameters
        ----------
        default_handler: function
            a function with the signature (summary, sbuf) to be called when a message of type message_type is received
            summary: dict
                the rmr message summary
            sbuf: ctypes c_void_p
                Pointer to an rmr message buffer. The user must call free on this when done.

        post_init: function (optional)
            optionally runs this function after the app initializes and before the run loop
            it's signature should be post_init(self)

        For the other parameters, see _BaseXapp
        """
        # init base
        super().__init__(
            rmr_port=rmr_port, rmr_wait_for_ready=rmr_wait_for_ready, use_fake_sdl=use_fake_sdl, post_init=post_init
        )

        # setup callbacks
        self._default_handler = default_handler
        self._dispatch = {}

        # used for thread control
        self._keep_going = True

        # register a default healthcheck handler
        # this default checks that rmr is working and SDL is working
        # the user can override this and register their own handler if they wish since the "last registered callback wins".
        def handle_healthcheck(self, summary, sbuf):
            ok = self.healthcheck()
            payload = b"OK\n" if ok else b"ERROR [RMR or SDL is unhealthy]\n"
            self.rmr_rts(sbuf, new_payload=payload, new_mtype=RIC_HEALTH_CHECK_RESP)
            self.rmr_free(sbuf)

        self.register_callback(handle_healthcheck, RIC_HEALTH_CHECK_REQ)

    def register_callback(self, handler, message_type):
        """
        registers this xapp to call handler(summary, buf) when an rmr message is received of type message_type

        Parameters
        ----------
        handler: function
            a function with the signature (summary, sbuf) to be called when a message of type message_type is received
            summary: dict
                the rmr message summary
            sbuf: ctypes c_void_p
                Pointer to an rmr message buffer. The user must call free on this when done.

        message:type: int
            the message type to look for

        Note if this method is called multiple times for a single message type, the "last one wins".
        """
        self._dispatch[message_type] = handler

    def run(self, thread=False):
        """
        This function should be called when the client xapp is ready to wait for their handlers to be called on received messages

        Parameters
        ----------
        thread: bool (optional)
            if thread is True, execution is returned to caller and the queue read loop is executed in a thread.
            The thread can be stopped using .stop()
            if False, execution is not returned and the framework loops
        """

        def loop():
            while self._keep_going:
                if not self._rmr_loop.rcv_queue.empty():
                    (summary, sbuf) = self._rmr_loop.rcv_queue.get()
                    # dispatch
                    func = self._dispatch.get(summary["message type"], None)
                    if not func:
                        func = self._default_handler
                    func(self, summary, sbuf)

        if thread:
            Thread(target=loop).start()
        else:
            loop()

    def stop(self):
        """
        stops the rmr xapp completely.
        """
        super().stop()
        self.logger.debug("Stopping queue reading thread..")
        self._keep_going = False


class Xapp(_BaseXapp):
    """
    Represents an xapp where the client provides a generic function to call, which is mostly likely a loop-forever loop
    """

    def __init__(self, entrypoint, rmr_port=4562, rmr_wait_for_ready=True, use_fake_sdl=False):
        """
        Parameters
        ----------
        entrypoint: function
            this function is called when the xapp runs; this is the user code
            it's signature should be function(self)

        For the other parameters, see _BaseXapp
        """
        # init base
        super().__init__(rmr_port=rmr_port, rmr_wait_for_ready=rmr_wait_for_ready, use_fake_sdl=use_fake_sdl)
        self._entrypoint = entrypoint

    def run(self):
        """
        This function should be called when the client xapp is ready to start their code
        """
        self._entrypoint(self)

    # there is no need for stop currently here (base has, and nothing special to do here)
