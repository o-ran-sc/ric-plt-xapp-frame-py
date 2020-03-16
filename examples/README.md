# Python xapp frame

# Running locally

Running the two examples (adjust for your shell notation)

    pip install --user -e .
    cd examples
    set -x LD_LIBRARY_PATH /usr/local/lib/:/usr/local/lib64; set -x  RMR_SEED_RT test_route.rt; python pong_xapp.py
    (diff tmux window)
    set -x LD_LIBRARY_PATH /usr/local/lib/:/usr/local/lib64; set -x  RMR_SEED_RT test_route.rt; python ping_xapp.py

# Running in Docker

    docker build -t ping:latest -f  Dockerfile-Ping .
    docker build -t pong:latest -f  Dockerfile-Pong .
    docker run -i --net=host ping:latest
    docker run -i --net=host pong:latest
