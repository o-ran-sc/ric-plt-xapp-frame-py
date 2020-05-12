.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0
.. Copyright (C) 2020 AT&T Intellectual Property

RMR Python Bindings
===================

Overview
--------

The xapp python framework package includes a python subpackage called
`rmr`.  This subpackage (`ricxappframe.rmr`) is a CTYPES wrapper
around the RMR shared library.  Most Xapp users will never use this
subpackage natively; however python apps that need access to the
low-level RMR API can use it.

Usage of this python package requires that the RMR shared-object
library is installed in a system library that is included in the
directories found by default, usually something like /usr/local/lib.

The RMR library man pages are available here: :doc:`RMR Man Pages <ric-plt-lib-rmr:index>`

RMR API
-------

.. automodule:: ricxappframe.rmr.rmr
    :members:


RMR Helper API
--------------

.. automodule:: ricxappframe.rmr.helpers
    :members:
