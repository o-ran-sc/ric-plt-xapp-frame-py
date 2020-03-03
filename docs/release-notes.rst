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

[0.2.0] - 3/3/2020
-------------------
::

    * now allows for RMR Xapps to call code before entering the infinite loop
    * stop is now called before throwing NotImplemented in the case where the client fails to provide a must have callback
    * (breaking) renames loop to entrypoint for "general" xapps
    * Changes wording around the two types of xapps (docs only)
    * more unit test code coverage
    * Removes a bad release file (will be added back in subseq. commit)

[0.1.0] - 2/27/2020
-------------------
::

    * Initial commit
