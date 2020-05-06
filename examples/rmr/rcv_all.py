# vim: ts=4 sw=4 expandtab:
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

#   Mnemonic:   rcv_all.py
#   Abstract:   This example shows how to receive all queued messages into
#               a bunch (an array of summaries).  RMR is initialised in multi-
#               threaded call mode so that it will queue messages on a 2K ring
#               and prevent the remote application(s) from blocking if we don't
#               do timely receives.  Then we read 'bursts' of messages sleeping
#               between reads to allow some message to pile up.
#
#               Because this programme does not send messages, there is no reason
#               to wait for RMR to initialise a route table (no call to rmr_ready
#               is needed.
#
#   Date:       26 September 2019
#
# ---------------------------------------------------------------------------------

from rmr import rmr
from rmr import helpers
import time
import sys
import signal


#    Ensure things terminate nicely
#
def signal_handler(sig, frame):
    print('SIGINT received! Cleaning up rmr')
    rmr.rmr_close(mrc)
    print("Byeee")
    sys.exit(0)

listen_port = "4560".encode('utf-8')                                          # port RMR will listen on (RMR needs string, not value)
mrc = rmr.rmr_init( listen_port, rmr.RMR_MAX_RCV_BYTES, rmr.RMRFL_MTCALL )    # put into multi-threaded call mode

signal.signal(signal.SIGINT, signal_handler)    # cleanup on ctl-c

while True:

    # three calling options:
    #mbunch = helpers.rmr_rcvall_msgs( mrc, [2, 4, 6] )     # get types 2, 4 and 6 only
    #mbunch = helpers.rmr_rcvall_msgs( mrc, [2] )           # get types 2 only
    mbunch = helpers.rmr_rcvall_msgs( mrc )                 # get all message types

    if mbunch == None or  len( mbunch ) < 1:
        print( "no messages" )
    else:
        print( "got %d messages" % len( mbunch ) )
        for mb in mbunch:
            print( "type=%d payload=%s" % (mb[rmr.RMR_MS_MSG_TYPE], mb[rmr.RMR_MS_PAYLOAD] ) )

    time.sleep( 1 )            # sleep to allow some to accumulate

