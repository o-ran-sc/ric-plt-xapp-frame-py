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

..
  Sphinx can generate API documentation by running Python to pull doc strings
  from the binding code using these Sphinx directives that are commented out:
         .. automodule:: ricxappframe.rmr.rmr
             :members:
  But that approach requires the RMR library to be installed, which is difficult
  to achieve at ReadTheDocs.io.  Instead, the RST below was generated and captured
  according to the method shown at
  https://stackoverflow.com/questions/2668187/make-sphinx-generate-rst-class-documentation-from-pydoc



.. py:module:: ricxappframe.rmr.rmr


..
    !! processed by numpydoc !!

.. py:data:: RMR_MAX_RCV_BYTES
   :module: ricxappframe.rmr.rmr
   :value: 65536


   Maximum size message to receive
















   ..
       !! processed by numpydoc !!

.. py:data:: RMRFL_MTCALL
   :module: ricxappframe.rmr.rmr
   :value: 2


   Multi-threaded initialization flag
















   ..
       !! processed by numpydoc !!

.. py:data:: RMRFL_NONE
   :module: ricxappframe.rmr.rmr
   :value: 0


   Empty flag
















   ..
       !! processed by numpydoc !!

.. py:data:: RMR_OK
   :module: ricxappframe.rmr.rmr
   :value: 0


   State constant for OK
















   ..
       !! processed by numpydoc !!

.. py:data:: RMR_ERR_TIMEOUT
   :module: ricxappframe.rmr.rmr
   :value: 12


   State constant for timeout
















   ..
       !! processed by numpydoc !!

.. py:data:: RMR_ERR_RETRY
   :module: ricxappframe.rmr.rmr
   :value: 10


   State constant for retry
















   ..
       !! processed by numpydoc !!

.. py:class:: rmr_mbuf_t
   :module: ricxappframe.rmr.rmr


   Mirrors public members of type rmr_mbuf_t from RMR header file src/common/include/rmr.h

   | typedef struct {
   |    int     state;          // state of processing
   |    int     mtype;          // message type
   |    int     len;            // length of data in the payload (send or received)
   |    unsigned char* payload; // transported data
   |    unsigned char* xaction; // pointer to fixed length transaction id bytes
   |    int sub_id;             // subscription id
   |    int      tp_state;      // transport state (a.k.a errno)
   |
   | these things are off limits to the user application
   |
   |    void*   tp_buf;         // underlying transport allocated pointer (e.g. nng message)
   |    void*   header;         // internal message header (whole buffer: header+payload)
   |    unsigned char* id;      // if we need an ID in the message separate from the xaction id
   |    int flags;              // various MFL (private) flags as needed
   |    int alloc_len;          // the length of the allocated space (hdr+payload)
   | } rmr_mbuf_t;

   RE PAYLOADs type below, see the documentation for c_char_p:
      class ctypes.c_char_p
           Represents the C char * datatype when it points to a zero-terminated string.
           For a general character pointer that may also point to binary data, POINTER(c_char)
           must be used. The constructor accepts an integer address, or a bytes object.













   :Attributes:

       **len**
           Structure/Union member

       **mtype**
           Structure/Union member

       **payload**
           Structure/Union member

       **state**
           Structure/Union member

       **sub_id**
           Structure/Union member

       **tp_state**
           Structure/Union member

       **xaction**
           Structure/Union member


   ..
       !! processed by numpydoc !!

