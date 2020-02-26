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
from setuptools import setup, find_packages

setup(
    name="ricxappframe",
    version="0.1.0",
    packages=find_packages(exclude=["tests.*", "tests"]),
    author="Tommy Carpenter",
    description="Xapp framework for python",
    url="https://gerrit.o-ran-sc.org/r/admin/repos/ric-plt/xapp-frame-py",
    install_requires=["msgpack", "rmr>=2.2.0, <3.0.0", "mdclogpy", "ricsdl>=2.0.3,<3.0.0"],
)
