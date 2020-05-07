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
message arrives, the appropriate callback is invoked.  An Xapp may
define and register a separate callback for each expected message
type.  Every Xapp must define a default callback function, which is
invoked when a message arrives for which no type-specific callback was
registered.  An analogy of this is AWS Lambda: "execute this code
every time an event comes in" (the code to execute can depend on the
type of event).

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
sets up an RMR thread and an SDL connection, then invokes the
client-provided function.

Threading in the Framework
--------------------------

RMR interactions are processed in a thread started by the framework.
This implementation detail is documented here for transparency, but
most users will not have to worry about this.

In both types of Xapp, the framework launches a separate thread whose
only job is to read from RMR and deposit all messages (and their
summaries) into a thread-safe queue.  When the client Xapp reads from
RMR using the framework (this read is done by the framework itself in
the RMR Xapp, but by the client in a general Xapp), the read is done
from the framework-managed queue.  The framework is implemented this
way so that a long-running client function (e.g., consume) will not
block RMR reads.  This is important because RMR is *not* a persistent
message bus, if an RMR client does not read fast enough, messages can
be lost.  So in this framework the client code is not in the same
thread as the RMR reads, to ensure that long-running client code will
not cause message loss.

In the case of RMR Xapps, there are currently 3 potential threads; the
thread that reads from RMR directly, and the user can optionally have
the RMR queue read run in a thread, returning execution back to the
user thread.  The default is only two threads however, where `.run`
does not return back execution and the user code is finished at that
point.

Healthchecks
------------

The framework provides a default RMR healthcheck probe handler for
reactive Xapps.  When an RMR healthcheck message arrives, this handler
checks that the RMR thread is healthy (of course the Xapp cannot even
reply if the thread is not healthy!), and that the SDL connection is
healthy.  The handler responds accordingly via RMA.  The Xapp can
override this probe handler by registering a new callback for the
appropriate message type.

The framework provides no healthcheck handler for general Xapps. Those
applications must handle healthcheck probe messages appropriately when
they read their RMR mailboxes.

There is no http service in the framework, so there is no support for
HTTP-based healthcheck probes, such as what a deployment manager like
Kubernetes may use.

Examples
--------

Two sample Xapps using this framework are provided in the `examples`
directory of the git repository.  The first, `ping`, is a general Xapp
that defines a main function that reads its RMR mailbox in addition to
other work.  The second, `pong`, is a reactive Xapp that only takes
action when a message is received.

To run a demonstration, build the Docker images for both examples
using the supplied Dockerfiles.  Then start the Pong container (the
listener) followed by the Ping container (the sender).  The Ping
application sends a message, the pong application receives the message
and use RMR's return-to-sender feature to reply.  Ping then reads its
own mailbox and demonstrates other functionality.
