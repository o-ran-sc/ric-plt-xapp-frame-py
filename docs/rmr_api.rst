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

.. py:class:: rmr_mbuf_t
   :module: ricxappframe.rmr.rmr


   Reimplementation of rmr_mbuf_t which is in an unaccessible header file (src/common/include/rmr.h)

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

   We do not include the fields we are not supposed to mess with

   RE PAYLOADs type below, see the documentation for c_char_p:
      class ctypes.c_char_p
          Represents the C char * datatype when it points to a zero-terminated string. For a general character pointer that may also point to binary data, POINTER(c_char) must be used. The constructor accepts an integer address, or a bytes object.













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

.. py:function:: rmr_init(uproto_port, max_msg_size, flags)
   :module: ricxappframe.rmr.rmr


   Refer to rmr C documentation for rmr_init
   extern void* rmr_init(char* uproto_port, int max_msg_size, int flags)

   This python function checks that the context is not None and raises
   an excption if it is.















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_ready(vctx)
   :module: ricxappframe.rmr.rmr


   Refer to rmr C documentation for rmr_ready
   extern int rmr_ready(void* vctx)
















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_close(vctx)
   :module: ricxappframe.rmr.rmr


   Refer to rmr C documentation for rmr_close
   extern void rmr_close(void* vctx)
















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_set_stimeout(vctx, time)
   :module: ricxappframe.rmr.rmr


   Refer to the rmr C documentation for rmr_set_stimeout
   extern int rmr_set_stimeout(void* vctx, int time)
















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_alloc_msg(vctx, size, payload=None, gen_transaction_id=False, mtype=None, meid=None, sub_id=None, fixed_transaction_id=None)
   :module: ricxappframe.rmr.rmr


   Refer to the rmr C documentation for rmr_alloc_msg
   extern rmr_mbuf_t* rmr_alloc_msg(void* vctx, int size)
   TODO: on next API break, clean up transaction_id ugliness. Kept for now to preserve API.

   if payload is not None, attempts to set the payload
   if gen_transaction_id is True, it generates and sets a transaction id. Note, fixed_transaction_id supersedes this option
   if mtype is not None, sets the sbuf's message type
   if meid is not None, sets the sbuf's meid
   if sub_id is not None, sets the sbud's subscription id
   if fixed_transaction_id is set, it deterministically sets the transaction_id. This overrides the option gen_transation_id















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_realloc_payload(ptr_mbuf, new_len, copy=False, clone=False)
   :module: ricxappframe.rmr.rmr


   Refer to the rmr C documentation for rmr_realloc_payload().
   extern rmr_mbuf_t* rmr_realloc_payload(rmr_mbuf_t*, int, int, int)
















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_free_msg(mbuf)
   :module: ricxappframe.rmr.rmr


   Refer to the rmr C documentation for rmr_free_msg
   extern void rmr_free_msg(rmr_mbuf_t* mbuf )
















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_payload_size(ptr_mbuf)
   :module: ricxappframe.rmr.rmr


   Refer to the rmr C documentation for rmr_payload_size
   extern int rmr_payload_size(rmr_mbuf_t* msg)
















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_send_msg(vctx, ptr_mbuf)
   :module: ricxappframe.rmr.rmr


   Refer to the rmr C documentation for rmr_send_msg
   extern rmr_mbuf_t* rmr_send_msg(void* vctx, rmr_mbuf_t* msg)
















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_rcv_msg(vctx, ptr_mbuf)
   :module: ricxappframe.rmr.rmr


   Refer to the rmr C documentation for rmr_rcv_msg
   extern rmr_mbuf_t* rmr_rcv_msg(void* vctx, rmr_mbuf_t* old_msg)
















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_torcv_msg(vctx, ptr_mbuf, ms_to)
   :module: ricxappframe.rmr.rmr


   Refer to the rmr C documentation for rmr_torcv_msg
   extern rmr_mbuf_t* rmr_torcv_msg(void* vctx, rmr_mbuf_t* old_msg, int ms_to)
















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_rts_msg(vctx, ptr_mbuf, payload=None, mtype=None)
   :module: ricxappframe.rmr.rmr


   Refer to the rmr C documentation for rmr_rts_msg
   extern rmr_mbuf_t*  rmr_rts_msg(void* vctx, rmr_mbuf_t* msg)

   additional features beyond c-rmr:
       if payload is not None, attempts to set the payload
       if mtype is not None, sets the sbuf's message type















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_call(vctx, ptr_mbuf)
   :module: ricxappframe.rmr.rmr


   Refer to the rmr C documentation for rmr_call
   extern rmr_mbuf_t* rmr_call(void* vctx, rmr_mbuf_t* msg)
















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_set_meid(ptr_mbuf, byte_str)
   :module: ricxappframe.rmr.rmr


   Refer to the rmr C documentation for rmr_bytes2meid
   extern int rmr_bytes2meid(rmr_mbuf_t* mbuf, unsigned char const* src, int len);

   Caution:  the meid length supported in an RMR message is 32 bytes, but C applications
   expect this to be a nil terminated string and thus only 31 bytes are actually available.

   Raises: exceptions.MeidSizeOutOfRang















   ..
       !! processed by numpydoc !!

