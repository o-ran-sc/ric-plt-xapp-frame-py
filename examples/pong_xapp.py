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
from ricxappframe.xapp_frame import RMRXapp, rmr


def post_init(_self):
    """post init"""
    print("pong xapp could do some useful stuff here!")


def sixtyh(self, summary, sbuf):
    """callback for 60000"""
    self.logger.info("pong registered 60000 handler called!")
    # see comment in ping about this; bytes does not work with the ric mdc logger currently
    print("pong 60000 handler received: {0}".format(summary))
    jpay = json.loads(summary[rmr.RMR_MS_MSG_PAYLOAD])
    self.rmr_rts(sbuf, new_payload=json.dumps({"ACK": jpay["test_send"]}).encode(), new_mtype=60001, retries=100)
    self.rmr_free(sbuf)


def defh(self, summary, sbuf):
    """default callback"""
    self.logger.info("pong default handler called!")
    print("pong default handler received: {0}".format(summary))
    self.rmr_free(sbuf)


xapp = RMRXapp(default_handler=defh, post_init=post_init, use_fake_sdl=True)
xapp.register_callback(sixtyh, 60000)
xapp.run()  # will not thread by default
