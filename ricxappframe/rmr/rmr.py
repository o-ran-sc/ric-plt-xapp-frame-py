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
"""
Wraps all RMR functions, but does not have a reference to the shared library.
"""
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
#: State constant for no endpoint based on msg type
RMR_ERR_NOENDPT = _get_rmr_constant('RMR_ERR_NOENDPT')
#: State constant for retry
RMR_ERR_RETRY = _get_rmr_constant('RMR_ERR_RETRY')
#: State constant for timeout
RMR_ERR_TIMEOUT = _get_rmr_constant('RMR_ERR_TIMEOUT')

# Publish keys used in the message summary dict as constants

# message payload, bytes
RMR_MS_PAYLOAD = "payload"
# payload length, integer
RMR_MS_PAYLOAD_LEN = "payload length"
# message type, integer
RMR_MS_MSG_TYPE = "message type"
# subscription ID, integer
RMR_MS_SUB_ID = "subscription id"
# transaction ID, bytes
RMR_MS_TRN_ID = "transaction id"
# state of message processing, integer; e.g., 0
RMR_MS_MSG_STATE = "message state"
# state of message processing converted to string; e.g., RMR_OK
RMR_MS_MSG_STATUS = "message status"
# number of bytes usable in the payload, integer
RMR_MS_PAYLOAD_MAX = "payload max size"
# managed entity ID, bytes
RMR_MS_MEID = "meid"
# message source, string; e.g., host:port
RMR_MS_MSG_SOURCE = "message source"
# transport state, integer
RMR_MS_ERRNO = "errno"


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
    |    void*   tp_buf;         // underlying transport allocated pointer
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
    # re payload, according to the following the python bytes are already unsigned:
    # https://bytes.com/topic/python/answers/695078-ctypes-unsigned-char
    _fields_ = [
        ("state", c_int),
        ("mtype", c_int),
        ("len", c_int),
        ("payload", POINTER(c_char)),
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


_rmr_realloc_payload = _wrap_rmr_function('rmr_realloc_payload', POINTER(rmr_mbuf_t), [POINTER(rmr_mbuf_t), c_int, c_int, c_int])


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

        extern int rmr_payload_size(rmr_mbuf_t* mbuf)

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


_rmr_send_msg = _wrap_rmr_function('rmr_send_msg', POINTER(rmr_mbuf_t), [c_void_p, POINTER(rmr_mbuf_t)])


def rmr_send_msg(vctx: c_void_p, ptr_mbuf: POINTER(rmr_mbuf_t)) -> POINTER(rmr_mbuf_t):
    """
    Sends the message according to the routing table and returns an empty buffer.
    Refer to RMR C documentation for method::

        extern rmr_mbuf_t* rmr_send_msg(void* vctx, rmr_mbuf_t* mbuf)

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context
    ptr_mbuf: c_void_p
        Pointer to rmr_mbuf structure

    Returns
    -------
    ctypes c_void_p:
        Pointer to rmr_mbuf structure
    """
    return _rmr_send_msg(vctx, ptr_mbuf)


# TODO: the old message (Send param) is actually optional, but I don't know how to specify that in Ctypes.
_rmr_rcv_msg = _wrap_rmr_function('rmr_rcv_msg', POINTER(rmr_mbuf_t), [c_void_p, POINTER(rmr_mbuf_t)])


def rmr_rcv_msg(vctx: c_void_p, ptr_mbuf: POINTER(rmr_mbuf_t)) -> POINTER(rmr_mbuf_t):
    """
    Waits for a message to arrive, and returns it.
    Refer to RMR C documentation for method::

        extern rmr_mbuf_t* rmr_rcv_msg(void* vctx, rmr_mbuf_t* old_mbuf)

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context
    ptr_mbuf: c_void_p
        Pointer to rmr_mbuf structure

    Returns
    -------
    ctypes c_void_p:
        Pointer to rmr_mbuf structure
    """
    return _rmr_rcv_msg(vctx, ptr_mbuf)


_rmr_torcv_msg = _wrap_rmr_function('rmr_torcv_msg', POINTER(rmr_mbuf_t), [c_void_p, POINTER(rmr_mbuf_t), c_int])


def rmr_torcv_msg(vctx: c_void_p, ptr_mbuf: POINTER(rmr_mbuf_t), ms_to: int) -> POINTER(rmr_mbuf_t):
    """
    Waits up to the timeout value for a message to arrive, and returns it.
    Refer to RMR C documentation for method::

        extern rmr_mbuf_t* rmr_torcv_msg(void* vctx, rmr_mbuf_t* old_mbuf, int ms_to)

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
    ctypes c_void_p:
        Pointer to rmr_mbuf structure
    """
    return _rmr_torcv_msg(vctx, ptr_mbuf, ms_to)


_rmr_rts_msg = _wrap_rmr_function('rmr_rts_msg', POINTER(rmr_mbuf_t), [c_void_p, POINTER(rmr_mbuf_t)])


def rmr_rts_msg(vctx: c_void_p, ptr_mbuf: POINTER(rmr_mbuf_t), payload=None, mtype=None) -> POINTER(rmr_mbuf_t):
    """
    Sends a message to the originating endpoint and returns an empty buffer.
    Refer to RMR C documentation for method::

        extern rmr_mbuf_t* rmr_rts_msg(void* vctx, rmr_mbuf_t* mbuf)

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
    ctypes c_void_p:
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

        extern rmr_mbuf_t* rmr_call(void* vctx, rmr_mbuf_t* mbuf)

    Parameters
    ----------
    ptr_mbuf: ctypes c_void_p
        Pointer to an RMR message buffer

    Returns
    -------
    ctypes c_void_p:
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
        Pointer to rmr_mbuf structure
    byte_tr: bytes
        Managed entity ID value

    Returns
    -------
    int:
        number of bytes copied
    """
    max_meid = _get_rmr_constant("RMR_MAX_MEID", 32)
    if len(byte_str) >= max_meid:
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
        Pointer to rmr_mbuf structure

    Returns
    -------
    bytes:
        Managed entity ID
    """
    max_meid = _get_rmr_constant("RMR_MAX_MEID", 32)  # size for buffer to fill
    buf = create_string_buffer(max_meid)
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
        Pointer to rmr_mbuf structure
    dest: ctypes c_char_p
        Pointer to a buffer to receive the message source

    Returns
    -------
    string:
        message-source information
    """
    return _rmr_get_src(ptr_mbuf, dest)


_rmr_set_vlevel = _wrap_rmr_function('rmr_set_vlevel', None, [c_int])


def rmr_set_vlevel(new_level: c_int):
    """
    Sets the verbosity level which determines the messages RMR writes to standard error.
    Refer to RMR C documentation for method::

        void rmr_set_vlevel( int new_level )

    Parameters
    ----------
    new_level: int
        New logging verbosity level, an integer in the range 0 (none) to 5 (debug).
    """
    _rmr_set_vlevel(new_level)


_rmr_wh_call = _wrap_rmr_function('rmr_wh_call', POINTER(rmr_mbuf_t), [c_void_p, c_int, POINTER(rmr_mbuf_t), c_int, c_int])


def rmr_wh_call(vctx: c_void_p, whid: c_int, ptr_mbuf: POINTER(rmr_mbuf_t), call_id: c_int, max_wait: c_int) -> POINTER(rmr_mbuf_t):
    """
    Sends a message buffer (msg) using a wormhole ID (whid) and waits for a response.
    Refer to RMR C documentation for method::

        rmr_mbuf_t* rmr_wh_call( void* vctx, rmr_whid_t whid, rmr_mbuf_t* mbuf, int call_id, int max_wait )

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context
    whid: c_int
        Wormhole ID returned by rmr_wh_open
    ptr_mbuf: ctypes POINTER(rmr_mbuf_t)
        Pointer to rmr_mbuf structure
    call_id: c_int
        number in the range of 2..255 to identify the caller
    max_wait: c_int
        number of milliseconds to wait for a reply

    Returns
    -------
    ctypes c_void_p:
        Pointer to rmr_mbuf structure
    """
    return _rmr_wh_call(vctx, whid, ptr_mbuf, call_id, max_wait)


_rmr_wh_close = _wrap_rmr_function('rmr_close', None, [c_void_p, c_int])


def rmr_wh_close(vctx: c_void_p, whid: c_int):
    """
    Closes the wormhole associated with the wormhole id.
    Refer to RMR C documentation for method::

        void rmr_close( void* vctx, rmr_whid_t whid )

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context
    whid: c_int
        Wormhole ID returned by rmr_wh_open
    """
    _rmr_wh_close(vctx, whid)


_rmr_wh_open = _wrap_rmr_function('rmr_wh_open', c_int, [c_void_p, c_char_p])


def rmr_wh_open(vctx: c_void_p, target: c_char_p) -> c_int:
    """
    Creates a direct link for sending to another RMR based process.
    Refer to RMR C documentation for method::

        rmr_whid_t rmr_wh_open( void* vctx, char* target )

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context
    target: str
        Pointer to bytes built from the target process host name and port number
        as a string; e.g., b'localhost:4550'

    Returns
    -------
    c_int:
        Wormhole ID
    """
    return _rmr_wh_open(vctx, target)


_rmr_wh_send_msg = _wrap_rmr_function('rmr_wh_send_msg', POINTER(rmr_mbuf_t), [c_void_p, c_int, POINTER(rmr_mbuf_t)])


def rmr_wh_send_msg(vctx: c_void_p, whid: c_int, ptr_mbuf: POINTER(rmr_mbuf_t)) -> POINTER(rmr_mbuf_t):
    """
    Sends a message buffer (msg) using a wormhole ID (whid).
    Refer to RMR C documentation for method::

        rmr_mbuf_t* rmr_wh_send_msg( void* vctx, rmr_whid_t id, rmr_mbuf_t* msg )

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context
    whid: c_int
        Wormhole ID returned by rmr_wh_open
    ptr_mbuf: ctypes POINTER(rmr_mbuf_t)
        Pointer to rmr_mbuf structure

    Returns
    -------
    ctypes POINTER(rmr_mbuf_t):
        Pointer to rmr_mbuf structure
    """
    return _rmr_wh_send_msg(vctx, whid, ptr_mbuf)


_rmr_wh_state = _wrap_rmr_function('rmr_wh_state', c_int, [c_void_p, c_int])


def rmr_wh_state(vctx: c_void_p, whid: c_int) -> c_int:
    """
    Gets the state of the connection associated with the given wormhole (whid).
    Refer to RMR C documentation for method::

        int rmr_wh_state( void* vctx, rmr_whid_t whid )

    Parameters
    ----------
    vctx: ctypes c_void_p
        Pointer to RMR context
    whid: c_int
        Wormhole ID returned by rmr_wh_open

    Returns
    -------
    c_int:
        State of the connection
    """
    return _rmr_wh_state(vctx, whid, whid)


########################################################################################
# Methods that exist ONLY in rmr-python, and are not wrapped methods.
# These should have been in a separate module, but leaving here to prevent api breakage.
########################################################################################


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
    # Logic came from the answer here:
    # https://stackoverflow.com/questions/55103298/python-ctypes-read-pointerc-char-in-python
    length = ptr_mbuf.contents.len
    char_arr = c_char * length
    return char_arr(*ptr_mbuf.contents.payload[:length]).raw


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
    max_xid = _get_rmr_constant("RMR_MAX_XID", 0)
    return val[:max_xid]


def message_summary(ptr_mbuf: c_void_p) -> dict:
    """
    Builds a dict with the contents of an RMR message.

    Parameters
    ----------
    ptr_mbuf: ctypes c_void_p
        Pointer to an RMR message buffer

    Returns
    -------
    dict:
        Message content as key-value pairs; keys are defined as RMR_MS_* constants.
    """
    return {
        RMR_MS_PAYLOAD: get_payload(ptr_mbuf) if ptr_mbuf.contents.state == RMR_OK else None,
        RMR_MS_PAYLOAD_LEN: ptr_mbuf.contents.len,
        RMR_MS_MSG_TYPE: ptr_mbuf.contents.mtype,
        RMR_MS_SUB_ID: ptr_mbuf.contents.sub_id,
        RMR_MS_TRN_ID: get_xaction(ptr_mbuf),
        RMR_MS_MSG_STATE: ptr_mbuf.contents.state,
        RMR_MS_MSG_STATUS: state_to_status(ptr_mbuf.contents.state),
        RMR_MS_PAYLOAD_MAX: rmr_payload_size(ptr_mbuf),
        RMR_MS_MEID: rmr_get_meid(ptr_mbuf),
        RMR_MS_MSG_SOURCE: get_src(ptr_mbuf),
        RMR_MS_ERRNO: ptr_mbuf.contents.tp_state,
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
    max_xid = _get_rmr_constant("RMR_MAX_XID", 0)
    memmove(ptr_mbuf.contents.xaction, tid_bytes, max_xid)


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
    max_src = _get_rmr_constant("RMR_MAX_SRC", 64)  # size to fill
    buf = create_string_buffer(max_src)
    rmr_get_src(ptr_mbuf, buf)
    return buf.value.decode()
