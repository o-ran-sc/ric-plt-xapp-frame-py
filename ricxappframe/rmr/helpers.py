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
#   Abstract:   This is a colleciton of extensions to the RMR base package
#               which are likely to be convenient for python programmes.

from ricxappframe.rmr import rmr


def rmr_rcvall_msgs(mrc, pass_filter=[]):
    """
    Assemble an array of all messages which can be received without
    blocking.  Effectively draining the message queue if RMR is started
    in mt-call mode, or draining any waiting TCP buffers.  If the
    pass_filter parameter is supplied it is treated as one or more message
    types to accept (pass through). Using the default, an empty list, results
    in messages with any type being captured.

    Parameters
    ----------
        mrc: ctypes c_void_p
            Pointer to the RMR context

        pass_filter: list (optional)
            The message type(s) to capture.

    Returns
    -------
        list of dict
        List of message summaries, one for each message captured.
    """

    new_messages = []
    mbuf = rmr.rmr_alloc_msg(mrc, 4096)  # allocate buffer to have something for a return status

    while True:
        mbuf = rmr.rmr_torcv_msg(mrc, mbuf, 0)  # set the timeout to 0 so this doesn't block!!

        summary = rmr.message_summary(mbuf)
        if summary[rmr.RMR_MS_MSG_STATUS] != "RMR_OK":  # ok indicates msg received, stop on all other states
            break

        if len(pass_filter) == 0 or summary[rmr.RMR_MS_MSG_TYPE] in pass_filter:  # no filter, or passes; capture it
            new_messages.append(summary)

    rmr.rmr_free_msg(mbuf)  # must free message to avoid leak
    return new_messages


def rmr_rcvall_msgs_raw(mrc, pass_filter=[]):
    """
    Same as rmr_rcvall_msgs, but the raw sbuf is also returned.
    Useful, for example, if rts is to be used.

    Parameters
    ----------
        mrc: ctypes c_void_p
            Pointer to the RMR context

        pass_filter: list (optional)
            The message type(s) to capture.

    Returns
    -------
    list of tuple:$
       List of tuples [(S, sbuf),...] where S is a message summary and sbuf is the raw message$
       the caller is responsible for calling rmr.rmr_free_msg(sbuf) for each sbuf afterwards to prevent memory leaks.
    """

    new_messages = []

    while True:
        mbuf = rmr.rmr_alloc_msg(mrc, 4096)  # allocate buffer to have something for a return status
        mbuf = rmr.rmr_torcv_msg(mrc, mbuf, 0)  # set the timeout to 0 so this doesn't block!!
        summary = rmr.message_summary(mbuf)
        if summary[rmr.RMR_MS_MSG_STATUS] != "RMR_OK":
            break

        if len(pass_filter) == 0 or mbuf.contents.mtype in pass_filter:  # no filter, or passes; capture it
            new_messages.append((summary, mbuf))
        else:
            rmr.rmr_free_msg(mbuf)

    return new_messages
