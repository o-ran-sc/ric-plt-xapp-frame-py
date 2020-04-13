# ==================================================================================
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
import uuid
from ctypes import POINTER, Structure
from ctypes import c_int, c_char, c_char_p, c_void_p, memmove, cast, create_string_buffer

from ricxappframe.rmr.exceptions import BadBufferAllocation, MeidSizeOutOfRange, InitFailed
from ricxappframe.rmr.rmrclib.rmrclib import rmr_c_lib, get_constants, state_to_status

##############
# PRIVATE API
##############


def _get_rmr_constant(key: str, default=None):
    """
    Gets the constant with the named key from the RMR C library.
    Returns None if the value is not a simple type. This happens
    during sphinx autodoc document generation, which mocks the
    rmrclib package to work without the RMR shared object file,
    and the response is something like this:
    <class 'ricxappframe.rmr.rmrclib.rmrclib.get_constants.get'>
    Workaround for https://github.com/sphinx-doc/sphinx/issues/7422
    """
    val = get_constants().get(key, default)
    return val if isinstance(val, (type(None), bool, bytes, float, int, str)) else None


# argtypes and restype are important:
# https://stackoverflow.com/questions/24377845/ctype-why-specify-argtypes
def _wrap_rmr_function(funcname, restype, argtypes):
    """
    Simplify wrapping ctypes functions.

    Parameters
    ----------
    funcname: str
        Name of library method
    restype: class
        Name of ctypes class; e.g., c_char_p
    argtypes: list
        List of ctypes classes; e.g., [ c_char_p, int ]

    Returns
    -------
    _FuncPointer:
        Pointer to C library function
"""
    func = rmr_c_lib.__getattr__(funcname)
    func.restype = restype
    func.argtypes = argtypes
    return func


##############
# PUBLIC API
##############

# Publish constants from RMR C-language header files for use by importers of this library.
# TODO: Are there others that will be useful?
#: Typical size message to receive; size is not limited
RMR_MAX_RCV_BYTES = _get_rmr_constant('RMR_MAX_RCV_BYTES')
#: Multi-threaded initialization flag
RMRFL_MTCALL = _get_rmr_constant('RMRFL_MTCALL', 0x02)  # initialization flags
#: Empty flag
RMRFL_NONE = _get_rmr_constant('RMRFL_NONE', 0x0)
#: State constant for OK
RMR_OK = _get_rmr_constant('RMR_OK', 0x00)
#: State constant for timeout
RMR_ERR_TIMEOUT = _get_rmr_constant('RMR_ERR_TIMEOUT')
#: State constant for retry
RMR_ERR_RETRY = _get_rmr_constant('RMR_ERR_RETRY')


class rmr_mbuf_t(Structure):
    """
    Mirrors public members of type rmr_mbuf_t from RMR header file src/common/include/rmr.h

    | typedef struct {
    |    int     state;          // state of processing
    |    int     mtype;          // message type
    |    int     len;            // length of data in the payload (send or received)
    |    unsigned char* payload; // transported data
    |    unsigned char* xaction; // pointer to fixed length transaction id bytes
    |    int sub_id;             // subscription id
    |    int      tp_state;      // transport state (a.k.a errno)
    |
    | these things are off limits to the user application
    |
    |    void*   tp_buf;         // underlying transport allocated pointer (e.g. nng message)
    |    void*   header;         // internal message header (whole buffer: header+payload)
    |    unsigned char* id;      // if we need an ID in the message separate from the xaction id
    |    int flags;              // various MFL (private) flags as needed
    |    int alloc_len;          // the length of the allocated space (hdr+payload)
    | } rmr_mbuf_t;

    RE PAYLOADs type below, see the documentation for c_char_p:
       class ctypes.c_char_p
            Represents the C char * datatype when it points to a zero-terminated string.
            For a general character pointer that may also point to binary data, POINTER(c_char)
            must be used. The constructor accepts an integer address, or a bytes object.
    """

    _fields_ = [
        ("state", c_int),
        ("mtype", c_int),
        ("len", c_int),
        ("payload", POINTER(c_char)),  # according to the following the python bytes are already unsigned
                                       # https://bytes.com/topic/python/answers/695078-ctypes-unsigned-char
        ("xaction", POINTER(c_char)),
        ("sub_id", c_int),
        ("tp_state", c_int),
    ]


_rmr_init = _wrap_rmr_function('rmr_init', c_void_p, [c_char_p, c_int, c_int])


