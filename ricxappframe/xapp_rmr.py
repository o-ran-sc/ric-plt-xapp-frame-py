"""
Contains rmr functionality specific to the xapp
The general rmr API is via "rmr"
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


import time
import queue
from threading import Thread
from mdclogpy import Logger
from rmr import rmr, helpers


mdc_logger = Logger(name=__name__)


class RmrLoop:
    """
    Class represents an rmr loop that constantly reads from rmr

    Note, we use a queue here, and a thread, rather than the xapp frame just looping and calling consume, so that a possibly slow running consume function does not block the reading of new messages
    """

    def __init__(self, rmr_port):
        """
        sets up rmr, then launches a thread that reads and injects messages into a queue
        """

        # Public
        # thread safe queue https://docs.python.org/3/library/queue.html
        # IE in a bad scenario, consume_func could take a long time and the ring size for rmr blows up here and messages are lost
        self.rcv_queue = queue.Queue()

        # rmr context. This is
        # rmr.RMRFL_MTCALL puts RMR into a multithreaded mode, where a thread populates a ring of messages that eceive calls read from
        mdc_logger.debug("Waiting for rmr to init on port {}..".format(rmr_port))
        self.mrc = rmr.rmr_init(str(rmr_port).encode(), rmr.RMR_MAX_RCV_BYTES, rmr.RMRFL_MTCALL)
        while rmr.rmr_ready(self.mrc) == 0:
            time.sleep(0.1)

        # Private
        self._last_ran = time.time()

        # start the work loop
        mdc_logger.debug("Starting loop thread")
        self._thread = Thread(target=self.loop)
        self._thread.start()

    def loop(self):
        """
        loop forever
        """
        mdc_logger.debug("Work loop starting")
        while True:

            # read our mailbox
            # TODO: take a flag as to whether RAW is needed or not
            # RAW allows for RTS however the caller must free, and the caller may not need RTS.
            # Currently after consuming, callers should do  rmr.rmr_free_msg(sbuf)

            for (msg, sbuf) in helpers.rmr_rcvall_msgs_raw(self.mrc):
                self.rcv_queue.put((msg, sbuf))

            self._last_ran = time.time()

            # TODO: should we sleep? A1 sleeps 1s here.

    def healthcheck(self, seconds=30):
        """
        returns a boolean representing whether the rmr loop is healthy, by checking two attributes:
        1. is it running?,
        2. is it stuck in a long (> seconds) loop?
        """
        return self._thread.is_alive() and ((time.time() - self._last_ran) < seconds)