.. py:function:: rmr_get_meid(ptr_mbuf)
   :module: ricxappframe.rmr.rmr


   Get the managed equipment ID (meid) from the message header.


   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer

   :Returns:

       string:
           meid













   ..
       !! processed by numpydoc !!

.. py:function:: rmr_get_src(ptr_mbuf, dest)
   :module: ricxappframe.rmr.rmr


   Refer to the rmr C documentation for rmr_get_src
   extern unsigned char*  rmr_get_src(rmr_mbuf_t* mbuf, unsigned char* dest);
















   ..
       !! processed by numpydoc !!

.. py:function:: get_payload(ptr_mbuf)
   :module: ricxappframe.rmr.rmr


   Given a rmr_buf_t*, get it's binary payload as a bytes object


   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer

   :Returns:

       bytes:
           the message payload













   ..
       !! processed by numpydoc !!

.. py:function:: get_xaction(ptr_mbuf)
   :module: ricxappframe.rmr.rmr


   given a rmr_buf_t*, get it's transaction id


   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer

   :Returns:

       bytes:
           the transaction id













   ..
       !! processed by numpydoc !!

.. py:function:: message_summary(ptr_mbuf)
   :module: ricxappframe.rmr.rmr


   Returns a dict that contains the fields of a message


   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer

   :Returns:

       dict:
           dict message summary













   ..
       !! processed by numpydoc !!

.. py:function:: set_payload_and_length(byte_str, ptr_mbuf)
   :module: ricxappframe.rmr.rmr


   | Set an rmr payload and content length
   | In place method, no return


   :Parameters:

       **byte_str: bytes**
           the bytes to set the payload to

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer














   ..
       !! processed by numpydoc !!

.. py:function:: generate_and_set_transaction_id(ptr_mbuf)
   :module: ricxappframe.rmr.rmr


   Generate a UUID and Set an rmr transaction id to it


   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer














   ..
       !! processed by numpydoc !!

.. py:function:: set_transaction_id(ptr_mbuf, tid_bytes)
   :module: ricxappframe.rmr.rmr


   Set an rmr transaction id
   TODO: on next API break, merge these two functions. Not done now to preserve API.


   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer

       **tid_bytes: bytes**
           bytes of the desired transaction id














   ..
       !! processed by numpydoc !!

.. py:function:: get_src(ptr_mbuf)
   :module: ricxappframe.rmr.rmr


   Get the message source (likely host:port)


   :Parameters:

       **ptr_mbuf: ctypes c_void_p**
           Pointer to an rmr message buffer

   :Returns:

       string:
           message source













   ..
       !! processed by numpydoc !!