def rmr_init(uproto_port: c_char_p, max_msg_size: int, flags: int) -> c_void_p:
    """
    Prepares the environment for sending and receiving messages.
    Refer to RMR C documentation for method::

        extern void* rmr_init(char* uproto_port, int max_msg_size, int flags)

    This function raises an exception if the returned context is None.

    Parameters
    ----------
    uproto_port: c_char_p
        Pointer to bytes built from the port number as a string; e.g., b'4550'
    max_msg_size: integer
        Maximum message size to receive
    flags: integer
        RMR option flags

    Returns
    -------
    c_void_p:
        Pointer to RMR context
    """
    mrc = _rmr_init(uproto_port, max_msg_size, flags)
    if mrc is None:
        raise InitFailed()
    return mrc


_rmr_ready = _wrap_rmr_function('rmr_ready', c_int, [c_void_p])


def rmr_ready(vctx: c_void_p) -> int:
    """
    Checks if a routing table has been received and installed.
    Refer to RMR C documentation for method::

        extern int rmr_ready(void* vctx)

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context

    Returns
    -------
    1 for yes, 0 for no
    """
    return _rmr_ready(vctx)


_rmr_close = _wrap_rmr_function('rmr_close', None, [c_void_p])


def rmr_close(vctx: c_void_p):
    """
    Closes the listen socket.
    Refer to RMR C documentation for method::

        extern void rmr_close(void* vctx)

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context

    Returns
    -------
    None
    """
    _rmr_close(vctx)


_rmr_set_stimeout = _wrap_rmr_function('rmr_set_stimeout', c_int, [c_void_p, c_int])


def rmr_set_stimeout(vctx: c_void_p, rloops: int) -> int:
    """
    Sets the configuration for how RMR will retry message send operations.
    Refer to RMR C documentation for method::

        extern int rmr_set_stimeout(void* vctx, int rloops)

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context
    rloops: int
        Number of retry loops

    Returns
    -------
    0 on success, -1 on failure
    """
    return _rmr_set_stimeout(vctx, rloops)


_rmr_alloc_msg = _wrap_rmr_function('rmr_alloc_msg', POINTER(rmr_mbuf_t), [c_void_p, c_int])


def rmr_alloc_msg(vctx: c_void_p, size: int,
                  payload=None, gen_transaction_id=False, mtype=None,
                  meid=None, sub_id=None, fixed_transaction_id=None):
    """
    Allocates and returns a buffer to write and send through the RMR library.
    Refer to RMR C documentation for method::

        extern rmr_mbuf_t* rmr_alloc_msg(void* vctx, int size)

    Optionally populates the message from the remaining arguments.

    TODO: on next API break, clean up transaction_id ugliness. Kept for now to preserve API.

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context
    size: int
        How much space to allocate
    payload: bytes
        if not None, attempts to set the payload
    gen_transaction_id: bool
        if True, generates and sets a transaction ID.
        Note, option fixed_transaction_id overrides this option
    mtype: bytes
        if not None, sets the sbuf's message type
    meid: bytes
        if not None, sets the sbuf's meid
    sub_id: bytes
        if not None, sets the sbuf's subscription id
    fixed_transaction_id: bytes
        if not None, used as the transaction ID.
        Note, this overrides the option gen_transaction_id

    Returns
    -------
    c_void_p:
        Pointer to rmr_mbuf structure
    """
    sbuf = _rmr_alloc_msg(vctx, size)
    try:
        # make sure the alloc worked
        sbuf.contents

        # set specified fields
        if payload:
            set_payload_and_length(payload, sbuf)

        if fixed_transaction_id:
            set_transaction_id(sbuf, fixed_transaction_id)
        elif gen_transaction_id:
            generate_and_set_transaction_id(sbuf)

        if mtype:
            sbuf.contents.mtype = mtype

        if meid:
            rmr_set_meid(sbuf, meid)

        if sub_id:
            sbuf.contents.sub_id = sub_id

        return sbuf

    except ValueError:
        raise BadBufferAllocation


_rmr_realloc_payload = _wrap_rmr_function('rmr_realloc_payload', POINTER(rmr_mbuf_t), [POINTER(rmr_mbuf_t), c_int, c_int, c_int])  # new_len, copy, clone


def rmr_realloc_payload(ptr_mbuf: c_void_p, new_len: int, copy=False, clone=False):
    """
    Allocates and returns a message buffer large enough for the new length.
    Refer to RMR C documentation for method::

        extern rmr_mbuf_t* rmr_realloc_payload(rmr_mbuf_t*, int, int, int)

    Parameters
    ----------
    ptr_mbuf: c_void_p
        Pointer to rmr_mbuf structure
    new_len: int
        Length
    copy: bool
        Whether to copy the original paylod
    clone: bool
        Whether to clone the original buffer

    Returns
    -------
    c_void_p:
        Pointer to rmr_mbuf structure
    """
    return _rmr_realloc_payload(ptr_mbuf, new_len, copy, clone)


