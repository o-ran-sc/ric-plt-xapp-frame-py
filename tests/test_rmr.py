# vim: ts=4 sw=4 expandtab:
# =================================================================================2
#       Copyright (c) 2019-2020 Nokia
#       Copyright (c) 2018-2020 AT&T Intellectual Property.
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
import pytest
from ricxappframe.rmr import rmr, helpers, exceptions
from ricxappframe.rmrclib import rmrclib


SIZE = 256
MRC_SEND = None
MRC_RCV = None


def setup_module():
    """
    test_rmr module setup
    """
    global MRC_SEND
    MRC_SEND = rmr.rmr_init(b"3562", rmrclib.RMR_MAX_RCV_BYTES, 0x00)
    while rmr.rmr_ready(MRC_SEND) == 0:
        time.sleep(1)

    global MRC_RCV
    MRC_RCV = rmr.rmr_init(b"3563", rmrclib.RMR_MAX_RCV_BYTES, 0x00)
    while rmr.rmr_ready(MRC_RCV) == 0:
        time.sleep(1)

    global MRC_BUF_RCV
    MRC_BUF_RCV = rmr.rmr_init(b"3564", rmrclib.RMR_MAX_RCV_BYTES, 0x02)
    while rmr.rmr_ready(MRC_BUF_RCV) == 0:
        time.sleep(1)


def teardown_module():
    """
    test rmr module teardown
    """
    rmr.rmr_close(MRC_SEND)
    rmr.rmr_close(MRC_RCV)


def _assert_new_sbuf(sbuf):
    """
    verify the initial state of an alloced message is what we expect
    """
    summary = rmr.message_summary(sbuf)
    assert summary["payload"] == b""
    assert summary["payload length"] == 0
    assert summary["subscription id"] == -1
    assert summary["transaction id"] == b""
    assert summary["message state"] == 0
    assert summary["message status"] == "RMR_OK"
    assert summary["meid"] == b""
    assert summary["errno"] == 0


def test_meid():
    """
    test meid stringification
    """
    sbuf = rmr.rmr_alloc_msg(MRC_SEND, SIZE)

    rmr.rmr_set_meid(sbuf, b"\x01\x02")
    assert rmr.rmr_get_meid(sbuf) == rmr.message_summary(sbuf)["meid"] == b"\x01\x02"
    assert len(rmr.rmr_get_meid(sbuf)) == 2

    rmr.rmr_set_meid(sbuf, b"\x00" * 31)
    assert rmr.rmr_get_meid(sbuf) == rmr.message_summary(sbuf)["meid"] == b""  # NULL bytes get truncated

    rmr.rmr_set_meid(sbuf, b"6" * 31)
    assert rmr.rmr_get_meid(sbuf) == rmr.message_summary(sbuf)["meid"] == b"6" * 31  # string in string out

    rmr.rmr_set_meid(sbuf, b"\x01\x02")
    assert (
        rmr.rmr_get_meid(sbuf) == rmr.message_summary(sbuf)["meid"] == b"\x01\x02"
    )  # Ctypes will chop at first nil, so expect only 2 bytes back

    assert len(rmr.rmr_get_meid(sbuf)) == 2

    # test that an exception is raised for buffers which are too long
    with pytest.raises(exceptions.MeidSizeOutOfRange):
        rmr.rmr_set_meid(sbuf, b"8" * 32)


def test_rmr_set_get():
    """
    test set functions
    """
    sbuf = rmr.rmr_alloc_msg(MRC_SEND, SIZE)
    _assert_new_sbuf(sbuf)

    # test payload
    pay = b"\x01\x00\x80"
    rmr.set_payload_and_length(pay, sbuf)
    summary = rmr.message_summary(sbuf)
    assert summary["payload"] == pay
    assert summary["payload length"] == 3

    # test transid (note we cant test payload because it's randomly gen)
    assert summary["transaction id"] == b""
    assert len(summary["transaction id"]) == 0
    rmr.generate_and_set_transaction_id(sbuf)
    summary = rmr.message_summary(sbuf)
    assert summary["transaction id"] != b""
    assert len(summary["transaction id"]) == 32

    # test meid
    assert rmr.rmr_get_meid(sbuf) == summary["meid"] == b""
    rmr.rmr_set_meid(sbuf, b"666\x01\x00\x01")
    summary = rmr.message_summary(sbuf)
    assert rmr.rmr_get_meid(sbuf) == summary["meid"] == b"666\x01"
    assert (len(summary["meid"])) == 4


