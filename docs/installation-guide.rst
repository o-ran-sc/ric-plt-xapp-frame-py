.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0
.. Copyright (C) 2020 AT&T Intellectual Property


Installation Guide
==================

.. contents::
   :depth: 3
   :local:

Installation
------------

The `ricxappframe` is available in `PyPi <https://pypi.org/project/ricxappframe>`_ . Use pip to install the version you want.

Installing the ricxappframe does NOT install the underlying rmr system dependency.
The underlying dependencies are in C.
For information on how to install rmr itself, see here for `packages <https://wiki.o-ran-sc.org/pages/viewpage.action?pageId=3605041>`_ and here to install from `source <https://wiki.o-ran-sc.org/display/RICP/RMR+Building+From+Source>`_.
Alternatively, you can borrow a script (note, this file contains an rmr version that is subject to change!) in the `a1 <https://gerrit.o-ran-sc.org/r/gitweb?p=ric-plt/a1.git;a=blob;f=integration_tests/install_rmr.sh;h=70ee489ba2895ea67ca2c93ecefb2776ba2c9ff3;hb=78ba273b279a7e7af6dba811a29746b881a53a8e>`_ repo.
