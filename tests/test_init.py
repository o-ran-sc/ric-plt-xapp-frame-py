# ==================================================================================
#       Copyright (c) 2020 Nokia
#       Copyright (c) 2020 AT&T Intellectual Property.
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
import requests
from unittest.mock import Mock
from ricxappframe.rmr.exceptions import InitFailed
from ricxappframe.xapp_frame import Xapp, RMRXapp

mock_post_200 = Mock(return_value=Mock(status_code=200, text='Mocked response'))
mock_post_204 = Mock(return_value=Mock(status_code=204, text='Mocked response'))


def test_bad_init():
    """test that an xapp whose rmr fails to init blows up"""

    def entry(self):
        pass

    with pytest.raises(InitFailed):
        bad_xapp = Xapp(xapp_ready_cb=entry, rmr_port=-1)
        bad_xapp.run()  # we wont get here

    def defh(self):
        pass

    with pytest.raises(InitFailed):
        bad_xapp = RMRXapp(default_handler=defh, rmr_port=-1)
        bad_xapp.run()  # we wont get here


def test_init_general_xapp(monkeypatch):
    def entry(self):
        # normally we would have some kind of loop here
        print("bye")

    monkeypatch.setattr(requests.Session, 'post', mock_post_200)
    gen_xapp = Xapp(xapp_ready_cb=entry, use_fake_sdl=True)
    gen_xapp.run()
    time.sleep(1)
    monkeypatch.setattr(requests.Session, 'post', mock_post_204)
    gen_xapp.stop()  # pytest will never return without this.


def test_init_rmr_xapp(monkeypatch):
    def post_init(self):
        print("hey")

    def foo(self, _summary, _sbuf):
        pass

    monkeypatch.setattr(requests.Session, 'post', mock_post_200)
    rmr_xapp = RMRXapp(foo, post_init=post_init, use_fake_sdl=True)
    # pytest will never return without thread and stop
    rmr_xapp.run(thread=True)
    time.sleep(1)
    monkeypatch.setattr(requests.Session, 'post', mock_post_204)
    rmr_xapp.stop()
