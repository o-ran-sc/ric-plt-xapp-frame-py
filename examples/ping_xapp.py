"""
Test receiver
"""

import time
import json
from threading import Thread
from rmr import rmr
from ricxappframe.xapp_frame import Xapp

# Now we use the framework to echo back the acks
class MyXapp(Xapp):
    def loop(self):
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