.. py:function:: rmr_init(uproto_port: ctypes.c_char_p, max_msg_size: int, flags: int) -> ctypes.c_void_p
   :module: ricxappframe.rmr.rmr


   Prepares the environment for sending and receiving messages.
   Refer to RMR C documentation for method::

       extern void* rmr_init(char* uproto_port, int max_msg_size, int flags)

   This function raises an exception if the returned context is None.

   :Parameters:

       **uproto_port: c_char_p**
           Pointer to a buffer with the port number as a string; e.g., "4550"

       **max_msg_size: integer**
           Maximum message size to receive

       **flags: integer**
           RMR option flags

   :Returns:

       c_void_p:
           Pointer to RMR context













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_ready(vctx: ctypes.c_void_p) -> int
   :module: ricxappframe.rmr.rmr


   Checks if a routing table has been received and installed.
   Refer to RMR C documentation for method::

       extern int rmr_ready(void* vctx)

   :Parameters:

       **vctx: ctypes c_void_p**
           Pointer to RMR context

   :Returns:

       1 for yes, 0 for no
           ..













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_close(vctx: ctypes.c_void_p)
   :module: ricxappframe.rmr.rmr


   Closes the listen socket.
   Refer to RMR C documentation for method::

       extern void rmr_close(void* vctx)

   :Parameters:

       **vctx: ctypes c_void_p**
           Pointer to RMR context

   :Returns:

       None
           ..













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_set_stimeout(vctx: ctypes.c_void_p, rloops: int) -> int
   :module: ricxappframe.rmr.rmr


   Sets the configuration for how RMR will retry message send operations.
   Refer to RMR C documentation for method::

       extern int rmr_set_stimeout(void* vctx, int rloops)

   :Parameters:

       **vctx: ctypes c_void_p**
           Pointer to RMR context

       **rloops: int**
           Number of retry loops

   :Returns:

       0 on success, -1 on failure
           ..













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_alloc_msg(vctx: ctypes.c_void_p, size: int, payload=None, gen_transaction_id: bool = False, mtype=None, meid=None, sub_id=None, fixed_transaction_id=None)
   :module: ricxappframe.rmr.rmr


   Allocates and returns a buffer to write and send through the RMR library.
   Refer to RMR C documentation for method::

       extern rmr_mbuf_t* rmr_alloc_msg(void* vctx, int size)

   Optionally populates the message from the remaining arguments.

   TODO: on next API break, clean up transaction_id ugliness. Kept for now to preserve API.

   :Parameters:

       **vctx: ctypes c_void_p**
           Pointer to RMR context

       **size: int**
           How much space to allocate

       **payload: bytes**
           if not None, attempts to set the payload

       **gen_transaction_id: bool**
           if True, generates and sets a transaction ID.
           Note, option fixed_transaction_id overrides this option

       **mtype: bytes**
           if not None, sets the sbuf's message type

       **meid: bytes**
           if not None, sets the sbuf's meid

       **sub_id: bytes**
           if not None, sets the sbuf's subscription id

       **fixed_transaction_id: bytes**
           if not None, used as the transaction ID.
           Note, this overrides the option gen_transaction_id

   :Returns:

       c_void_p:
           Pointer to rmr_mbuf structure













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_realloc_payload(ptr_mbuf: ctypes.c_void_p, new_len: int, copy: bool = False, clone: bool = False)
   :module: ricxappframe.rmr.rmr


   Allocates and returns a message buffer large enough for the new length.
   Refer to RMR C documentation for method::

       extern rmr_mbuf_t* rmr_realloc_payload(rmr_mbuf_t*, int, int, int)

   :Parameters:

       **ptr_mbuf: c_void_p**
           Pointer to rmr_mbuf structure

       **new_len: int**
           Length

       **copy: bool**
           Whether to copy the original paylod

       **clone: bool**
           Whether to clone the original buffer

   :Returns:

       c_void_p:
           Pointer to rmr_mbuf structure













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_free_msg(ptr_mbuf: ctypes.c_void_p)
   :module: ricxappframe.rmr.rmr


   Releases the message buffer.
   Refer to RMR C documentation for method::

       extern void rmr_free_msg(rmr_mbuf_t* mbuf )

   :Parameters:

       **ptr_mbuf: c_void_p**
           Pointer to rmr_mbuf structure

   :Returns:

       None
           ..













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_payload_size(ptr_mbuf: ctypes.c_void_p) -> int
   :module: ricxappframe.rmr.rmr


   Gets the number of bytes available in the payload.
   Refer to RMR C documentation for method::

       extern int rmr_payload_size(rmr_mbuf_t* msg)

   :Parameters:

       **ptr_mbuf: c_void_p**
           Pointer to rmr_mbuf structure

   :Returns:

       int:
           Number of bytes available













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_send_msg(vctx: ctypes.c_void_p, ptr_mbuf: ricxappframe.rmr.rmr.LP_rmr_mbuf_t) -> ricxappframe.rmr.rmr.LP_rmr_mbuf_t
   :module: ricxappframe.rmr.rmr


   Sends the message according to the routing table and returns an empty buffer.
   Refer to RMR C documentation for method::

       extern rmr_mbuf_t* rmr_send_msg(void* vctx, rmr_mbuf_t* msg)

   :Parameters:

       **vctx: ctypes c_void_p**
           Pointer to RMR context

       **ptr_mbuf: c_void_p**
           Pointer to rmr_mbuf structure

   :Returns:

       c_void_p:
           Pointer to rmr_mbuf structure













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_rcv_msg(vctx: ctypes.c_void_p, ptr_mbuf: ricxappframe.rmr.rmr.LP_rmr_mbuf_t) -> ricxappframe.rmr.rmr.LP_rmr_mbuf_t
   :module: ricxappframe.rmr.rmr


   Waits for a message to arrive, and returns it.
   Refer to RMR C documentation for method::

       extern rmr_mbuf_t* rmr_rcv_msg(void* vctx, rmr_mbuf_t* old_msg)

   :Parameters:

       **vctx: ctypes c_void_p**
           Pointer to RMR context

       **ptr_mbuf: c_void_p**
           Pointer to rmr_mbuf structure

   :Returns:

       c_void_p:
           Pointer to rmr_mbuf structure













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_torcv_msg(vctx: ctypes.c_void_p, ptr_mbuf: ricxappframe.rmr.rmr.LP_rmr_mbuf_t, ms_to: int) -> ricxappframe.rmr.rmr.LP_rmr_mbuf_t
   :module: ricxappframe.rmr.rmr


   Waits up to the timeout value for a message to arrive, and returns it.
   Refer to RMR C documentation for method::

       extern rmr_mbuf_t* rmr_torcv_msg(void* vctx, rmr_mbuf_t* old_msg, int ms_to)

   :Parameters:

       **vctx: ctypes c_void_p**
           Pointer to RMR context

       **ptr_mbuf: c_void_p**
           Pointer to rmr_mbuf structure

       **ms_to: int**
           Time out value in milliseconds

   :Returns:

       c_void_p:
           Pointer to rmr_mbuf structure













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_rts_msg(vctx: ctypes.c_void_p, ptr_mbuf: ricxappframe.rmr.rmr.LP_rmr_mbuf_t, payload=None, mtype=None) -> ricxappframe.rmr.rmr.LP_rmr_mbuf_t
   :module: ricxappframe.rmr.rmr


   Sends a message to the originating endpoint and returns an empty buffer.
   Refer to RMR C documentation for method::

       extern rmr_mbuf_t* rmr_rts_msg(void* vctx, rmr_mbuf_t* msg)

   additional features beyond c-rmr:
       if payload is not None, attempts to set the payload
       if mtype is not None, sets the sbuf's message type

   :Parameters:

       **vctx: ctypes c_void_p**
           Pointer to an RMR context

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an RMR message buffer

       **payload: bytes**
           Payload

       **mtype: bytes**
           Message type

   :Returns:

       c_void_p:
           Pointer to rmr_mbuf structure













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_call(vctx: ctypes.c_void_p, ptr_mbuf: ricxappframe.rmr.rmr.LP_rmr_mbuf_t) -> ricxappframe.rmr.rmr.LP_rmr_mbuf_t
   :module: ricxappframe.rmr.rmr


   Sends a message, waits for a response and returns it.
   Refer to RMR C documentation for method::

       extern rmr_mbuf_t* rmr_call(void* vctx, rmr_mbuf_t* msg)

   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an RMR message buffer

   :Returns:

       c_void_p:
           Pointer to rmr_mbuf structure













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_set_meid(ptr_mbuf: ricxappframe.rmr.rmr.LP_rmr_mbuf_t, byte_str: bytes) -> int
   :module: ricxappframe.rmr.rmr


   Sets the managed entity field in the message and returns the number of bytes copied.
   Refer to RMR C documentation for method::

       extern int rmr_bytes2meid(rmr_mbuf_t* mbuf, unsigned char const* src, int len);

   Caution:  the meid length supported in an RMR message is 32 bytes, but C applications
   expect this to be a nil terminated string and thus only 31 bytes are actually available.

   Raises: exceptions.MeidSizeOutOfRang

   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an RMR message buffer

       **byte_tr: bytes**
           Managed entity ID value

   :Returns:

       int:
           number of bytes copied













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_get_meid(ptr_mbuf: ricxappframe.rmr.rmr.LP_rmr_mbuf_t) -> bytes
   :module: ricxappframe.rmr.rmr


   Gets the managed entity ID (meid) from the message header.
   This is a python-friendly version of RMR C method::

       extern unsigned char* rmr_get_meid(rmr_mbuf_t* mbuf, unsigned char* dest);

   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an RMR message buffer

   :Returns:

       bytes:
           Managed entity ID













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_get_src(ptr_mbuf: ricxappframe.rmr.rmr.LP_rmr_mbuf_t, dest: ctypes.c_char_p) -> ctypes.c_char_p
   :module: ricxappframe.rmr.rmr


   Copies the message-source information to the buffer.
   Refer to RMR C documentation for method::

       extern unsigned char* rmr_get_src(rmr_mbuf_t* mbuf, unsigned char* dest);

   :Parameters:

       **ptr_mbuf: ctypes POINTER(rmr_mbuf_t)**
           Pointer to an RMR message buffer

       **dest: ctypes c_char_p**
           Pointer to a buffer to receive the message source

   :Returns:

       string:
           message-source information













   ..
       !! processed by numpydoc !!

