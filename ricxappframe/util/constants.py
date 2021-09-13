# ==================================================================================
#
#       Copyright (c) 2021 Samsung Electronics Co., Ltd. All Rights Reserved.
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
#
# ==================================================================================


class Constants:

    # xapp registration constants
    SERVICE_HTTP = "SERVICE_{}_{}_HTTP_PORT"
    SERVICE_RMR = "SERVICE_{}_{}_RMR_PORT"
    CONFIG_PATH = "/ric/v1/config"
    REGISTER_PATH = "http://service-{}-appmgr-http.{}:8080/ric/v1/register"
    DEREGISTER_PATH = "http://service-{}-appmgr-http.{}:8080/ric/v1/deregister"
    DEFAULT_PLT_NS = "ricplt"
    DEFAULT_XAPP_NS = "ricxapp"

    # message-type constants
    RIC_HEALTH_CHECK_REQ = 100
    RIC_HEALTH_CHECK_RESP = 101

    # environment variable with path to configuration file
    CONFIG_FILE_ENV = "CONFIG_FILE"
