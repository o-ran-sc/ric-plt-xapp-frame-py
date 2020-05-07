.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0
.. Copyright (C) 2020 AT&T Intellectual Property

Framework Overview
==================

This package is a framework for writing Xapps in python. The framework
reduces the amount of code required in an Xapp by providing common
features needed by all Python-based Xapps including communication with
the RIC message router (RMR) and the Shared Data Layer (SDL).

The framework was designed to suport many types of Xapps, including
applications that are purely reactive to RMR messages, and
applications that initiate actions according to other criteria. 

Reactive Xapps
--------------

A reactive Xapp acts on messages that are delivered (pushed) via RMR.
The Xapp only takes action upon receipt of an RMR message. The Xapp
never takes action at another time.

This type of application is constructed by creating callback functions
and registering them with the framework by message type.  When an RMR
message arrives, the appropriate callback is invoked.  An Xapp can
define and register a callback for every expected message type.  Every
Xapp must define at least one callback function, the default callback,
which is called when a message type arrives for which no specific
callback was registered.  An analogy of this is AWS Lambda: "execute
this code every time an event comes in" (the code to execute can
depend on the type of event).

General Xapps
-------------

A general Xapp acts according to its own criteria, which may include
receipt of RMR messages.

This type of application is constructed by creating a function that
gets invoked by the framework.  Typically that function contains a
`while (something)` event loop.  If the function returns, the Xapp
stops.  In this type of Xapp, the Xapp must fetch its own data, either
from RMR, SDL or other source.  The framework does less work for a
general application compared to a reactive application.  The framework
sets up an RMR thread and an SDL connection, then invokes the client
provided function.  This is appropriate for Xapps that are not purely
event driven.

Threading in the Framework
--------------------------

RMR interactions are processed in a thread started by the framework.
This implementation detail is documented here for transparency, but
most users will not have to worry about this.

In both types of Xapp, the framework launches a seperate thread whose
only job is to read from RMR and deposit all messages (and their
summaries) into a thread safe queue.  When the client Xapp reads using
the framework (this read is done by the framework itself in the RMR
Xapp, but by the client in a general Xapp), the read is done from the
queue.  The framework is implemented this way so that a long-running
client function (e.g., consume) cannot block RMR reads.  This is
important because RMR is *not* a persistent message bus, if any RMR
client does not read fast enough, messages can be lost.  So in this
framework the client code is not in the same thread as the RMR reads,
so that long running client code can never lead to lost messages.

In the case of RMR Xapps, there are currently 3 potential threads; the
thread that reads from RMR directly, and the user can optionally have
the RMR queue read run in a thread, returning execution back to the
user thread.  The default is only two threads however, where `.run`
does not return back execution and the user code is finished at that
point.

Healthchecks
------------

RMR Xapps come with a default RMR healthcheck probe handler.  When the
RMRXapp is sent an RMR healthcheck, it will check to see if the RMR
thread is healthy (of course it can't even reply if it's not!), and
that the SDL connection is healthy.  The Xapp responds accordingly.
The user can override this default handler by registering a new
callback to the appropriate message type.

General Xapps must handle healthchecks when they read their RMR
mailbox, since there is no notion of handlers.

There is no http service in the framework therefore there are no http
healthchecks.

Examples
--------

There are two sample Xapps that use this framework in the `examples`
directory.  The first `ping`, is a general Xapp that defines a main
function that reads its RMR mailbox in addition to other work.  The
second, `pong`, is a reactive Xapp that only takes action when a
message is received.

To run a demonstration, build the Docker images for both examples
using the supplied Dockerfiles.  Then start the Pong container (the
listener) followed by the Ping container (the sender).  The Ping
application sends a message, the pong application receives the message
and use RMR's return-to-sender feature to reply.  Ping then reads its
own mailbox and demonstrates other functionality.