_rmr_free_msg = _wrap_rmr_function('rmr_free_msg', None, [POINTER(rmr_mbuf_t)])


def rmr_free_msg(ptr_mbuf: c_void_p):
    """
    Releases the message buffer.
    Refer to RMR C documentation for method::

        extern void rmr_free_msg(rmr_mbuf_t* mbuf )

    Parameters
    ----------
    ptr_mbuf: c_void_p
        Pointer to rmr_mbuf structure

    Returns
    -------
    None
    """
    if ptr_mbuf is not None:
        _rmr_free_msg(ptr_mbuf)


_rmr_payload_size = _wrap_rmr_function('rmr_payload_size', c_int, [POINTER(rmr_mbuf_t)])


def rmr_payload_size(ptr_mbuf: c_void_p) -> int:
    """
    Gets the number of bytes available in the payload.
    Refer to RMR C documentation for method::

        extern int rmr_payload_size(rmr_mbuf_t* msg)

    Parameters
    ----------
    ptr_mbuf: c_void_p
        Pointer to rmr_mbuf structure

    Returns
    -------
    int:
        Number of bytes available
    """
    return _rmr_payload_size(ptr_mbuf)


"""
The following functions all seem to have the same interface
"""

_rmr_send_msg = _wrap_rmr_function('rmr_send_msg', POINTER(rmr_mbuf_t), [c_void_p, POINTER(rmr_mbuf_t)])


def rmr_send_msg(vctx: c_void_p, ptr_mbuf: POINTER(rmr_mbuf_t)) -> POINTER(rmr_mbuf_t):
    """
    Sends the message according to the routing table and returns an empty buffer.
    Refer to RMR C documentation for method::

        extern rmr_mbuf_t* rmr_send_msg(void* vctx, rmr_mbuf_t* msg)

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context
    ptr_mbuf: c_void_p
        Pointer to rmr_mbuf structure

    Returns
    -------
    c_void_p:
        Pointer to rmr_mbuf structure
    """
    return _rmr_send_msg(vctx, ptr_mbuf)


# TODO: the old message (Send param) is actually optional, but I don't know how to specify that in Ctypes.
_rmr_rcv_msg = _wrap_rmr_function('rmr_rcv_msg', POINTER(rmr_mbuf_t), [c_void_p, POINTER(rmr_mbuf_t)])


def rmr_rcv_msg(vctx: c_void_p, ptr_mbuf: POINTER(rmr_mbuf_t)) -> POINTER(rmr_mbuf_t):
    """
    Waits for a message to arrive, and returns it.
    Refer to RMR C documentation for method::

        extern rmr_mbuf_t* rmr_rcv_msg(void* vctx, rmr_mbuf_t* old_msg)

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context
    ptr_mbuf: c_void_p
        Pointer to rmr_mbuf structure

    Returns
    -------
    c_void_p:
        Pointer to rmr_mbuf structure
    """
    return _rmr_rcv_msg(vctx, ptr_mbuf)


_rmr_torcv_msg = _wrap_rmr_function('rmr_torcv_msg', POINTER(rmr_mbuf_t), [c_void_p, POINTER(rmr_mbuf_t), c_int])


def rmr_torcv_msg(vctx: c_void_p, ptr_mbuf: POINTER(rmr_mbuf_t), ms_to: int) -> POINTER(rmr_mbuf_t):
    """
    Waits up to the timeout value for a message to arrive, and returns it.
    Refer to RMR C documentation for method::

        extern rmr_mbuf_t* rmr_torcv_msg(void* vctx, rmr_mbuf_t* old_msg, int ms_to)

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context
    ptr_mbuf: c_void_p
        Pointer to rmr_mbuf structure
    ms_to: int
        Time out value in milliseconds

    Returns
    -------
    c_void_p:
        Pointer to rmr_mbuf structure
    """
    return _rmr_torcv_msg(vctx, ptr_mbuf, ms_to)


_rmr_rts_msg = _wrap_rmr_function('rmr_rts_msg', POINTER(rmr_mbuf_t), [c_void_p, POINTER(rmr_mbuf_t)])


