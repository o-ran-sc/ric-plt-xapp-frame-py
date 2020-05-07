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
from ricxappframe.xapp_frame import Xapp


def entry(self):
    my_ns = "myxapp"
    number = 0
    while True:
        # test healthcheck
        print("ping is healthy? {}".format(xapp.healthcheck()))

        # rmr send to default handler
        self.rmr_send(json.dumps({"ping": number}).encode(), 6660666)

        # rmr send 60000, should trigger registered callback
        val = json.dumps({"test_send": number}).encode()
        self.rmr_send(val, 60000)
        number += 1

        # store it in SDL and read it back; delete and read
        self.sdl_set(my_ns, "ping", number)
        self.logger.info(self.sdl_get(my_ns, "ping"))
        self.logger.info(self.sdl_find_and_get(my_ns, "pin"))
        self.sdl_delete(my_ns, "ping")
        self.logger.info(self.sdl_get(my_ns, "ping"))

        # rmr receive
        for (summary, sbuf) in self.rmr_get_messages():
            # summary is a dict that contains bytes so we can't use json.dumps on it
            # so we have no good way to turn this into a string to use the logger unfortunately
            # print is more "verbose" than the ric logger
            # if you try to log this you will get: TypeError: Object of type bytes is not JSON serializable
            print("ping: {0}".format(summary))
            self.rmr_free(sbuf)

        time.sleep(2)


xapp = Xapp(entrypoint=entry, rmr_port=4564, use_fake_sdl=True)
xapp.run()
