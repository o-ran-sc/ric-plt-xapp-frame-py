# Tests

First, edit the `local.rt` file with your hostname.

Start the receiver and the tester. Be sure to set `LD_LIBRARY_PATH` or your system equivelent to point to where the RMR .so files are. On my system (Arch Linux) they are as below. Also, `set -x` is fish shell notation, substitute for your shell.

    set -x LD_LIBRARY_PATH /usr/local/lib/; set -x RMR_SEED_RT ./local.rt; python receive.py
    set -x LD_LIBRARY_PATH /usr/local/lib/; set -x RMR_SEED_RT ./local.rt; python send.py
