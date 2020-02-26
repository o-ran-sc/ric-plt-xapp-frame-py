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
from ricxappframe.xapp_frame import Xapp

gen_xapp = None
rmr_xapp = None


def test_init_general_xapp():
    class MyXapp(Xapp):
        # TODO: obviouslly a lot more is needed here. For now this tests that the class is instantiable.
        def loop(self):
            print("ok")

    global gen_xapp
    gen_xapp = MyXapp(rmr_wait_for_ready=False)
    gen_xapp.run()


def teardown_module():
    """
    module teardown

    pytest will never return without this.
    """
    gen_xapp.stop()
