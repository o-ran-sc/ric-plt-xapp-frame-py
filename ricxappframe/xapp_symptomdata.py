#       Copyright (c) 2022 Nokia
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
# Symptomdata collection is triggered from the trblmgr ricplt pod. This subsystem provides for xapp interface to subscribe the
# symptomdata collection via lwsd pod. When the symptomdata collection is triggered then the xapp gets the callback to collect
# the symptomdata.
#
# If the dynamic registration is needed, then the xapp needs to use the Symptomdata.subscribe(...) method to indicate symptomdata
# collection. In case the xapp is set to trblmgr config file then the registration is not needed.
#
# If the xapp has the internal data for symptomdata collection REST call response, it can use the helper methods getFileList and collect
# to get the needed files or readymade zipped package for reponse.
#
import os
import re
import time
import requests
import json
from requests.exceptions import HTTPError
from zipfile import ZipFile
from threading import Timer
from datetime import datetime
from mdclogpy import Logger

logging = Logger(name=__name__)


class RepeatTimer(Timer):
    # timer class for housekeeping and file rotating
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class Symptomdata(object):
    # service is the local POD service id, path the temporal storage, host should be the trblmgr service name
    def __init__(self, service="", servicehost="", path="/tmp/", lwsduri=None, timeout=30):
        """
        init

        Parameters
        ----------
        service: string
            xapp service name
        servicehost: string
            xapp service host name
        path:
            temporal path where the symptomdata collection is stored
        lwsduri:
            lwsd uri for symptomdata dynamic registration
        timeout:
            timeout for subscription status polling
        """
        if not os.path.exists(path):
            os.mkdir(path)
        self.service = service
        self.servicehost = servicehost
        self.path = path
        self.lwsduri = lwsduri
        self.timeout = timeout
        # runtime attrs
        self.zipfilename = None
        logging.info("Symptomdata init service:%s path:%s lwsduri:%s timeout:%d" % (self.service, self.path, self.lwsduri, self.timeout))
        if self.lwsduri is not None:
            # do the subscription, set to True so that first the query is triggered
            self.lwsdok = True
            self.subscribe(args=("",))
            self.subscribetimer = RepeatTimer(self.timeout, self.subscribe, args=("",))
            self.subscribetimer.start()

    # make the symptomdata subscription query to lwsd - dynamic registration (needed if the static config in trblmgr does not have xapp service data)
    def subscribe(self, args):
        """
        subscribe
            internally used subscription function if the dynamic registration has been set
        """
        if self.lwsduri is not None:
            try:
                proxies = {"http": "", "https": ""}    # disable proxy usage
                headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
                if self.lwsdok is False:
                    jsondata = json.dumps({'url': 'http://' + self.servicehost +
                                           ':8080/ric/v1/symptomdata', 'service': self.service, 'instance': '1'})
                    response = requests.post(self.lwsduri,
                                             data=jsondata,
                                             headers=headers,
                                             proxies=proxies)
                    logging.info("Symptomdata subscription success")
                    self.lwsdok = True
                elif self.lwsdok is True:
                    self.lwsdok = False
                    response = requests.get(self.lwsduri, headers=headers, proxies=proxies)
                    for item in response.json():
                        if item.get('service') == self.service:
                            logging.info("Symptomdata subscription request success")
                            self.lwsdok = True
                    if self.lwsdok is False:
                        logging.error("Symptomdata subscription missing")
                response.raise_for_status()
            except HTTPError as http_err:
                logging.error("Symptomdata subscription failed - http error : %s" % (http_err))
                self.lwsdok = False
            except Exception as err:
                logging.error("Symptomdata subscription failed - error : %s" % (err))
                self.lwsdok = False

    def stop(self):
        """
        stop
            stops the dynamic service registration/polling
        """
        if self.subscribetimer is not None:
            self.subscribetimer.cancel()

    def __del__(self):
        if self.subscribetimer is not None:
            self.subscribetimer.cancel()

    def getFileList(self, regex, fromtime, totime):
        """
        getFileList
            internal use only, get the matching files for collect method
        """
        fileList = []
        path, wc = regex.rsplit('/', 1)
        logging.info("Filtering path: %s using wildcard %s fromtime %d totime %d" % (path + '/', wc, fromtime, totime))
        try:
            for root, dirs, files in os.walk((path + '/')):
                for filename in files:
                    if re.match(wc, filename):
                        file_path = os.path.join(root, filename)
                        filest = os.stat(file_path)
                        if fromtime > 0:
                            logging.info("Filtering file time %d fromtime %d totime %d" % (filest.st_ctime, fromtime, totime))
                            if fromtime <= filest.st_ctime:
                                logging.info("Adding file time %d fromtime %d" % (filest.st_ctime, fromtime))
                                if totime > 0:
                                    if totime >= filest.st_ctime:
                                        fileList.append(file_path)
                                else:
                                    fileList.append(file_path)
                        elif totime > 0:
                            if totime >= filest.st_ctime:
                                logging.info("Filtering file time %d fromtime %d totime %d" % (filest.st_ctime, fromtime, totime))
                                fileList.append(file_path)
                        else:
                            fileList.append(file_path)

        except OSError as e:
            logging.error("System error %d" % (e.errno))
        return fileList

    def collect(self, zipfiletmpl, fileregexlist, fromtime, totime):
        """
        collect
            collects the symptomdata based on the file regular expression match and stored the symptomdata. Optionaly
            caller can use fromtime and totime to choose only files matching the access time

        Parameters
        ----------
        zipfiletmpl: string
            template for zip file name using the strftime format - ex: ``"symptomdata"+'-%Y-%m-%d-%H-%M-%S.zip'``
        fileregexlist: string array
            array for file matching - ex: ``('examples/*.csv',)``
        fromtime: integer
            time value seconds
        totime: integer
            time value seconds
        Returns
        -------
        string
            zipfile name
        """
        zipfilename = self.path + datetime.fromtimestamp(int(time.time())).strftime(zipfiletmpl)
        logging.info("Compressing files to symptomdata archive: %s" % (zipfilename))
        zipdata = ZipFile(zipfilename, "w")
        self.remove()
        self.zipfilename = None
        fileCnt = 0
        for fileregex in fileregexlist:
            logging.info("Compressing files using %s" % (fileregex))
            fileList = self.getFileList(fileregex, fromtime, totime)
            try:
                if len(fileList) > 0:
                    for file_path in fileList:
                        logging.info("Adding file %s to archive" % (file_path))
                        zipdata.write(file_path, file_path)
                        fileCnt += 1
            except OSError as e:
                logging.error("System error %d" % (e.errno))
        zipdata.close()
        if fileCnt > 0:
            self.zipfilename = zipfilename
        return self.zipfilename

    def read(self):
        """
        read
            reads the stored symptomdata file content

        Returns
        -------
        string
            zipfile name
        integer
            data lenght
        bytes
            bytes of the file data
        """
        data = None
        with open(self.zipfilename, 'rb') as file:
            data = file.read()
        return (self.zipfilename, len(data), data)

    def remove(self):
        if self.zipfilename is not None:
            os.remove(self.zipfilename)
