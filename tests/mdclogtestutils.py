# Copyright (c) 2019 AT&T Intellectual Property.
# Copyright (c) 2018-2019 Nokia.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This source code is part of the near-RT RIC (RAN Intelligent Controller)
# platform project (RICP).
#
"""Helper functions for mdclogpy unit tests."""

import json


class TestMdcLogUtils():
    """Helper functions for unit tests."""

    @staticmethod
    def get_logs(call_args_list):
        """Return the logs as a list of strings from the call_args_list."""
        return [x[0][0] for x in call_args_list]

    @staticmethod
    def get_logs_as_json(call_args_list):
        """Return the logs as a list of json objects from the call_args_list."""
        return list(map(json.loads, TestMdcLogUtils.get_logs(call_args_list)))
