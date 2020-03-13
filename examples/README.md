# Python xapp frame

Running the two examples (adjust for your shell notation)

    pip install --user -e .
    cd examples
    set -x LD_LIBRARY_PATH /usr/local/lib/:/usr/local/lib64; set -x  RMR_SEED_RT test_route.rt; python pong_xapp.py
    (diff tmux window)
    set -x LD_LIBRARY_PATH /usr/local/lib/:/usr/local/lib64; set -x  RMR_SEED_RT test_route.rt; python ping_xapp.py
