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

    def __init__(self, port, wait_for_ready=True):
        """
        sets up rmr, then launches a thread that reads and injects messages into a queue

        Parameters
        ----------
        port: int
            port to listen on

        wait_for_ready: bool (optional)
            if this is True, then this function hangs until rmr is ready to send, which includes having a valid routing file.
            this can be set to False if the client only wants to *receive only*
        """

        # Public
        # thread safe queue https://docs.python.org/3/library/queue.html
        # We use a thread and a queue so that a long running consume callback function can never block reads.
        # IE a consume implementation could take a long time and the ring size for rmr blows up here and messages are lost
        self.rcv_queue = queue.Queue()

        # rmr context; RMRFL_MTCALL puts RMR into a multithreaded mode, where a thread populates a ring of messages that receive calls read from
        self.mrc = rmr.rmr_init(str(port).encode(), rmr.RMR_MAX_RCV_BYTES, rmr.RMRFL_MTCALL)

        if wait_for_ready:
            mdc_logger.debug("Waiting for rmr to init on port {}..".format(port))
            while rmr.rmr_ready(self.mrc) == 0:
                time.sleep(0.1)

        # Private
        self._keep_going = True  # used to tell this thread to stop it's work
        self._last_ran = time.time()  # used for healthcheck
        self._loop_is_running = False  # used in stop to know when it's safe to kill the mrc

        # start the work loop
        mdc_logger.debug("Starting loop thread")

        def loop():
            mdc_logger.debug("Work loop starting")
            self._loop_is_running = True
            while self._keep_going:

                # read our mailbox
                # TODO: take a flag as to whether RAW is needed or not
                # RAW allows for RTS however the caller must free, and the caller may not need RTS.
                # Currently after consuming, callers should do  rmr.rmr_free_msg(sbuf)

                for (msg, sbuf) in helpers.rmr_rcvall_msgs_raw(self.mrc):
                    self.rcv_queue.put((msg, sbuf))

                self._last_ran = time.time()

            self._loop_is_running = False

        self._thread = Thread(target=loop)
        self._thread.start()

    def stop(self):
        """
        sets a flag that will cleanly stop the thread
        """
        mdc_logger.debug("Stopping rmr thread. Waiting for last iteration to finish..")
        self._keep_going = False
        # wait until the current batch of messages is done, then kill the rmr connection
        # note; I debated putting this in "loop" however if the while loop was still going setting mrc to close here would blow up any processing still currently happening
        # probably more polite to at least finish the current batch and then close. So here we wait until the current batch is done, then we kill the mrc
        while self._loop_is_running:
            pass
        mdc_logger.debug("Closing rmr connection")
        rmr.rmr_close(self.mrc)

    def healthcheck(self, seconds=30):
        """
        returns a boolean representing whether the rmr loop is healthy, by checking two attributes:
        1. is it running?,
        2. is it stuck in a long (> seconds) loop?

        Parameters
        ----------
        seconds: int (optional)
            the rmr loop is determined healthy if it has completed in the last (seconds)
        """
        return self._thread.is_alive() and ((time.time() - self._last_ran) < seconds)