.. py:function:: get_payload(ptr_mbuf: ctypes.c_void_p) -> bytes
   :module: ricxappframe.rmr.rmr


   Gets the binary payload from the rmr_buf_t*.


   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer

   :Returns:

       bytes:
           the message payload













   ..
       !! processed by numpydoc !!

.. py:function:: get_xaction(ptr_mbuf: ctypes.c_void_p) -> bytes
   :module: ricxappframe.rmr.rmr


   Gets the transaction ID from the rmr_buf_t*.


   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer

   :Returns:

       bytes:
           the transaction id













   ..
       !! processed by numpydoc !!

.. py:function:: message_summary(ptr_mbuf: ctypes.c_void_p) -> dict
   :module: ricxappframe.rmr.rmr


   Returns a dict with the fields of an RMR message.


   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer

   :Returns:

       dict:
           dict message summary













   ..
       !! processed by numpydoc !!

.. py:function:: set_payload_and_length(byte_str: bytes, ptr_mbuf: ctypes.c_void_p)
   :module: ricxappframe.rmr.rmr


   Sets an rmr payload and content length.
   In place method, no return.


   :Parameters:

       **byte_str: bytes**
           the bytes to set the payload to

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer














   ..
       !! processed by numpydoc !!

.. py:function:: generate_and_set_transaction_id(ptr_mbuf: ctypes.c_void_p)
   :module: ricxappframe.rmr.rmr


   Generates a UUID and sets the RMR transaction id to it


   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer














   ..
       !! processed by numpydoc !!

.. py:function:: set_transaction_id(ptr_mbuf: ctypes.c_void_p, tid_bytes: bytes)
   :module: ricxappframe.rmr.rmr


   Sets an RMR transaction id
   TODO: on next API break, merge these two functions. Not done now to preserve API.


   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer

       **tid_bytes: bytes**
           bytes of the desired transaction id














   ..
       !! processed by numpydoc !!

.. py:function:: get_src(ptr_mbuf: ctypes.c_void_p) -> str
   :module: ricxappframe.rmr.rmr


   Gets the message source (likely host:port)


   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer

   :Returns:

       string:
           message source













   ..
       !! processed by numpydoc !!