def rmr_rts_msg(vctx: c_void_p, ptr_mbuf: POINTER(rmr_mbuf_t), payload=None, mtype=None) -> POINTER(rmr_mbuf_t):
    """
    Sends a message to the originating endpoint and returns an empty buffer.
    Refer to RMR C documentation for method::

        extern rmr_mbuf_t* rmr_rts_msg(void* vctx, rmr_mbuf_t* msg)

    additional features beyond c-rmr:
        if payload is not None, attempts to set the payload
        if mtype is not None, sets the sbuf's message type

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to an RMR context
    ptr_mbuf: ctypes c_void_p
        Pointer to an RMR message buffer
    payload: bytes
        Payload
    mtype: bytes
        Message type

    Returns
    -------
    c_void_p:
        Pointer to rmr_mbuf structure
    """

    if payload:
        set_payload_and_length(payload, ptr_mbuf)

    if mtype:
        ptr_mbuf.contents.mtype = mtype

    return _rmr_rts_msg(vctx, ptr_mbuf)


_rmr_call = _wrap_rmr_function('rmr_call', POINTER(rmr_mbuf_t), [c_void_p, POINTER(rmr_mbuf_t)])


def rmr_call(vctx: c_void_p, ptr_mbuf: POINTER(rmr_mbuf_t)) -> POINTER(rmr_mbuf_t):
    """
    Sends a message, waits for a response and returns it.
    Refer to RMR C documentation for method::

        extern rmr_mbuf_t* rmr_call(void* vctx, rmr_mbuf_t* msg)

    Parameters
    ----------
    ptr_mbuf: ctypes c_void_p
        Pointer to an RMR message buffer

    Returns
    -------
    c_void_p:
        Pointer to rmr_mbuf structure
    """
    return _rmr_call(vctx, ptr_mbuf)


_rmr_bytes2meid = _wrap_rmr_function('rmr_bytes2meid', c_int, [POINTER(rmr_mbuf_t), c_char_p, c_int])


def rmr_set_meid(ptr_mbuf: POINTER(rmr_mbuf_t), byte_str: bytes) -> int:
    """
    Sets the managed entity field in the message and returns the number of bytes copied.
    Refer to RMR C documentation for method::

        extern int rmr_bytes2meid(rmr_mbuf_t* mbuf, unsigned char const* src, int len);

    Caution:  the meid length supported in an RMR message is 32 bytes, but C applications
    expect this to be a nil terminated string and thus only 31 bytes are actually available.

    Raises: exceptions.MeidSizeOutOfRang

    Parameters
    ----------
    ptr_mbuf: ctypes c_void_p
        Pointer to an RMR message buffer
    byte_tr: bytes
        Managed entity ID value

    Returns
    -------
    int:
        number of bytes copied
    """
    max = _get_rmr_constant("RMR_MAX_MEID", 32)
    if len(byte_str) >= max:
        raise MeidSizeOutOfRange

    return _rmr_bytes2meid(ptr_mbuf, byte_str, len(byte_str))


# CAUTION:  Some of the C functions expect a mutable buffer to copy the bytes into;
#           if there is a get_* function below, use it to set up and return the
#           buffer properly.

# extern unsigned char*  rmr_get_meid(rmr_mbuf_t* mbuf, unsigned char* dest);
# we don't provide direct access to this function (unless it is asked for) because it is not really useful to provide your own buffer.
# Rather, rmr_get_meid does this for you, and just returns the string.
_rmr_get_meid = _wrap_rmr_function('rmr_get_meid', c_char_p, [POINTER(rmr_mbuf_t), c_char_p])


def rmr_get_meid(ptr_mbuf: POINTER(rmr_mbuf_t)) -> bytes:
    """
    Gets the managed entity ID (meid) from the message header.
    This is a python-friendly version of RMR C method::

        extern unsigned char* rmr_get_meid(rmr_mbuf_t* mbuf, unsigned char* dest);

    Parameters
    ----------
    ptr_mbuf: ctypes c_void_p
        Pointer to an RMR message buffer

    Returns
    -------
    bytes:
        Managed entity ID
    """
    sz = _get_rmr_constant("RMR_MAX_MEID", 32)  # size for buffer to fill
    buf = create_string_buffer(sz)
    _rmr_get_meid(ptr_mbuf, buf)
    return buf.value


_rmr_get_src = _wrap_rmr_function('rmr_get_src', c_char_p, [POINTER(rmr_mbuf_t), c_char_p])


def rmr_get_src(ptr_mbuf: POINTER(rmr_mbuf_t), dest: c_char_p) -> c_char_p:
    """
    Copies the message-source information to the buffer.
    Refer to RMR C documentation for method::

        extern unsigned char* rmr_get_src(rmr_mbuf_t* mbuf, unsigned char* dest);

    Parameters
    ----------
    ptr_mbuf: ctypes POINTER(rmr_mbuf_t)
        Pointer to an RMR message buffer
    dest: ctypes c_char_p
        Pointer to a buffer to receive the message source

    Returns
    -------
    string:
        message-source information
    """
    return _rmr_get_src(ptr_mbuf, dest)


