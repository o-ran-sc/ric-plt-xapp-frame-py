.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0
.. Copyright (C) 2020 AT&T Intellectual Property

RIC Alarm API
=============

Overview
--------

The xapp python framework provides an alarm feature in the python
subpackage `ricxappframe.alarm`.  This subpackage defines objects and
methods for creating, raising and clearing alarms.

The alarm feature reuses the `ricxappframe.rmr` subpackage for
transporting alarm messages. That in turn requires the RMR
shared-object library to be available in a system library that is
searched by default, usually something like /usr/local/lib.

The alarm feature sends messages using RMR message type
`RIC_ALARM_UPDATE` in the `ricxappframe.alarm.alarm` module, currently
value 13111. The Xapp's routing table must have one (or more) entries
for that message type.

The complete API for the Alarm feature appears below.


Example Usage
-------------

Alarms are created, raised and cleared using an `AlarmManager` as
shown below. The manager requires an RMR context at creation time.

.. code-block:: python

    from ricxappframe.alarm import alarm
    from ricxappframe.rmr import rmr

    rmr_context = rmr.rmr_init(b"4562", rmr.RMR_MAX_RCV_BYTES, 0x00)
    alarm_mgr = alarm.AlarmManager(rmr_context, "managed-object-id", "application-id")
    alarm3 = alarm_mgr.create_alarm(3, alarm.AlarmSeverity.DEFAULT, "identifying", "additional")
    success = alarm_mgr.raise_alarm(alarm3)



Alarm API
---------

.. automodule:: ricxappframe.alarm.alarm
    :members:


Alarm Messages
--------------

Alarm messages conform to the following JSON schema.

.. literalinclude:: ../ricxappframe/alarm/alarm-schema.json
  :language: JSON
