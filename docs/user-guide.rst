.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0
.. Copyright (C) 2020 AT&T Intellectual Property

User Guide
==========

This document explains how to develop an Xapp using the RIC Xapp framework.
Information for maintainers of this framework is in the Developer Guide.

Xapp writers should use the public classes and methods from the Xapp Python
framework package as documented below.


Class _BaseXapp
---------------

Although this base class should not be used directly, it is inherited by
the public classes shown below and all of this class's public methods are
available for use by application writers.

.. autoclass:: ricxappframe.xapp_frame._BaseXapp
    :members:


Class RMRXapp
-------------

Application writers should extend this class to implement a reactive Xapp;
also see class Xapp.

.. autoclass:: ricxappframe.xapp_frame.RMRXapp
    :members:

Class Xapp
----------

Application writers should extend this class to implement a general Xapp;
also see class RMRXapp.

.. autoclass:: ricxappframe.xapp_frame.Xapp
    :members:


Class SDLWrapper
----------------

Application writers may instantiate this class directly to communicate with the SDL service.

.. autoclass:: ricxappframe.xapp_sdl.SDLWrapper
    :members:

Class Symptomdata
-----------------

Application writers may instantiate this class directly to communicate with the symptomdata service.

.. autoclass:: ricxappframe.xapp_symptomdata.Symptomdata
    :members:

Class NewSubscriber
-------------------

Application writers may instantiate this class directly to communicate REST based subscriptions.

.. autoclass:: ricxappframe.xapp_subscribe.NewSubscriber
    :members:

Class RestHandler
-----------------

Application writers may instantiate this class directly to have the xapp REST server service.

.. autoclass:: ricxappframe.xapp_rest.RestHandler
    :members:
