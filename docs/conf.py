import os
import sys
from docs_conf.conf import *

# autodoc needs this to find the code
sys.path.insert(0, os.path.abspath("../"))

language = 'en'

extensions = ["sphinx.ext.autodoc", "sphinx.ext.intersphinx", "sphinx.ext.viewcode", "numpydoc"]

# don't alphabetically order
autodoc_member_order = "bysource"
# Tell numpydoc NOT to generate a list of class members to silence sphinx warnings like this:
# simple.py:docstring of simple.simple.Simple.rst:20:autosummary: stub file not found 'simple.simple.Simple.hello'. Check your autosummary_generate setting.
numpydoc_show_class_members = False

linkcheck_ignore = ["http://localhost.*", "http://127.0.0.1.*", "https://gerrit.o-ran-sc.org.*"]

# silence complaints from autodoc gen
nitpick_ignore = [
            ('py:class', 'ctypes.c_char_p'),
            ('py:class', 'ctypes.c_void_p'),
            ('py:class', 'ricxappframe.rmr.rmr.LP_rmr_mbuf_t'),
            ]

# Suppress unresolved cross-reference warnings (also raised outside nitpicky
# mode under -W) for auto-generated ctypes pointer types like
# 'ctypes.LP_rmr_mbuf_t', which Sphinx synthesises from POINTER(rmr_mbuf_t)
# in type signatures and cannot resolve to a real Python class.
suppress_warnings = ['ref.class']

# Mock all third-party runtime dependencies so that autodoc can import
# the package without installing them. This keeps docs/requirements-docs.txt
# free of runtime/build-only deps such as ricsdl (which transitively pulls
# hiredis 2.0.0, broken on Python 3.13+ due to the removed 'imp' module),
# inotify/inotify_simple, msgpack, mdclogpy, etc. The 'ricxappframe.rmr.rmrclib'
# entry remains because the RMR C shared library is not available in the
# Read the Docs build environment.
autodoc_mock_imports = [
    'ricxappframe.rmr.rmrclib',
    'ricxappframe.entities',
    'ricxappframe.subsclient',
    'certifi',
    'google',
    'inotify',
    'inotify_simple',
    'mdclogpy',
    'msgpack',
    'requests',
    'ricsdl',
    'six',
    'urllib3',
]

# Supports links to RMR man pages
branch = 'latest'
intersphinx_mapping['ric-plt-lib-rmr'] = ('https://docs.o-ran-sc.org/projects/o-ran-sc-ric-plt-lib-rmr/en/%s' % branch, None)
