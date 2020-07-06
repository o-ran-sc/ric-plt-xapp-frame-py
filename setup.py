# ==================================================================================
#       Copyright (c) 2020 Nokia
#       Copyright (c) 2020 AT&T Intellectual Property.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# ==================================================================================
from os.path import dirname, abspath, join as path_join
from setuptools import setup, find_packages

SETUP_DIR = abspath(dirname(__file__))


def _long_descr():
    """Yields the content of documentation files for the long description"""
    try:
        doc_path = path_join(SETUP_DIR, "docs/overview.rst")
        with open(doc_path) as f:
            return f.read()
    except FileNotFoundError:  # this happens during unit testing, we don't need it
        return ""


setup(
    name="ricxappframe",
    version="1.4.0",
    packages=find_packages(exclude=["tests.*", "tests"]),
    author="O-RAN Software Community",
    description="Xapp and RMR framework for python",
    url="https://gerrit.o-ran-sc.org/r/admin/repos/ric-plt/xapp-frame-py",
    install_requires=["inotify_simple", "msgpack", "mdclogpy", "ricsdl>=2.0.3,<3.0.0"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Telecommunications Industry",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Communications",
    ],
    python_requires=">=3.7",
    keywords="RIC xapp",
    license="Apache 2.0",
    data_files=[("", ["LICENSE.txt"])],
    long_description=_long_descr(),
    long_description_content_type="text/x-rst",
)
