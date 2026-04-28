<!--
SPDX-License-Identifier: CC-BY-4.0
Copyright (C) 2024 OpenInfra Foundation Europe. All rights reserved.
-->

# Contributing to xapp-frame-py

Thank you for contributing to the O-RAN-SC `ric-plt/xapp-frame-py`
project. Patches are submitted via Gerrit at
<https://gerrit.o-ran-sc.org/r/q/project:ric-plt/xapp-frame-py>.

This document captures contributor-facing constraints that are not
obvious from the source tree alone. For the formal commit conventions
and DCO requirements, see the project-wide `Commit Rules` published in
the O-RAN-SC documentation.

## Documentation builds and `autodoc_mock_imports`

The Sphinx documentation build (`tox -e docs`, also run by Read the
Docs) uses `sphinx.ext.autodoc` to generate API reference pages by
importing the `ricxappframe` package directly. The Read the Docs build
environment cannot run the package's normal runtime: the RMR C shared
library it wraps (`ricxappframe.rmr.rmrclib`) is not available, and
several of the package's third-party Python imports either are
unavailable on Python 3.13+ (for example, `ricsdl` transitively pulls
`hiredis 2.0.0`, whose source build relies on the removed `imp`
module) or are incompatible with autodoc's mock loader (for example,
the generated `*_pb2.py` modules under `ricxappframe.entities.rnib`,
or `ricxappframe.subsclient.api_client` which builds tuples from
`six.integer_types` at class definition time).

To work around all of these, `docs/conf.py` declares an explicit
`autodoc_mock_imports = [...]` list covering:

- The C-extension shim (`ricxappframe.rmr.rmrclib`)
- Internal subtrees that contain generated or legacy code which
  cannot tolerate mocking of their own dependencies
  (`ricxappframe.entities`, `ricxappframe.subsclient`)
- Every top-level third-party Python module imported by `ricxappframe`
  modules (`certifi`, `google`, `inotify`, `inotify_simple`,
  `mdclogpy`, `msgpack`, `requests`, `ricsdl`, `six`, `urllib3`)

### What this means for contributors

**If you add a new top-level third-party `import` to any module under
`ricxappframe/`, you must also add the top-level package name to
`autodoc_mock_imports` in `docs/conf.py`.** Otherwise the
documentation build will fail at autodoc-import time, and the failure
will be promoted to a hard error by `sphinx-build -W`.

The same rule applies if you add a new internal subtree that contains
generated code (for example, freshly generated protobuf bindings) or
legacy code that does class-level operations on its dependencies — in
those cases, mock the entire subtree (e.g. `ricxappframe.entities`)
rather than each of its third-party imports individually.

### Verifying locally

Before pushing a change that touches `ricxappframe/` or
`docs/conf.py`, run:

```bash
tox -e docs
```

The build must succeed with zero warnings (the project enforces
`-W` so that warnings become errors). If autodoc reports a missing
module, add the top-level name to `autodoc_mock_imports` in
`docs/conf.py` and re-run.

### Why mocks rather than installing the real dependencies?

Read the Docs builds run on a stock Linux container with a fresh
Python install and no access to the RMR shared library. Installing
the package's runtime requirements via `docs/requirements-docs.txt`
was the previous approach, but it broke on Python 3.13 once `ricsdl`
became uninstallable from source. Mocking is the supported Sphinx
mechanism for this situation; see the
[autodoc documentation on mock imports](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autodoc_mock_imports).

## Where else this is documented

- The decision to convert from runtime-install to mock-imports was
  raised on Gerrit as change
  [15624](https://gerrit.o-ran-sc.org/r/c/ric-plt/xapp-frame-py/+/15624)
  and is recorded as the `Fix(docs)` commit immediately preceding
  the Phase 1 RTD modernisation in this repository's history.
- The broader O-RAN-SC documentation modernisation programme (Phase 1
  baseline + Phase 2 redoc → openapi) is tracked under Gerrit topics
  [`docs-update`](https://gerrit.o-ran-sc.org/r/q/topic:docs-update)
  and
  [`docs-update-p2`](https://gerrit.o-ran-sc.org/r/q/topic:docs-update-p2).