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

import time
import os
from contextlib import suppress
from mdclogpy import Logger

from ricxappframe.util.constants import Constants
from ricxappframe.xapp_frame import RMRXapp

mdc_logger = Logger(name=__name__)
rmr_xapp_config = None
rmr_xapp_defconfig = None
rmr_xapp_noconfig = None
config_file_path = "/tmp/file.json"


def init_config_file():
    with open(config_file_path, "w") as file:
        file.write('{ "start" : "value" }')


def write_config_file():
    # generate an inotify/config event
    with open(config_file_path, "w") as file:
        file.write('{ "change" : "value2" }')

def default_rmr_handler(self, summary, sbuf):
        pass

def test_config_no_env(monkeypatch):
    init_config_file()
    monkeypatch.delenv(Constants.CONFIG_FILE_ENV, raising=False)

    config_event_seen = False

    def config_handler(self, json):
        nonlocal config_event_seen
        config_event_seen = True

    global rmr_xapp_noconfig
    rmr_xapp_noconfig = RMRXapp(default_rmr_handler, config_handler=config_handler, rmr_port=4652, use_fake_sdl=True)
    # in unit tests we need to thread here or else execution is not returned!
    rmr_xapp_noconfig.run(thread=True, rmr_timeout=1)

    write_config_file()
    # give the work loop a chance to timeout on RMR and process the config event
    time.sleep(3)
    assert not config_event_seen
    rmr_xapp_noconfig.stop()
    rmr_xapp_noconfig = None


def test_default_config_handler():
    """Just for coverage"""
    init_config_file()

    # listen port is irrelevant, no messages arrive
    global rmr_xapp_defconfig
    rmr_xapp_defconfig = RMRXapp(default_rmr_handler, rmr_port=4567, use_fake_sdl=True)
    # in unit tests we need to thread here or else execution is not returned!
    rmr_xapp_defconfig.run(thread=True, rmr_timeout=1)
    write_config_file()
    # give the work loop a chance to timeout on RMR and process the config event
    time.sleep(3)
    rmr_xapp_defconfig.stop()
    rmr_xapp_defconfig = None


def test_custom_config_handler():
    # point watcher at the file
    init_config_file()

    startup_config_event = False
    change_config_event = False

    def config_handler(self, json):
        mdc_logger.info("config_handler: json {}".format(json))
        nonlocal startup_config_event
        nonlocal change_config_event
        if "start" in json:
            startup_config_event = True
        if "change" in json:
            change_config_event = True

    # listen port is irrelevant, no messages arrive
    global rmr_xapp_config
    rmr_xapp_config = RMRXapp(default_rmr_handler, config_handler=config_handler, rmr_port=4567, use_fake_sdl=True)
    assert startup_config_event
    rmr_xapp_config.run(thread=True, rmr_timeout=1)  # in unit tests we need to thread here or else execution is not returned!
    write_config_file()
    # give the work loop a chance to timeout on RMR and process the config event
    time.sleep(3)
    assert change_config_event
    rmr_xapp_config.stop()
    rmr_xapp_config = None


def teardown_module():
    """
    this is like a "finally"; the name of this function is pytest magic
    safer to put down here since certain failures above can lead to pytest never returning
    for example if an exception gets raised before stop is called in any test function above,
    pytest will hang forever
    """
    os.remove(config_file_path)
    with suppress(Exception):
        if rmr_xapp_config:
            rmr_xapp_config.stop()
        if rmr_xapp_defconfig:
            rmr_xapp_defconfig.stop()
        if rmr_xapp_noconfig:
            rmr_xapp_noconfig.stop()