def test_alloc_fancy():
    """test allocation with setting payload, trans, mtype, subid"""
    pay = b"yoo\x01\x00\x80"
    sbuf = rmr.rmr_alloc_msg(MRC_SEND, SIZE, payload=pay, gen_transaction_id=True, mtype=14, meid=b"asdf", sub_id=654321)
    summary = rmr.message_summary(sbuf)
    assert summary["payload"] == pay
    assert summary["payload length"] == 6
    assert summary["transaction id"] != b""  # hard to test what it will be, but make sure not empty
    assert len(summary["transaction id"]) == 32
    assert summary["message state"] == 0
    assert summary["message type"] == sbuf.contents.mtype == 14
    assert rmr.rmr_get_meid(sbuf) == summary["meid"] == b"asdf"
    assert sbuf.contents.sub_id == summary["subscription id"] == 654321


def test_alloc_overlapping_flags():
    """test allocation with setting the transaction id"""
    sbuf = rmr.rmr_alloc_msg(MRC_SEND, SIZE, gen_transaction_id=True, fixed_transaction_id=b"6" * 32)
    summary = rmr.message_summary(sbuf)
    assert summary["transaction id"] == b"66666666666666666666666666666666"


def test_rcv_timeout():
    """
    test torcv; this is a scary test because if it fails... it doesn't fail, it will run forever!
    We receive a message (though nothing has been sent) and make sure the function doesn't block forever.

    There is no unit test for rmr_rcv_msg; too dangerous, that is a blocking call that may never return.
    """
    sbuf_rcv = rmr.rmr_alloc_msg(MRC_RCV, SIZE)
    sbuf_rcv = rmr.rmr_torcv_msg(MRC_RCV, sbuf_rcv, 50)  # should time out after 50ms
    summary = rmr.message_summary(sbuf_rcv)
    assert summary["message state"] == 12
    assert summary["message status"] == "RMR_ERR_TIMEOUT"


def test_send_rcv():
    """
    test send and receive
    """
    pay = b"\x01\x00\x80"

    # send a message
    sbuf_send = rmr.rmr_alloc_msg(MRC_SEND, SIZE)
    _assert_new_sbuf(sbuf_send)
    rmr.set_payload_and_length(pay, sbuf_send)
    sbuf_send.contents.mtype = 0
    sbuf_send = rmr.rmr_send_msg(MRC_SEND, sbuf_send)
    send_summary = rmr.message_summary(sbuf_send)
    assert send_summary["message state"] == 0  # if send fails don't attempt receive
    assert send_summary["message status"] == "RMR_OK"
    time.sleep(0.5)

    # receive it in other context
    sbuf_rcv = rmr.rmr_alloc_msg(MRC_RCV, SIZE)
    sbuf_rcv = rmr.rmr_torcv_msg(MRC_RCV, sbuf_rcv, 2000)
    rcv_summary = rmr.message_summary(sbuf_rcv)
    assert rcv_summary["message state"] == 0
    assert rcv_summary["message status"] == "RMR_OK"
    assert rcv_summary["message type"] == 0
    assert rcv_summary["payload"] == pay

    # send an ACK back
    ack_pay = b"message received"
    sbuf_rcv = rmr.rmr_rts_msg(MRC_RCV, sbuf_rcv, payload=ack_pay, mtype=6666)
    rcv_ack_summary = rmr.message_summary(sbuf_rcv)

    # have the sender receive it
    sbuf_send = rmr.rmr_torcv_msg(MRC_SEND, sbuf_send, 2000)
    send_ack_summary = rmr.message_summary(sbuf_send)

    assert send_ack_summary["message state"] == rcv_ack_summary["message state"] == 0
    assert send_ack_summary["message status"] == rcv_ack_summary["message status"] == "RMR_OK"
    assert send_ack_summary["payload"] == ack_pay
    assert send_ack_summary["message type"] == 6666


def test_send_rcv_subid_good():
    """
    test send and receive where subid is used for routing
    """
    pay = b"\x01\x00\x80"
    test_mtype = 46656
    test_subid = 777

    # send a message
    sbuf_send = rmr.rmr_alloc_msg(MRC_SEND, 3, pay, mtype=test_mtype, sub_id=test_subid)
    pre_send_summary = rmr.message_summary(sbuf_send)
    sbuf_send = rmr.rmr_send_msg(MRC_SEND, sbuf_send)
    send_summary = rmr.message_summary(sbuf_send)

    # receive it in other context
    time.sleep(0.5)
    sbuf_rcv = rmr.rmr_alloc_msg(MRC_RCV, 3)
    sbuf_rcv = rmr.rmr_torcv_msg(MRC_RCV, sbuf_rcv, 2000)
    rcv_summary = rmr.message_summary(sbuf_rcv)

    # asserts
    assert send_summary["message state"] == rcv_summary["message state"] == 0
    assert send_summary["message status"] == rcv_summary["message status"] == "RMR_OK"
    assert pre_send_summary["payload"] == rcv_summary["payload"] == pay
    assert pre_send_summary["message type"] == rcv_summary["message type"] == test_mtype
    assert pre_send_summary["subscription id"] == rcv_summary["subscription id"] == test_subid


