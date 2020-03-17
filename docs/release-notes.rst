.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0
.. Copyright (C) 2020 AT&T Intellectual Property

Release Notes
===============

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <http://keepachangelog.com/>`__
and this project adheres to `Semantic Versioning <http://semver.org/>`__.

.. contents::
   :depth: 3
   :local:

[0.4.1] - 3/17/2020
-------------------
::

    * Switch tox to use py38
    * switch to latest builders


[0.4.0] - 3/13/2020
-------------------
::

    * minor breaking change; switches the default behavior RE threading for RMRXapps. The default is not to return execution, but the caller (in `run`) can choose to loop in a thread.
    * Add Dockerized examples


[0.3.0] - 3/10/2020
-------------------
::

    * Large change to the "feel" of this framework: rather than subclass instantiation, xapps now use initialization and registration functions to register handlers
    * rmr xapps can now register handlers for specific message types (and they must prodive a default callback); if the user does this then "message to function routing" is now handled by the framework itself
    * RMRXapp now runs the polling loop in a thread, and returns execution back to the caller. The user is then free to loop, or do nothing, and call stop() when they want.
    * Raises tox coverage minimum to 70 from 50 (currently at 86)

[0.2.0] - 3/3/2020
-------------------
::

    * now allows for RMRXapps to call code before entering the infinite loop
    * stop is now called before throwing NotImplemented in the case where the client fails to provide a must have callback; this ensures there is no dangling rmr thread
    * stop now calls rmr_close to correctly free up any port(s)
    * (breaking) renames `loop` to `entrypoint` since the function does not have to contain a loop (though it most likely does)
    * Changes wording around the two types of xapps (docs only)
    * Uses a new version of rmr python that crashes when the rmr mrc fails to init, which prevents an xapp trying to use an unusable rmr
    * more unit test code coverage
    * Adds more fields to setup like long_desc and classifiers so the pypi page looks nicer
    * Removes a bad release file (will be added back in subseq. commit)

[0.1.0] - 2/27/2020
-------------------
::

    * Initial commit
