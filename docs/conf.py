import os
import sys
from docs_conf.conf import *

# autodoc needs this to find the code
sys.path.insert(0, os.path.abspath("../"))

extensions = ["sphinx.ext.autodoc", "sphinx.ext.intersphinx", "sphinx.ext.viewcode", "numpydoc"]

# don't alphabetically order
autodoc_member_order = "bysource"

linkcheck_ignore = ["http://localhost.*", "http://127.0.0.1.*", "https://gerrit.o-ran-sc.org.*"]

# silence complaints from autodoc gen
nitpick_ignore = [
            ('py:class', 'ctypes.c_char_p'),
            ('py:class', 'ctypes.c_void_p'),
            ('py:class', 'ricxappframe.rmr.rmr.LP_rmr_mbuf_t'),
            ]

# RMR c library is not available in ReadTheDocs
autodoc_mock_imports = ['ricxappframe.rmr.rmrclib']

# Supports links to RMR man pages
branch = 'latest'
intersphinx_mapping['ric-plt-lib-rmr'] = ('https://docs.o-ran-sc.org/projects/o-ran-sc-ric-plt-lib-rmr/en/%s' % branch, None)
