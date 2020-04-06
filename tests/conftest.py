# vim: ts=4 sw=4 expandtab:
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
import pytest


# These are here just to reduce the size of the code in test_rmr so those (important) tests are more readable; in theory these dicts could be large
# The actual value of the constants should be ignored by the tests; all we should care
# about is that the constant value was returned by the RMR function. Further, we should
# not consider it an error if RMR returns more than what is listed here; these are the
# list of what is/could be used by this package.
@pytest.fixture
def expected_constants():
    return {
        "RMR_MAX_XID": 32,
        "RMR_MAX_SID": 32,
        "RMR_MAX_MEID": 32,
        "RMR_MAX_SRC": 64,
        "RMR_MAX_RCV_BYTES": 4096,
        "RMRFL_NONE": 0,
        "RMRFL_MTCALL": 2,  # can't be added here until jenkins version >= 1.8.3
        "RMRFL_AUTO_ALLOC": 3,
        "RMR_DEF_SIZE": 0,
        "RMR_VOID_MSGTYPE": -1,
        "RMR_VOID_SUBID": -1,
        "RMR_OK": 0,
        "RMR_ERR_BADARG": 1,
        "RMR_ERR_NOENDPT": 2,
        "RMR_ERR_EMPTY": 3,
        "RMR_ERR_NOHDR": 4,
        "RMR_ERR_SENDFAILED": 5,
        "RMR_ERR_CALLFAILED": 6,
        "RMR_ERR_NOWHOPEN": 7,
        "RMR_ERR_WHID": 8,
        "RMR_ERR_OVERFLOW": 9,
        "RMR_ERR_RETRY": 10,
        "RMR_ERR_RCVFAILED": 11,
        "RMR_ERR_TIMEOUT": 12,
        "RMR_ERR_UNSET": 13,
        "RMR_ERR_TRUNC": 14,
        "RMR_ERR_INITFAILED": 15,
    }


@pytest.fixture
def expected_states():
    return {
        0: "RMR_OK",
        1: "RMR_ERR_BADARG",
        2: "RMR_ERR_NOENDPT",
        3: "RMR_ERR_EMPTY",
        4: "RMR_ERR_NOHDR",
        5: "RMR_ERR_SENDFAILED",
        6: "RMR_ERR_CALLFAILED",
        7: "RMR_ERR_NOWHOPEN",
        8: "RMR_ERR_WHID",
        9: "RMR_ERR_OVERFLOW",
        10: "RMR_ERR_RETRY",
        11: "RMR_ERR_RCVFAILED",
        12: "RMR_ERR_TIMEOUT",
        13: "RMR_ERR_UNSET",
        14: "RMR_ERR_TRUNC",
        15: "RMR_ERR_INITFAILED",
    }
