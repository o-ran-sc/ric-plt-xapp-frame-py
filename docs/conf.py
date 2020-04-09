import os
import sys
from docs_conf.conf import *

sys.path.insert(0, os.path.abspath("../"))

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "numpydoc"]

# dont alphabetically order
autodoc_member_order = "bysource"

linkcheck_ignore = ["http://localhost.*", "http://127.0.0.1.*", "https://gerrit.o-ran-sc.org.*"]
nitpick_ignore = [
            ('py:class', 'ctypes.c_char_p'),
            ('py:class', 'ctypes.c_void_p'),
            ('py:class', 'ricxappframe.rmr.rmr.LP_rmr_mbuf_t'),
            ]

# RMR shared object is not available in ReadTheDocs
autodoc_mock_imports = ['ricxappframe.rmrclib.rmrclib']
