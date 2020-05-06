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
from ricxappframe.rmr import rmr
from ricxappframe.rmr.rmr_mocks import rmr_mocks


MRC = None
SIZE = 256


def _partial_dict_comparison(subset_dict, target_dict):
    """
    Compares that target_dict[k] == subset_dict[k] for all k <- subset_dict
    """
    for k, v in subset_dict.items():
        assert k in target_dict
        assert target_dict[k] == subset_dict[k]


def test_send_mock(monkeypatch):
    """
    tests the send mock
    """
    monkeypatch.setattr("ricxappframe.rmr.rmr.rmr_send_msg", rmr_mocks.send_mock_generator(12))
    rmr_mocks.patch_rmr(monkeypatch)
    sbuf = rmr.rmr_alloc_msg(MRC, SIZE)
    rmr.set_payload_and_length("testttt".encode("utf8"), sbuf)

    expected = {
        rmr.RMR_MS_MEID: None,
        rmr.RMR_MS_MSG_SOURCE: "localtest:80",
        rmr.RMR_MS_MSG_STATE: 0,
        rmr.RMR_MS_MSG_TYPE: 0,
        rmr.RMR_MS_MSG_STATUS: "RMR_OK",
        rmr.RMR_MS_PAYLOAD: b"testttt",
        rmr.RMR_MS_PAYLOAD_LEN: 7,
        rmr.RMR_MS_PAYLOAD_MAX: 4096,
        rmr.RMR_MS_SUB_ID: 0,
    }
    _partial_dict_comparison(expected, rmr.message_summary(sbuf))

    # set the mtype
    sbuf.contents.mtype = 666

    # send it (the fake send sets the state, and touches nothing else)
    sbuf = rmr.rmr_send_msg(MRC, sbuf)

    expected = {
        rmr.RMR_MS_MEID: None,
        rmr.RMR_MS_MSG_SOURCE: "localtest:80",
        rmr.RMR_MS_MSG_STATE: 12,
        rmr.RMR_MS_MSG_TYPE: 666,
        rmr.RMR_MS_MSG_STATUS: "RMR_ERR_TIMEOUT",
        rmr.RMR_MS_PAYLOAD: None,
        rmr.RMR_MS_PAYLOAD_LEN: 7,
        rmr.RMR_MS_PAYLOAD_MAX: 4096,
        rmr.RMR_MS_SUB_ID: 0,
    }
    _partial_dict_comparison(expected, rmr.message_summary(sbuf))


def test_rcv_mock(monkeypatch):
    """
    tests the rmr recieve mocking generator
    """
    rmr_mocks.patch_rmr(monkeypatch)
    sbuf = rmr.rmr_alloc_msg(MRC, SIZE)

    # test rcv
    monkeypatch.setattr("ricxappframe.rmr.rmr.rmr_rcv_msg", rmr_mocks.rcv_mock_generator({"foo": "bar"}, 666, 0, True))
    sbuf = rmr.rmr_rcv_msg(MRC, sbuf)
    assert rmr.get_payload(sbuf) == b'{"foo": "bar"}'
    assert sbuf.contents.mtype == 666
    assert sbuf.contents.state == 0
    assert sbuf.contents.len == 14

    # test torcv, although the timeout portion is not currently mocked or tested
    monkeypatch.setattr("ricxappframe.rmr.rmr.rmr_torcv_msg", rmr_mocks.rcv_mock_generator({"foo": "bar"}, 666, 0, True, 50))
    sbuf = rmr.rmr_torcv_msg(MRC, sbuf, 5)
    assert rmr.get_payload(sbuf) == b'{"foo": "bar"}'
    assert sbuf.contents.mtype == 666
    assert sbuf.contents.state == 0
    assert sbuf.contents.len == 14


def test_alloc(monkeypatch):
    """
    test alloc with all fields set
    """
    rmr_mocks.patch_rmr(monkeypatch)
    sbuf = rmr.rmr_alloc_msg(
        MRC, SIZE, payload=b"foo", gen_transaction_id=True, mtype=5, meid=b"mee", sub_id=234, fixed_transaction_id=b"t" * 32
    )
    summary = rmr.message_summary(sbuf)
    assert summary[rmr.RMR_MS_PAYLOAD] == b"foo"
    assert summary[rmr.RMR_MS_TRN_ID] == b"t" * 32
    assert summary[rmr.RMR_MS_MSG_TYPE] == 5
    assert summary[rmr.RMR_MS_MEID] == b"mee"
    assert summary[rmr.RMR_MS_SUB_ID] == 234