def test_send_rcv_subid_bad_subid():
    """
    test send and receive where subid is used for routing but nobody recieves this subid
    """
    sbuf_send = rmr.rmr_alloc_msg(MRC_SEND, 3, b"\x01\x00\x80", mtype=46656, sub_id=778)
    sbuf_send = rmr.rmr_send_msg(MRC_SEND, sbuf_send)
    assert rmr.message_summary(sbuf_send)["message state"] == 2
    assert rmr.message_summary(sbuf_send)["message status"] == "RMR_ERR_NOENDPT"


def test_send_rcv_subid_bad_mtype():
    """
    test send and receive where subid is used for routing but nobody recieves this mtype
    """
    sbuf_send = rmr.rmr_alloc_msg(MRC_SEND, 3, b"\x01\x00\x80", mtype=46657, sub_id=777)
    sbuf_send = rmr.rmr_send_msg(MRC_SEND, sbuf_send)
    assert rmr.message_summary(sbuf_send)["message state"] == 2
    assert rmr.message_summary(sbuf_send)["message status"] == "RMR_ERR_NOENDPT"


def send_burst(mrc, fmt, mtype=1, num=13, counter=0):
    """
        Internal function to support test_rcv_all.
        Send a burst of messages optionally giving the type, payload
        and number to send.
    """
    sbuf_send = rmr.rmr_alloc_msg(MRC_SEND, SIZE)  # seed message buffer

    for i in range(num):
        payload = bytes(fmt % counter, "UTF-8")
        counter += 1

        rmr.set_payload_and_length(payload, sbuf_send)
        sbuf_send.contents.mtype = mtype

        max_retries = 5
        while max_retries > 0:
            sbuf_send = rmr.rmr_send_msg(mrc, sbuf_send)
            ms = rmr.message_summary(sbuf_send)
            if ms["message state"] != 10:  # 10 is retry
                break
            max_retries -= 1
            time.sleep(0.75)

        assert ms["message state"] == 0
        assert max_retries > 0


def test_rcv_all():
    """
    test the ability to receive a batch of queued messages.
    """
    pay_fmt = "send to ring msg: %d"  # dynamic message format with counter

    send_burst(MRC_SEND, pay_fmt)  # send a bunch of 13 messages that should queue
    time.sleep(1)  # ensure underlying transport gets cycles to send/receive

    bundle = helpers.rmr_rcvall_msgs(MRC_BUF_RCV)  # use the buffered receiver to read all with a single call
    assert len(bundle) == 13

    for i, ms in enumerate(bundle):
        ms = bundle[i]  # validate each summary returned, and ordering preserved
        assert ms["message state"] == 0
        expected_pay = bytes(pay_fmt % i, "UTF-8")
        assert ms["payload"] == expected_pay

    send_burst(MRC_SEND, pay_fmt, mtype=1, num=10)  # send a second round with msg types 1 and 2 to test filter
    send_burst(MRC_SEND, pay_fmt, mtype=2, num=8)
    send_burst(MRC_SEND, pay_fmt, mtype=1, num=5)
    send_burst(MRC_SEND, pay_fmt, mtype=2, num=4, counter=8)  # total of 12 messages with type 2 should be queued
    time.sleep(1)  # ensure underlying transport gets cycles to send/receive

    bundle = helpers.rmr_rcvall_msgs_raw(MRC_BUF_RCV, [2])  # receive only message type 2 messages
    assert len(bundle) == 12  # we should only get the second batch of 12 messages

    for i, (ms, sbuf) in enumerate(bundle):  # test the raw version
        test_summary = rmr.message_summary(sbuf)
        assert test_summary == ms
        assert ms["message state"] == 0  # all should be OK
        assert ms["message type"] == 2  # only mtype 2 should have been received
        expected_pay = bytes(pay_fmt % i, "UTF-8")  # ordering should still jive with the counter
        assert ms["payload"] == expected_pay
        rmr.rmr_free_msg(sbuf)


def test_bad_buffer():
    """test that we get a proper exception when the buffer has a null pointer"""
    with pytest.raises(exceptions.BadBufferAllocation):
        rmr.rmr_alloc_msg(None, 4096)


def test_resize_payload():
    """test the ability to insert a larger payload into an existing message"""
    mtype = 99
    subid = 100

    mbuf = rmr.rmr_alloc_msg(MRC_SEND, 25)  # allocate buffer with small payload
    mbuf.contents.mtype = mtype  # type and sub-id should not change
    mbuf.contents.sub_id = subid

    long_payload = b"This is a long payload that should force the message buffer to be reallocated"
    rmr.set_payload_and_length(long_payload, mbuf)
    summary = rmr.message_summary(mbuf)
    assert summary["payload max size"] >= len(long_payload)  # RMR may allocate a larger payload space
    assert summary["payload length"] == len(long_payload)  # however, the length must be exactly the same
    assert summary["message type"] == mtype  # both mtype and sub-id should be preserved in new
    assert summary["subscription id"] == subid
