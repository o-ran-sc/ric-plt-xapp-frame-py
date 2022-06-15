.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0
.. Copyright (C) 2020 AT&T Intellectual Property

Developer Guide
===============

This document explains how to maintain the RIC Xapp framework.
Information for users of this framework (i.e., Xapp developers) is in the User Guide.

Tech Stack
----------

The framework requires Python version 3.8 or later, and depends on
these packages provided by the O-RAN-SC project and third parties:

* msgpack
* mdclogpy
* ricsdl
* protobuf


Version bumping the framework
-----------------------------

This project follows semver. When changes are made, the versions are in:

#. ``docs/release-notes.rst``
#. ``setup.py``

Version bumping RMR
-------------------

These items in this repo must be kept in sync with the RMR version:

#. Dockerfile-Unit-Test
#. examples/Dockerfile-Ping
#. examples/Dockerfile-Pong
#. ``rmr-version.yaml`` controls what version of RMR is installed for
   unit testing in Jenkins CI

Registration/Deregistartion of Xapp
-----------------------------------

For registration and deregistration of Xapp following items need to be defined:

#. CONFIG_FILE_PATH variable as a environment variable in Dockerfile if running
   Xapp as a docker container or in configmap in case of Xapp as a pod.
#. Copy the xappConfig.json into the docker image in Dockerfile.

Example Xapp
------------

Director examples has many examples for creating the xapp having features like:
* REST subscription interface
* symptomdata handler
* rmr send/receive
* REST healthy and ready response handler
* REST config handler

List of xapps:
* ping_xapp.py and ping_xapp.py using RMR to send and receive
* xapp_symptomdata.py for subscribing the symptomdata event
* xapp_test.py for both symptomdata, RMR recveice, k8s healthy service and REST subscription

xapp_test.py
------------

Test xapp can be run by creating the docker container or as standalone process. For testing restserversimu.py
has been made to emulate the REST subscription request responses and responding the symptomdata dynamic registration
reponse. When running the xapp_test you need to create the RMR static routing file so that the rmr initialization
will return (otherwise it will wait for rtmgr connection).

Test xapp has as well the config file in descriptor/config-file.json where your can adjust the local runtime
environment for subscriptions and symptomdata lwsd service ip address.

Subsciprion interface url has the submgr service endpoint : ``http://service-ricplt-submgr-http.ricplt:8088/``
Symptomdata registration url set to lwsd service url : ``http://service-ricplt-lwsd-http.ricplt:8080/ric/v1/lwsd``

In case of using restserversimu.py for testing configure your host ip address, for example 192.168.1.122 port 8090:

Subsciprion interface url has the submgr service endpoint : ``http://192.168.1.122:9000/``
Symptomdata registration url set to lwsd service url : ``http://192.168.1.122:9000/ric/v1/lwsd``

Then start the restserversimu:

export PYTHONPATH=./
python3 examples/restserversimu.py -port 9000 -address 192.168.1.122

and then the xapp_test:

export PYTHONPATH=./
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
export RMR_SEED_RT=examples/descriptor/xapp-test.rt
export RMR_SRC_ID="192.168.1.122"
python3 examples/xapp_test.py -config examples/descriptor/config-file.json -port 8888 -xapp xapp-test -service xapp-test

If you like to implement the kubernetes healthy service responder, you can follow the example how to use the 
xapp_rest.py defined rest hander. Basically you can initiate the REST service listener and add the handlers (examples in
xapp_tets.py).

Subscription REST interface
---------------------------

api/xapp_rest_api.yaml defines interface and it has been used to generate the swagger api calls.

Generating the swagger client model:
docker run --rm -v ${PWD}:/local -u $(id -u ${USER}):$(id -g ${USER}) swaggerapi/swagger-codegen-cli generate -i /local/api/xapp_rest_api.yaml -l python -o /local/out

swagger-codegen-cli generated code result needs to be adjusted to have the ricxappframe prefix. 
Replace the module name to have the ricxappframe prefix:

find ./out/swagger_client -type f -exec sed -i -e 's/swagger_client/ricxappframe\.swagger_client/g' {} \;

Then copy the generated ./out/swagger_client directory to ./ricxappframe/subsclient directory:

cp -r ./out/swagger_client/* ./ricxappframe/subsclient

Unit Testing
------------

Running the unit tests requires the python packages ``tox`` and ``pytest``.

The RMR library is also required during unit tests. If running directly from tox
(outside a Docker container), install RMR according to its instructions.

Upon completion, view the test coverage like this:

::

   tox
   open htmlcov/index.html

Alternatively, if you cannot install RMR locally, you can run the unit
tests in Docker. This is somewhat less nice because you don't get the
pretty HTML report on coverage.

::

   docker build  --no-cache -f Dockerfile-Unit-Test .
