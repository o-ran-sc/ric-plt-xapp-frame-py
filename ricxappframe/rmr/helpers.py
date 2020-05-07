# ==================================================================================
#       Copyright (c) 2019 Nokia
#       Copyright (c) 2018-2019 AT&T Intellectual Property.
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

#   Mnemonic:   helpers.py
#   Abstract:   This is a collection of extensions to the RMR base package
#               which are likely to be convenient for Python programs.

from ricxappframe.rmr import rmr


def rmr_rcvall_msgs(mrc, pass_filter=None, timeout=0):
    """
    Assembles an array of all messages which can be received without blocking
    (but see the timeout parameter).  Effectively drains the message queue if
    RMR is started in mt-call mode, or draining any waiting TCP buffers.  If
    the pass_filter parameter is supplied, it is treated as one or more
    message types to accept (pass through). Using the default, an empty list,
    results in capturing all messages. If the timeout parameter is supplied
    and is not zero, this call may block up to that number of milliseconds
    waiting for a message to arrive. Using the default, zero, results in
    non-blocking no-wait behavior.

    Parameters
    ----------
        mrc: ctypes c_void_p
            Pointer to the RMR context

        pass_filter: list (optional)
            The message type(s) to capture.

        timeout: int (optional)
            The number of milliseconds to wait for a message to arrive.

    Returns
    -------
        List of message summaries (dict), one for each message received; may be empty.
    """

    new_messages = []
    mbuf = rmr.rmr_alloc_msg(mrc, 4096)  # allocate and reuse a single buffer for RMR

    while True:
        mbuf = rmr.rmr_torcv_msg(mrc, mbuf, timeout)  # first call may have non-zero timeout
        timeout = 0  # reset so subsequent calls do not wait
        summary = rmr.message_summary(mbuf)
        if summary[rmr.RMR_MS_MSG_STATUS] != "RMR_OK":  # ok indicates msg received, stop on all other states
            break

        if pass_filter is None or len(pass_filter) == 0 or summary[rmr.RMR_MS_MSG_TYPE] in pass_filter:  # no filter, or passes; capture it
            new_messages.append(summary)

    rmr.rmr_free_msg(mbuf)  # free the single buffer to avoid leak
    return new_messages


def rmr_rcvall_msgs_raw(mrc, pass_filter=None, timeout=0):
    """
    Same as rmr_rcvall_msgs, but answers tuples with the raw sbuf.
    Useful if return-to-sender (rts) functions are required.

    Parameters
    ----------
        mrc: ctypes c_void_p
            Pointer to the RMR context

        pass_filter: list (optional)
            The message type(s) to capture.

        timeout: int (optional)
            The number of milliseconds to wait for a message to arrive.

    Returns
    -------
    list of tuple:
        List of tuples [(S, sbuf),...] where S is a message summary (dict), and sbuf is the raw message; may be empty.
        The caller MUST call rmr.rmr_free_msg(sbuf) when finished with each sbuf to prevent memory leaks!
    """

    new_messages = []

    while True:
        mbuf = rmr.rmr_alloc_msg(mrc, 4096)  # allocate a new buffer for every message
        mbuf = rmr.rmr_torcv_msg(mrc, mbuf, timeout)  # first call may have non-zero timeout
        timeout = 0  # reset so subsequent calls do not wait
        summary = rmr.message_summary(mbuf)
        if summary[rmr.RMR_MS_MSG_STATUS] != "RMR_OK":
            rmr.rmr_free_msg(mbuf)  # free the failed-to-receive buffer
            break

        if pass_filter is None or len(pass_filter) == 0 or mbuf.contents.mtype in pass_filter:  # no filter, or passes; capture it
            new_messages.append((summary, mbuf))  # caller is responsible for freeing the buffer
        else:
            rmr.rmr_free_msg(mbuf)  # free the filtered-out message buffer

    return new_messages
