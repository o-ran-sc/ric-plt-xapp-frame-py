"""
Test xapp 1
"""
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
import json
from threading import Thread
from rmr import rmr
from ricxappframe.xapp_frame import Xapp

# Now we use the framework to echo back the acks
class MyXapp(Xapp):
    def entrypoint(self):
        my_ns = "myxapp"
        number = 0
        while True:
            # test healthcheck
            print("Healthy? {}".format(xapp.healthcheck()))

            # rmr send
            val = json.dumps({"test_send": number}).encode()
            self.rmr_send(val, 60000)
            number += 1

            # store it in SDL and read it back; delete and read
            self.sdl_set(my_ns, "numba", number)
            print((self.sdl_get(my_ns, "numba"), self.sdl_find_and_get(my_ns, "num")))
            self.sdl_delete(my_ns, "numba")
            print(self.sdl_get(my_ns, "numba"))

            # rmr receive
            for (summary, sbuf) in self.rmr_get_messages():
                print(summary)
                self.rmr_free(sbuf)

            time.sleep(1)


xapp = MyXapp(4564, use_fake_sdl=True)
xapp.run()
