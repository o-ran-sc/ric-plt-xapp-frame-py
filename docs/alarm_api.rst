.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0
.. Copyright (C) 2020 AT&T Intellectual Property

RIC Alarm API
=============

Overview
--------

The xapp python framework package includes a python subpackage called
`Alarm`.  This subpackage (`ricxappframe.alarm`) provides objects and
methods for defining and raising alarms, which are transmitted using
the RMR shared library.

Usage of this python package requires that the RMR shared-object
library is installed in a system library that is included in the
directories found by default, usually something like /usr/local/lib.

Alarm messages conform to the following JSON schema.

.. literalinclude:: ../ricxappframe/alarm/alarm-schema.json
  :language: JSON

Alarm API
---------

.. automodule:: ricxappframe.alarm.alarm
    :members:
