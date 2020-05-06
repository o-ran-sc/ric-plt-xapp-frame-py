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
tests data functions
"""

from ricxappframe.xapp_sdl import SDLWrapper


NS = "testns"


def test_sdl():
    """
    test raw sdl functions
    """
    sdl = SDLWrapper(use_fake_sdl=True)
    sdl.set(NS, "as.df1", "data")
    sdl.set(NS, "as.df2", "data2")
    assert sdl.get(NS, "as.df1") == "data"
    assert sdl.get(NS, "as.df2") == "data2"
    assert sdl.find_and_get(NS, "as.df1") == {"as.df1": "data"}
    assert sdl.find_and_get(NS, "as.df2") == {"as.df2": "data2"}
    assert sdl.find_and_get(NS, "as.df") == {"as.df1": "data", "as.df2": "data2"}
    assert sdl.find_and_get(NS, "as.d") == {"as.df1": "data", "as.df2": "data2"}
    assert sdl.find_and_get(NS, "as.") == {"as.df1": "data", "as.df2": "data2"}
    assert sdl.find_and_get(NS, "asd") == {}

    # delete 1
    sdl.delete(NS, "as.df1")
    assert sdl.get(NS, "as.df1") is None
    assert sdl.get(NS, "as.df2") == "data2"

    # delete 2
    sdl.delete(NS, "as.df2")
    assert sdl.get(NS, "as.df2") is None

    assert sdl.find_and_get(NS, "as.df") == {}
    assert sdl.find_and_get(NS, "") == {}
