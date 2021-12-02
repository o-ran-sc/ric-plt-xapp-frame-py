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
import ctypes
from ctypes.util import find_library
import json

# Subpackage that creates and publishes a reference to the C shared library.
# Intended to be private; RMR-python and xapp-frame-py users should not need this.
# Sphinx and autodoc mock this module to run without the .so file present.

# https://docs.python.org/3.7/library/ctypes.html
# https://stackoverflow.com/questions/2327344/ctypes-loading-a-c-shared-library-that-has-dependencies/30845750#30845750
# make sure you do a set -x LD_LIBRARY_PATH /usr/local/lib/;
rmr_c_lib = ctypes.CDLL("librmr_si.so", mode=ctypes.RTLD_GLOBAL)
_rmr_get_consts = rmr_c_lib.rmr_get_consts
_rmr_get_consts.argtypes = []
_rmr_get_consts.restype = ctypes.c_void_p

libc = ctypes.CDLL(find_library("c"))
_libc_free = libc.free
_libc_free.argtypes = [ctypes.c_void_p]
_libc_free.restype = None


def get_constants(cache={}):
    """
    Gets constants published by RMR and caches for subsequent calls.
    TODO: are there constants that end user applications need?
    """
    if cache:
        return cache

    ptr = _rmr_get_consts()  # read pointer to json data
    js = ctypes.cast(ptr, ctypes.c_char_p).value  # cast it to python string
    cache = json.loads(str(js.decode()))  # create constants value object as a hash
    _libc_free(ptr)
    return cache


def get_mapping_dict(cache={}):
    """
    Builds a state mapping dict from constants and caches for subsequent calls.
    Relevant constants at this writing include:

    RMR_OK              0   state is good
    RMR_ERR_BADARG      1   argument passd to function was unusable
    RMR_ERR_NOENDPT     2   send/call could not find an endpoint based on msg type
    RMR_ERR_EMPTY       3   msg received had no payload; attempt to send an empty message
    RMR_ERR_NOHDR       4   message didn't contain a valid header
    RMR_ERR_SENDFAILED  5   send failed; errno has nano reason
    RMR_ERR_CALLFAILED  6   unable to send call() message
    RMR_ERR_NOWHOPEN    7   no wormholes are open
    RMR_ERR_WHID        8   wormhole id was invalid
    RMR_ERR_OVERFLOW    9   operation would have busted through a buffer/field size
    RMR_ERR_RETRY       10  request (send/call/rts) failed, but caller should retry (EAGAIN for wrappers)
    RMR_ERR_RCVFAILED   11  receive failed (hard error)
    RMR_ERR_TIMEOUT     12  message processing call timed out
    RMR_ERR_UNSET       13  the message hasn't been populated with a transport buffer
    RMR_ERR_TRUNC       14  received message likely truncated
    RMR_ERR_INITFAILED  15  initialization of something (probably message) failed

    """
    if cache:
        return cache

    rmr_consts = get_constants()
    for key in rmr_consts:  # build the state mapping dict
        if key[:7] in ["RMR_ERR", "RMR_OK"]:
            en = int(rmr_consts[key])
            cache[en] = key

    return cache


def state_to_status(stateno):
    """
    Converts a msg state integer to a status string.

    Returns "UNKNOWN STATE" if the int value is not known.
    """
    sdict = get_mapping_dict()
    return sdict.get(stateno, "UNKNOWN STATE")
