 #!/bin/bash

 pytest --cov . \
    --cov-report xml \
    --cov-report term-missing \
    --cov-report html \
    --cov-config=./asn1/test/.coveragerc
