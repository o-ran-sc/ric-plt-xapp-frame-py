User Guide
==========

This document explains how to develop an Xapp using the RIC Xapp framework.
Information for maintainers of this framework is in the Developer Guide.


Xapp writers should use the public classes and methods from the Xapp Python
framework package as documented below.


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
