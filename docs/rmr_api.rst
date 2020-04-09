RMR Python Bindings
===================

Overview
--------

The xapp python framework repository includes a python submodule
called `rmr`.  This package (`ricxappframe.rmr`) is a CTYPES wrapper
around the RMR shared library.  Most Xapp users will never use this
package natively; however python apps that need access to the low
level RMR API can use this package.  Usage of this python package
requires that you have the RMR shared-object library installed.


RMR API
-------

.. automodule:: ricxappframe.rmr.rmr
    :members:


RMR Helper API
--------------

.. automodule:: ricxappframe.rmr.helpers
    :members:
