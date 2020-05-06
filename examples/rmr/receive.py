# ==================================================================================
#       Copyright (c) 2019 Nokia
#       Copyright (c) 2018-2019 AT&T Intellectual Property.
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
from ricxappframe.rmr import rmr
import time
import sys
import signal


# Demonstrate RMR cleanup
def signal_handler(sig, frame):
    print("SIGINT received! Cleaning up RMR")
    rmr.rmr_close(mrc)
    print("Byeee")
    sys.exit(0)


# init rmr
mrc = rmr.rmr_init("4560".encode("utf-8"), rmr.RMR_MAX_RCV_BYTES, 0x00)
while rmr.rmr_ready(mrc) == 0:
    time.sleep(1)
    print("not yet ready")
rmr.rmr_set_stimeout(mrc, 2)

# capture ctrl-c
signal.signal(signal.SIGINT, signal_handler)


sbuf = None
while True:
    print("Waiting for a message, will timeout after 2000ms")
    sbuf = rmr.rmr_torcv_msg(mrc, sbuf, 2000)
    summary = rmr.message_summary(sbuf)
    if summary[rmr.RMR_MS_MSG_STATE] == 12:
        print("Nothing received =(")
    else:
        print("Message received!: {}".format(summary))
        val = b"message recieved OK yall!"
        rmr.set_payload_and_length(val, sbuf)
        sbuf = rmr.rmr_rts_msg(mrc, sbuf)
    time.sleep(1)
