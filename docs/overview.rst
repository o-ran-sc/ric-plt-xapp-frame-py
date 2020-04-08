.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0
.. Copyright (C) 2020 AT&T Intellectual Property

Framework Overview
==================

This library is a framework for writing Xapps in python.
There may or may not be many Xapps written in python; however rmr, sdl, and logging libraries all exist for python, and this framework brings them together.

There are (at the time of writing) two "kinds" of Xapps one can instantiate with this framework that model "push" (RMR Xapps) and "pull" (General Xapps), as described below.

RMR Xapps
---------
This class of Xapps are purely reactive to rmr; data is always "pushed" to it via rmr.
That is, every time the Xapp receives an rmr message, they do something, then wait for the next message to arrive, end never need to execute functionality at another time (if they do, use the next class).
This is represented by a series of callbacks that get registered to receive rmr message types.
Every time an rmr message arrives, the user callback for that message type is invoked, or if the user has not registered a callback for that type, their default callback (mandatory) is invoked.
An analogy of this is AWS Lambda: "execute this code every time an event comes in" (the code to execute can depend on the type of event).

General Xapps
-------------
In this class of Xapp the user simply provides a function that gets invoked, and typically that function has a `while (something)` in it.
If the function returns, the Xapp will stop.
In this type of Xapp, the Xapp must "pull" it's own data, typically from SDL, rmr (ie query another component for data), or other sources.
The framework is "lighter" in this case then the former; it sets up an SDL connection, an rmr thread, and then calls the client provided function.
This is to be used for Xapps that are not purely event driven.

RMR Threading in the framework
------------------------------
NOTE: this is an implementation detail!
We expose this for transparency but most users will not have to worry about this.

In both types of Xapp, the framework launches a seperate thread whose only job is to read from rmr and deposit all messages (and their summaries) into a thread safe queue.
When the client Xapp reads using the framework (this read is done by the framework itself in the RMR Xapp, but by the client in a general Xapp), the read is done from the queue.
The framework is implemented this way so that a long running client function (e.g., consume) cannot block rmr reads.
This is important because rmr is *not* a persistent message bus, if any rmr client does not read "fast enough", messages can be lost.
So in this framework the client code is not in the same thread as the rmr reads, so that long running client code can never lead to lost messages.

In the case of RMR Xapps, there are currently 3 potential threads; the thread that reads from rmr directly, and the user can optionally have the rmr queue read run in a thread, returning execution back to the user thread.
The default is only two threads however, where `.run` does not return back execution and the user code is "finished" at that point.

Healthchecks
------------
RMRXapps come with a default rmr healthcheck probe handler.
When the RMRXapp is sent an rmr healthcheck, it will check to see if the rmr thread is healthy (well it can't even reply if it's not!), and that the SDL connection is healthy.
The Xapp responds accordingly.
The user can override this default handler by registering a new callback to the appropriate message type.

General Xapps must handle healthchecks when they read their rmr mailbox, since there is no notion of handlers.

There is no http service (Currently) in the framework therefore there are no http healthchecks.

Examples
--------
There are two examples in the `examples` directory; `ping` which is a general Xapp, and `pong` which is an RMR Xapp.
Ping sends a message, pong receives the message and use rts to reply.
Ping then reads it's own mailbox and demonstrates other functionality.
The highlight to note is that `pong` is purely reactive, it only does anything when a message is received.
Ping uses a general that also happens to read it's rmr mailbox inside.
