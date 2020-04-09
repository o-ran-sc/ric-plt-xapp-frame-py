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
from ricxappframe.rmrclib import rmrclib


def test_get_constants(expected_constants):
    """
    test getting constants. We don't care what values are returned as those
    should be meaningful only to RMR. We do care that all of the constants
    which are defined in expected_contents are returned.  Further, we don't
    consider it to be an error if the returned list has more constants than
    what are in our list.

    To avoid frustration, this should list all missing keys, not fail on the
    first missing key.
    """
    errors = 0
    econst = expected_constants
    rconst = rmrclib.get_constants()
    for key in econst:  # test all expected constants
        if key not in rconst:  # expected value not listed by rmr
            errors += 1
            print("did not find required constant in list from RMR: %s" % key)

    assert errors == 0


def test_get_mapping_dict(expected_states):
    """
    test getting mapping string
    """
    assert rmrclib.get_mapping_dict() == expected_states
    assert rmrclib.state_to_status(0) == "RMR_OK"
    assert rmrclib.state_to_status(12) == "RMR_ERR_TIMEOUT"
    assert rmrclib.state_to_status(666) == "UNKNOWN STATE"
