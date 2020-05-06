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

"""
Provides mocks that are useful for end applications unit testing
"""

import json
import uuid
from ricxappframe.rmr import rmr


def rcv_mock_generator(msg_payload, msg_type, msg_state, jsonb, timeout=0):
    """
    generates a mock function that can be used to monkeypatch rmr_torcv_msg or rmr_rcv_msg
    """

    def f(_mrc, sbuf, _timeout=timeout):  # last param is needed for calls to rmr_torcv_msg, but not in rmr_rcv_msg
        sbuf.contents.mtype = msg_type
        payload = json.dumps(msg_payload).encode("utf-8") if jsonb else msg_payload
        sbuf.contents.payload = payload
        sbuf.contents.len = len(payload)
        sbuf.contents.state = msg_state
        if msg_state != 0:  # set something in transport state if 'error'
            sbuf.contents.tp_state = 99
        else:
            sbuf.contents.tp_state = 0
        return sbuf

    return f


def send_mock_generator(msg_state):
    """
    generates a mock function that can be used to monkeypatch rmr_send_msg
    usage example:
        monkeypatch.setattr('ricxappframe.rmr.rmr.rmr_send_msg', rmr_mocks.send_mock_generator(0))
    """

    def f(_unused, sbuf):
        sbuf.contents.state = msg_state
        if msg_state != 0:  # set something in transport state if 'error'
            sbuf.contents.tp_state = 99
        else:
            sbuf.contents.tp_state = 0
        return sbuf

    return f


class _Sbuf_Contents:
    """fake version of how pointers work (ctype pointer access is done by accessing a magical attribute called "contents"""

    def __init__(self):
        self.state = 0
        self.mtype = 0
        self.len = 0
        self.payload = ""
        self.xaction = uuid.uuid1().hex.encode("utf-8")
        self.sub_id = 0
        self.tp_state = 0
        self.meid = None

    def __str__(self):
        return str(
            {
                rmr.RMR_MS_MSG_STATE: self.state,
                rmr.RMR_MS_MSG_TYPE: self.mtype,
                rmr.RMR_MS_PAYLOAD_LEN: self.len,
                rmr.RMR_MS_PAYLOAD: self.payload,
                rmr.RMR_MS_TRN_ID: self.xaction,
                rmr.RMR_MS_SUB_ID: self.sub_id,
                rmr.RMR_MS_ERRNO: self.tp_state,
                rmr.RMR_MS_MEID: self.meid,
            }
        )


class Rmr_mbuf_t:
    """fake version of rmr.rmr_mbuf_t"""

    def __init__(self):
        self.contents = _Sbuf_Contents()


def patch_rmr(monkeypatch):
    """
    Patch rmr; requires a monkeypatch (pytest) object to be passed in
    """

    def fake_alloc(
        _vctx, _sz, payload=None, gen_transaction_id=False, mtype=None, meid=None, sub_id=None, fixed_transaction_id=None
    ):
        sbuf = Rmr_mbuf_t()
        if payload:
            sbuf.contents.payload = payload

        if fixed_transaction_id:
            sbuf.contents.xaction = fixed_transaction_id
        elif gen_transaction_id:
            sbuf.contents.xaction = uuid.uuid1().hex.encode("utf-8")

        if mtype:
            sbuf.contents.mtype = mtype

        if meid:
            sbuf.contents.meid = meid

        if sub_id:
            sbuf.contents.sub_id = sub_id

        return sbuf

    def fake_set_payload_and_length(payload, sbuf):
        sbuf.contents.payload = payload
        sbuf.contents.len = len(payload)

    def fake_generate_and_set_transaction_id(sbuf):
        sbuf.contents.xaction = uuid.uuid1().hex.encode("utf-8")

    def fake_get_payload(sbuf):
        return sbuf.contents.payload

    def fake_get_meid(sbuf):
        return sbuf.contents.meid

    def fake_get_src(_sbuf):
        return "localtest:80"  # this is not a part of rmr_mbuf_t

    def fake_rmr_payload_size(_sbuf):
        return 4096

    def fake_free(_sbuf):
        pass

    monkeypatch.setattr("ricxappframe.rmr.rmr.rmr_free_msg", fake_free)
    monkeypatch.setattr("ricxappframe.rmr.rmr.rmr_alloc_msg", fake_alloc)
    monkeypatch.setattr("ricxappframe.rmr.rmr.set_payload_and_length", fake_set_payload_and_length)
    monkeypatch.setattr("ricxappframe.rmr.rmr.generate_and_set_transaction_id", fake_generate_and_set_transaction_id)
    monkeypatch.setattr("ricxappframe.rmr.rmr.get_payload", fake_get_payload)
    monkeypatch.setattr("ricxappframe.rmr.rmr.get_src", fake_get_src)
    monkeypatch.setattr("ricxappframe.rmr.rmr.rmr_get_meid", fake_get_meid)
    monkeypatch.setattr("ricxappframe.rmr.rmr.rmr_payload_size", fake_rmr_payload_size)
