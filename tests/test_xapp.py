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
import pytest
from ricxappframe.xapp_frame import Xapp

gen_xapp = None
rmr_xapp = None


def test_bad_gen_xapp():
    class MyXapp(Xapp):
        def post_init(self):
            pass

    with pytest.raises(NotImplementedError):
        # missing entrypoint
        bad_xapp = MyXapp(rmr_wait_for_ready=False, use_fake_sdl=True)
        bad_xapp.run()


def test_init_general_xapp():
    class MyXapp(Xapp):
        def post_init(self):
            self.sdl_set("testns", "mykey", 6)

        def entrypoint(self):
            assert self.sdl_get("testns", "mykey") == 6
            assert self.sdl_find_and_get("testns", "myk") == {"mykey": 6}
            assert self.healthcheck()
            # normally we would have some kind of loop here
            print("bye")

    global gen_xapp
    gen_xapp = MyXapp(rmr_wait_for_ready=False, use_fake_sdl=True)
    gen_xapp.run()


def teardown_module():
    """
    module teardown

    pytest will never return without this.
    """
    gen_xapp.stop()
