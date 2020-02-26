"""Test xapp"""
import json
from xapp_frame import RMRXapp


# Note, this is an OOP pattern for this that I find slightly more natural
# The problem is we want the client xapp to be able to call methods defined in the RMRXapp
# Another exactly equivelent way would have been to use Closures like
# def consume(summary, sbuf):
#    xapp.rts()
# xapp = RMRXapp(consume)
# However, the subclass looks slightly more natural. Open to the alternative.


class MyXapp(RMRXapp):
    def consume(self, summary, sbuf):
        """callbnack called for each new message"""
        print(summary)
        jpay = json.loads(summary["payload"])
        self.rmr_rts(sbuf, new_payload=json.dumps({"ACK": jpay["test_send"]}).encode(), new_mtype=60001, retries=100)
        self.rmr_free(sbuf)


xapp = MyXapp(use_fake_sdl=True)
xapp.run()
