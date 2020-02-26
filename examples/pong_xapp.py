"""
Test xapp 2 that works with 1
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
import json
from ricxappframe.xapp_frame import RMRXapp


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
