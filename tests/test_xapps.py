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
import json
import time
from contextlib import suppress
from ricxappframe.xapp_frame import Xapp, RMRXapp

rmr_xapp = None
gen_xapp = None


def test_flow():

    # test variables
    def_called = 0
    sixty_called = 0

    # create rmr app
    global rmr_xapp

    def post_init(self):
        self.logger.info("suppp info")
        self.logger.debug("suppp debug")

    def default_handler(self, summary, sbuf):
        nonlocal def_called
        def_called += 1
        assert json.loads(summary["payload"]) == {"test send 60001": 1}
        self.rmr_free(sbuf)

    rmr_xapp = RMRXapp(default_handler, post_init=post_init, rmr_port=4564, rmr_wait_for_ready=False, use_fake_sdl=True)

    def sixtythou_handler(self, summary, sbuf):
        nonlocal sixty_called
        sixty_called += 1
        assert json.loads(summary["payload"]) == {"test send 60000": 1}
        self.rmr_free(sbuf)

    rmr_xapp.register_callback(sixtythou_handler, 60000)
    rmr_xapp.run(thread=True)  # in unit tests we need to thread here or else execution is not returned!

    time.sleep(1)

    def entry(self):

        self.sdl_set("testns", "mykey", 6)
        assert self.sdl_get("testns", "mykey") == 6
        assert self.sdl_find_and_get("testns", "myk") == {"mykey": 6}
        assert self.healthcheck()

        val = json.dumps({"test send 60000": 1}).encode()
        self.rmr_send(val, 60000)

        val = json.dumps({"test send 60001": 2}).encode()
        self.rmr_send(val, 60001)

    global gen_xapp
    gen_xapp = Xapp(entrypoint=entry, rmr_wait_for_ready=False, use_fake_sdl=True)
    gen_xapp.run()

    time.sleep(1)

    assert def_called == 1
    assert sixty_called == 1


def teardown_module():
    """
    this is like a "finally"; the name of this function is pytest magic
    safer to put down here since certain failures above can lead to pytest never returning
    for example if an exception gets raised before stop is called in any test function above, pytest will hang forever
    """
    with suppress(Exception):
        gen_xapp.stop()
    with suppress(Exception):
        rmr_xapp.stop()
