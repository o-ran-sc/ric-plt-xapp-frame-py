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

"""Structured logging library with Mapped Diagnostic Context

Outputs the log entries to standard out in structured format, json currently.
Severity based filtering.
Supports Mapped Diagnostic Context (MDC).

Set MDC pairs are automatically added to log entries by the library.
"""
from typing import TypeVar
from enum import IntEnum
import sys
import json
import time
import os
import inotify.adapters
import threading


class Level(IntEnum):
    """Severity levels of the log messages."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40


LEVEL_STRINGS = {Level.DEBUG: "DEBUG",
                 Level.INFO: "INFO",
                 Level.WARNING: "WARNING",
                 Level.ERROR: "ERROR"}


Value = TypeVar('Value', str, int)


class MDCLogger():
    """Initialize the mdclogging module.
    Calling of the function is optional. If not called, the process name
    (sys.argv[0]) is used by default.

    Keyword arguments:
    name -- name of the component. The name will appear as part of the log
            entries.
    """
    def __init__(self, name: str = sys.argv[0], level: Level = Level.ERROR):
        """Initialize a Logger instance.

            Keyword arguments:
            name -- name of the component. The name will appear as part of the
                    log entries.
        """
        self.procname = name
        self.current_level = level
        self.mdc = {}

    # Pass configmap_monitor = True to monitor configmap to change logs dynamically using configmap

    def mdclog_format_init(self, configmap_monitor=False):

        self.mdc = {"PID": "", "SYSTEM_NAME": "", "HOST_NAME": "", "SERVICE_NAME": "", "CONTAINER_NAME": "", "POD_NAME": ""}
        self.get_env_params_values()
        try:
            self.filename = os.environ['CONFIG_MAP_NAME']
            self.dirname = str(self.filename[:self.filename.rindex('/')])
            self.parse_file()

            if configmap_monitor:
                self.register_log_change_notify()

        except Exception as e:
            print("Unable to Add Watch on ConfigMap File", e)

    def _output_log(self, log: str):

        """Output the log, currently to stdout."""
        print(log)

    def log(self, level: Level, message: str):
        """Log a message.

        Logs the message with the given severity if it is equal or higher than
        the current logging level.

        Keyword arguments:
        level -- severity of the log message
        message -- log message
        """
        if level >= self.current_level:
            log_entry = {}
            log_entry["ts"] = int(round(time.time() * 1000))
            log_entry["crit"] = LEVEL_STRINGS[level]
            log_entry["id"] = self.procname
            log_entry["mdc"] = self.mdc
            log_entry["msg"] = message
            self._output_log(json.dumps(log_entry))

    def error(self, message: str):
        """Log an error message. Equals to log(ERROR, msg)."""
        self.log(Level.ERROR, message)

    def warning(self, message: str):
        """Log a warning message. Equals to log(WARNING, msg)."""
        self.log(Level.WARNING, message)

    def info(self, message: str):
        """Log an info message. Equals to log(INFO, msg)."""
        self.log(Level.INFO, message)

    def debug(self, message: str):
        """Log a debug message. Equals to log(DEBUG, msg)."""
        self.log(Level.DEBUG, message)

    def set_level(self, level: Level):
        """Set current logging level.

        Keyword arguments:
        level -- logging level. Log messages with lower severity will be
                 filtered.
        """
        try:
            self.current_level = Level(level)
        except ValueError:
            pass

    def get_level(self) -> Level:
        """Return the current logging level."""
        return self.current_level

    def add_mdc(self, key: str, value: Value):
        """Add a logger specific MDC.

        If an MDC with the given key exists, it is replaced with the new one.
        An MDC can be removed with remove_mdc() or clean_mdc().

        Keyword arguments:
        key -- MDC key
        value -- MDC value
        """
        self.mdc[key] = value

    def get_env_params_values(self):

        try:
            self.mdc['SYSTEM_NAME'] = os.environ['SYSTEM_NAME']
        except Exception:
            self.mdc['SYSTEM_NAME'] = ""

        try:
            self.mdc['HOST_NAME'] = os.environ['HOST_NAME']
        except Exception:
            self.mdc['HOST_NAME'] = ""

        try:
            self.mdc['SERVICE_NAME'] = os.environ['SERVICE_NAME']
        except Exception:
            self.mdc['SERVICE_NAME'] = ""

        try:
            self.mdc['CONTAINER_NAME'] = os.environ['CONTAINER_NAME']
        except Exception:
            self.mdc['CONTAINER_NAME'] = ""

        try:
            self.mdc['POD_NAME'] = os.environ['POD_NAME']
        except Exception:
            self.mdc['POD_NAME'] = ""
        try:
            self.mdc['PID'] = os.getpid()
        except Exception:
            self.mdc['PID'] = ""

    def update_mdc_log_level_severity(self, level):

        severity_level = Level.ERROR

        if(level == ""):
            print("Invalid Log Level defined in ConfigMap")
        elif((level.upper() == "ERROR") or (level.upper() == "ERR")):
            severity_level = Level.ERROR
        elif((level.upper() == "WARNING") or (level.upper() == "WARN")):
            severity_level = Level.WARNING
        elif(level.upper() == "INFO"):
            severity_level = Level.INFO
        elif(level.upper() == "DEBUG"):
            severity_level = Level.DEBUG

        self.set_level(severity_level)

    def parse_file(self):
        src = open(self.filename, 'r')
        level = ""
        for line in src:
            if 'log-level:' in line:
                level_tmp = str(line.split(':')[-1]).strip()
                level = level_tmp
                break
        src.close()
        self.update_mdc_log_level_severity(level)

    def monitor_loglevel_change_handler(self):
        i = inotify.adapters.Inotify()
        i.add_watch(self.dirname)
        for event in i.event_gen():
            if (event is not None) and ('IN_MODIFY' in str(event[1]) or 'IN_DELETE' in str(event[1])):
                self.parse_file()

    def register_log_change_notify(self):
        t1 = threading.Thread(target=self.monitor_loglevel_change_handler)
        t1.daemon = True
        try:
            t1.start()
        except (KeyboardInterrupt, SystemExit):
            # TODO: add cleanup handler
            # cleanup_stop_thread()
            sys.exit()

    def get_mdc(self, key: str) -> Value:
        """Return logger's MDC value with the given key or None."""
        try:
            return self.mdc[key]
        except KeyError:
            return None

    def remove_mdc(self, key: str):
        """Remove logger's MDC with the given key."""
        try:
            del self.mdc[key]
        except KeyError:
            pass

    def clean_mdc(self):
        """Remove all MDCs of the logger instance."""
        self.mdc = {}
