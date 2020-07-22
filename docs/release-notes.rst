.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0
.. Copyright (C) 2020 AT&T Intellectual Property

Release Notes
=============

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <http://keepachangelog.com/>`__
and this project adheres to `Semantic Versioning <http://semver.org/>`__.


[1.5.0] - 2020-07-10
--------------------
* Add Stats manager API (`RIC-381 <https://jira.o-ran-sc.org/browse/RIC-381>`_)


[1.4.0] - 2020-07-06
--------------------
* Revise Alarm manager to send via RMR wormhole (`RIC-529 <https://jira.o-ran-sc.org/browse/RIC-529>`_)


[1.3.0] - 2020-06-24
--------------------
* Add configuration-change API (`RIC-425 <https://jira.o-ran-sc.org/browse/RIC-425>`_)


[1.2.1] - 2020-06-22
--------------------
* Revise alarm message type (`RIC-514 <https://jira.o-ran-sc.org/browse/RIC-514>`_)


[1.2.0] - 2020-06-04
--------------------
* Extend RMR module to support wormhole methods
* Add alarm API (`RIC-380 <https://jira.o-ran-sc.org/browse/RIC-380>`_)


[1.1.2] - 2020-05-13
--------------------
* Extend and publish class and method documentation as user guide in RST


[1.1.1] - 2020-05-07
--------------------
* Use timeout on queue get method to avoid 100% CPU usage (`RIC-354 <https://jira.o-ran-sc.org/browse/RIC-354>`_)
* Upgrade to RMR version 4.0.5


[1.1.0] - 2020-05-06
--------------------
* Use RMR timeout on receive to avoid 100% CPU usage (`RIC-354 <https://jira.o-ran-sc.org/browse/RIC-354>`_)
* Publish message-summary dict keys as constants to avoid hardcoding strings
* Add wrapper and test for RMR method rmr_set_vlevel(int)


[1.0.3] - 2020-04-29
--------------------
* Upgrade to RMR version 4.0.2


[1.0.2] - 2020-04-22
--------------------
* Upgrade to RMR version 3.8.0


[1.0.1] - 2020-04-10
--------------------
* Publish API documentation using Sphinx autodoc, which required
  changes so Sphinx can run when the RMR .so file is not available,
  such as during a ReadTheDocs build.
* Create new subpackage rmr/rmrclib with the C library loaded via
  ctypes.
* Extend sphinx configuration to mock the new rmrclib subpackage
* Add method to get constants from RMR library and detect mock
  objects to work around a bug in Sphinx 3.0.0.
* Split test files into test_rmr and test_rmrclib.
* Add function to define argtype and restype values for library functions
* Configure intersphinx link for RMR man pages at ReadTheDocs.io


[1.0.0] - 4/6/2020
------------------
* Python rmr has been moved into this repo. The module name has NOT
  changed in order to make the transition for repos very easy. The
  only transition needed should be prefixing rmr with ricxappframe in
  import statements, and to include this rather than rmr in setup.


[0.7.0] - 4/2/2020
------------------
* RMRXapps by default now implement the rmr healthcheck probe;
  users can also override it with a more complex handler if they
  wish
* Fix a bug in the unit tests where a payload mismatch wouldn't
  actually fail the test (would now)


[0.6.0] - 3/23/2020
-------------------
* Switch to SI95 for rmr


[0.5.0] - 3/18/2020
-------------------
* All xapps (via the base class) now have a logger attribute that can
  be invoked to provide mdc logging. It is a passthrough to the RIC
  mdc logger for python (untouched, no value in an API on top at the
  current time).


[0.4.1] - 3/17/2020
-------------------
* Switch tox to use py38
* switch to latest builders


[0.4.0] - 3/13/2020
-------------------
* Minor breaking change; switches the default behavior RE
  threading for RMRXapps. The default is not to return execution,
  but the caller (in `run`) can choose to loop in a thread.
* Add Dockerized examples


[0.3.0] - 3/10/2020
-------------------
* Large change to the "feel" of this framework: rather than subclass
  instantiation, xapps now use initialization and registration
  functions to register handlers
* rmr xapps can now register handlers for specific message types (and
  they must prodive a default callback); if the user does this then
  "message to function routing" is now handled by the framework itself
* RMRXapp now runs the polling loop in a thread, and returns execution
  back to the caller. The user is then free to loop, or do nothing,
  and call stop() when they want.
* Raises tox coverage minimum to 70 from 50 (currently at 86)


[0.2.0] - 3/3/2020
------------------
* now allows for RMRXapps to call code before entering the infinite
  loop
* stop is now called before throwing NotImplemented in the case where
  the client fails to provide a must have callback; this ensures there
  is no dangling rmr thread
* stop now calls rmr_close to correctly free up any port(s)
* (breaking) renames `loop` to `entrypoint` since the function does
  not have to contain a loop (though it most likely does)
* Changes wording around the two types of xapps (docs only)
* Uses a new version of rmr python that crashes when the rmr mrc fails
  to init, which prevents an xapp trying to use an unusable rmr
* more unit test code coverage
* Adds more fields to setup like long_desc and classifiers so the pypi
  page looks nicer
* Removes a bad release file (will be added back in subseq. commit)


[0.1.0] - 2/27/2020
-------------------
* Initial commit
