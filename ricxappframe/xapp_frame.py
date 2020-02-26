"""
Framework for python xapps
Framework here means Xapp classes that can be subclassed
"""
import xapp_rmr
from rmr import rmr
from mdclogpy import Logger
from xapp_sdl import SDLWrapper


mdc_logger = Logger(name=__name__)


# Private base class; not for direct client use


class _BaseXapp:
    """
    Base xapp; not for client use directly
    """

    def __init__(self, rmr_port=4562, use_fake_sdl=False):
        """
        Init
        """

        # Start rmr rcv thread
        self._rmr_loop = xapp_rmr.RmrLoop(rmr_port)
        self._mrc = self._rmr_loop.mrc  # for convenience

        # SDL
        self._sdl = SDLWrapper(use_fake_sdl)

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


# Public Classes to subclass (these subclass _BaseXapp)


class RMRXapp(_BaseXapp):
    """
    Represents an xapp that is purely driven by rmr messages (i.e., when messages are received, the xapp does something
    When run is called, the xapp framework waits for rmr messages, and calls the client provided consume callback on every one
    """

    def consume(self, summary, sbuf):
        """
        This function is to be implemented by the client and is called whenever a new rmr message is received.
        It is expected to take two parameters (besides self):

        Parameters
        ----------
        summary: dict
            the rmr message summary
        sbuf: ctypes c_void_p
            Pointer to an rmr message buffer. The user must call free on this when done.
        """
        raise NotImplementedError()

    def run(self):
        """
        This function should be called when the client xapp is ready to wait for consume to be called on received messages
        """
        while True:
            if not self._rmr_loop.rcv_queue.empty():
                (summary, sbuf) = self._rmr_loop.rcv_queue.get()
                self.consume(summary, sbuf)


class Xapp(_BaseXapp):
    """
    Represents an xapp where the client provides a generic function to call, which is mostly likely a loop-forever loop
    """

    def loop(self):
        """
        This function is to be implemented by the client and is called
        """
        raise NotImplementedError()

    def run(self):
        """
        This function should be called when the client xapp is ready to start their loop
        This is simple and the client could just call self.loop(), however this gives a consistent interface as the other xapps
        """
        self.loop()