# Methods that exist ONLY in rmr-python, and are not wrapped methods
# In hindsight, I wish i put these in a separate module, but leaving this here to prevent api breakage.


def get_payload(ptr_mbuf: c_void_p) -> bytes:
    """
    Gets the binary payload from the rmr_buf_t*.

    Parameters
    ----------
    ptr_mbuf: ctypes c_void_p
        Pointer to an rmr message buffer

    Returns
    -------
    bytes:
        the message payload
    """
    # Logic came from the answer here: https://stackoverflow.com/questions/55103298/python-ctypes-read-pointerc-char-in-python
    sz = ptr_mbuf.contents.len
    CharArr = c_char * sz
    return CharArr(*ptr_mbuf.contents.payload[:sz]).raw


def get_xaction(ptr_mbuf: c_void_p) -> bytes:
    """
    Gets the transaction ID from the rmr_buf_t*.

    Parameters
    ----------
    ptr_mbuf: ctypes c_void_p
        Pointer to an rmr message buffer

    Returns
    -------
    bytes:
        the transaction id
    """
    val = cast(ptr_mbuf.contents.xaction, c_char_p).value
    sz = _get_rmr_constant("RMR_MAX_XID", 0)
    return val[:sz]


def message_summary(ptr_mbuf: c_void_p) -> dict:
    """
    Returns a dict with the fields of an RMR message.

    Parameters
    ----------
    ptr_mbuf: ctypes c_void_p
        Pointer to an rmr message buffer

    Returns
    -------
    dict:
        dict message summary
    """
    return {
        "payload": get_payload(ptr_mbuf) if ptr_mbuf.contents.state == RMR_OK else None,
        "payload length": ptr_mbuf.contents.len,
        "message type": ptr_mbuf.contents.mtype,
        "subscription id": ptr_mbuf.contents.sub_id,
        "transaction id": get_xaction(ptr_mbuf),
        "message state": ptr_mbuf.contents.state,
        "message status": state_to_status(ptr_mbuf.contents.state),
        "payload max size": rmr_payload_size(ptr_mbuf),
        "meid": rmr_get_meid(ptr_mbuf),
        "message source": get_src(ptr_mbuf),
        "errno": ptr_mbuf.contents.tp_state,
    }


def set_payload_and_length(byte_str: bytes, ptr_mbuf: c_void_p):
    """
    Sets an rmr payload and content length.

    Parameters
    ----------
    byte_str: bytes
        the bytes to set the payload to
    ptr_mbuf: ctypes c_void_p
        Pointer to an rmr message buffer

    Returns
    -------
    None
    """
    if rmr_payload_size(ptr_mbuf) < len(byte_str):  # existing message payload too small
        ptr_mbuf = rmr_realloc_payload(ptr_mbuf, len(byte_str), True)

    memmove(ptr_mbuf.contents.payload, byte_str, len(byte_str))
    ptr_mbuf.contents.len = len(byte_str)


def generate_and_set_transaction_id(ptr_mbuf: c_void_p):
    """
    Generates a UUID and sets the RMR transaction id to it

    Parameters
    ----------
    ptr_mbuf: ctypes c_void_p
        Pointer to an rmr message buffer
    """
    set_transaction_id(ptr_mbuf, uuid.uuid1().hex.encode("utf-8"))


def set_transaction_id(ptr_mbuf: c_void_p, tid_bytes: bytes):
    """
    Sets an RMR transaction id
    TODO: on next API break, merge these two functions. Not done now to preserve API.

    Parameters
    ----------
    ptr_mbuf: ctypes c_void_p
        Pointer to an rmr message buffer
    tid_bytes: bytes
        bytes of the desired transaction id
    """
    sz = _get_rmr_constant("RMR_MAX_XID", 0)
    memmove(ptr_mbuf.contents.xaction, tid_bytes, sz)


def get_src(ptr_mbuf: c_void_p) -> str:
    """
    Gets the message source (likely host:port)

    Parameters
    ----------
    ptr_mbuf: ctypes c_void_p
        Pointer to an rmr message buffer

    Returns
    -------
    string:
        message source
    """
    sz = _get_rmr_constant("RMR_MAX_SRC", 64)  # size to fill
    buf = create_string_buffer(sz)
    rmr_get_src(ptr_mbuf, buf)
    return buf.value.decode()
