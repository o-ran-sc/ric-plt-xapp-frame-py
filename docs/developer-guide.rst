.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0

Developer Guide
===============

.. contents::
   :depth: 3
   :local:

Version bumping the framework
-----------------------------

This project follows semver. When changes are made, the versions are in:

1) ``docs/release-notes.rst``

2) ``setup.py``

Version bumping RMR
-------------------

These items in this repo must be kept in sync:
* Dockerfile-Unit-Test
* examples/Dockerfile-Ping
* examples/Dockerfile-Pong
* ``rmr-version.yaml`` controls what rmr gets installed for unit testing in Jenkins


Unit Testing
------------

You can run the unit tests in Docker to avoid installing RMR locally:

::

   docker build -f Dockerfile-Unit-Test .
