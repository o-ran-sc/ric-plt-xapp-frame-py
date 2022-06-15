#!/bin/sh
export RMR_SEED_RT=/opt/ric/config/xapp-test.rt
python3 ./xapp_test.py -xapp xapp-test -config /opt/ric/config/config-file.json -service xapp-test &
while [ 1 ]; do
	# just dummy sleep command
	sleep 60
done
