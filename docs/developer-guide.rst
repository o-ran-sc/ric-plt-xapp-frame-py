.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0
.. Copyright (C) 2020 AT&T Intellectual Property

Developer Guide
===============

This document explains how to maintain the RIC Xapp framework.
Information for users of this framework (i.e., Xapp developers) is in the User Guide.

Tech Stack
----------

The framework requires Python version 3.7 or later, and depends on
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
