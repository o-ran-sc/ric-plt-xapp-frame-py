..
.. Copyright (c) 2019 AT&T Intellectual Property.
..
.. Copyright (c) 2019 Nokia.
..
.. Copyright (c) 2021 Samsung
..
.. Licensed under the Creative Commons Attribution 4.0 International
..
.. Public License (the "License"); you may not use this file except
..
.. in compliance with the License. You may obtain a copy of the License at
..
..
..     https://creativecommons.org/licenses/by/4.0/
..
..
.. Unless required by applicable law or agreed to in writing, documentation
..
.. distributed under the License is distributed on an "AS IS" BASIS,
..
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
..
.. See the License for the specific language governing permissions and
..
.. limitations under the License.
..
.. This source code is part of the near-RT RIC (RAN Intelligent Controller)
..
.. platform project (RICP).
..

MDCLogger
=========


Usage
-----

The library can be used in as shown below.


.. code:: bash

 ```python
   from ricappframe.logger.mdclogger import MDCLogger
   my_logger = MDCLogger()
   my_logger.mdclog_format_init(configmap_monitor=True)
   my_logger.error("This is an error log")
 ```

A program can create several logger instances.

mdclog_format_init() Adds the MDC log format with HostName, PodName, ContainerName, ServiceName,PID,CallbackNotifyforLogFieldChange

Pass configmap_monitor = False in mdclog_format_init() function to stop dynamic log level change based on configmap.

Logging Levels
--------------
.. code:: bash

 """Severity levels of the log messages."""
     DEBUG = 10
     INFO = 20
     WARNING = 30
     ERROR = 40

mdcLogger API's
---------------

1. Set current logging level

.. code:: bash

 def set_level(self, level: Level):

        Keyword arguments:
        level -- logging level. Log messages with lower severity will be filtered.

2. Return the current logging level

.. code:: bash

 def get_level(self) -> Level:

3. Add a logger specific MDC

.. code:: bash

 def add_mdc(self, key: str, value: Value):

        Keyword arguments:
        key -- MDC key
        value -- MDC value

4. Return logger's MDC value with the given key or None

.. code:: bash

 def get_mdc(self, key: str) -> Value:

5. Remove logger's MDC with the given key

.. code:: bash

 def remove_mdc(self, key: str):

6. Remove all MDCs of the logger instance.

.. code:: bash

 def clean_mdc(self):


7. Initialise Logging format: 

This api Initialzes mdclog print format using MDC Dictionary by extracting the environment variables in the calling process for “SYSTEM_NAME”, “HOST_NAME”, “SERVICE_NAME”, “CONTAINER_NAME”, “POD_NAME” & “CONFIG_MAP_NAME” mapped to HostName, ServiceName, ContainerName, Podname and Configuration-file-name of the services respectively.


.. code:: bash

 def mdclog_format_init(configmap_monitor=False):

        Keyword arguments:
        configmap_monitor -- Enables/Disables Dynamic log level change based on configmap
                          -- Boolean values True/False can be passed as per requirement.


