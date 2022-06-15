import os
import requests
from zipfile import ZipFile
from requests import Response as response
from ricxappframe.xapp_symptomdata import Symptomdata


def new_loaddata(*args, **kwargs):
    # Your custom testing override
    return ""


class MockResponse(object):
    def __init__(self, reponse, jsonout):
        self.status_code = response
        self.url = 'http://lwsd.ricplt:8089/ric/v1/lwsd'
        self.headers = {'Content-type': 'application/json'}
        self.jsonout = jsonout

    def json(self):
        return self.jsonout

    def raise_for_status(self):
        return self.status_code


class MockStat(object):
    def __init__(self, st_ctime=None):
        self.st_ctime = st_ctime


class MockOs(object):
    def __init__(self, walk=None, st_ctime=None):
        self.walkresp = walk
        self.st_ctime = st_ctime

    def walk(self, path):
        return self.walkresp

    def stat(self, filename):
        st = MockStat(self.st_ctime)
        return st


def test_symptomdata_subscribe(monkeypatch):
    def mock_requests_post(uri, data, headers, proxies):
        print("%s %s" % (uri, data))
        return MockResponse(200, [{'service': 'xapp.service'}])

    def mock_requests_get(uri, headers, proxies):
        print("%s" % (uri))
        return MockResponse(200, [])

    # mock the http get and post
    monkeypatch.setattr(requests, 'post', mock_requests_post)
    monkeypatch.setattr(requests, 'get', mock_requests_get)

    # this will return not found
    s = Symptomdata("xapp", "xapp.ricxapp.service", "tmp", "http://lwsd.ricplt:8089/ric/v1/lwsd")
    # stop timer loop
    s.stop()
    # make subscription
    s.subscribe(None)
    assert s.lwsdok is True


def test_symptomdata_subscribe_exists(monkeypatch):
    def mock_requests_get(uri, headers, proxies):
        print("%s" % (uri))
        return MockResponse(200, [{'service': 'xapp_other'}, {'service': 'xapp'}])

    # mock the http get
    monkeypatch.setattr(requests, 'get', mock_requests_get)

    # this will return not found
    s = Symptomdata("xapp", "xapp.ricxapp.service", "tmp", "http://lwsd.ricplt:8089/ric/v1/lwsd")
    # stop timer loop
    s.stop()
    assert s.lwsdok is True


def test_symptomdata_collect_time(monkeypatch):
    myos = MockOs(walk=[('mydir', (), ('file1.csv', 'file2.csv', 'file3.txt', 'file.json'))], st_ctime=1647502471)

    def mock_requests_get(uri, headers, proxies):
        return MockResponse(200, [{'service': 'xapp_other'}, {'service': 'xapp'}])

    def mock_os_walk(path):
        return myos.walk(path)

    def mock_os_stat(filename):
        return myos.stat(filename)

    def mock_zipfile_write(me, fromfile, tofile):
        return

    # mock the http get
    monkeypatch.setattr(requests, 'get', mock_requests_get)
    # mock the os walk
    monkeypatch.setattr(os, 'walk', mock_os_walk)
    # mock the os stat
    monkeypatch.setattr(os, 'stat', mock_os_stat)

    # mock the zipfile stat
    monkeypatch.setattr(ZipFile, 'write', mock_zipfile_write)

    # this will return not found
    s = Symptomdata("xapp", "xapp.ricxapp.service", "tmp", "http://lwsd.ricplt:8089/ric/v1/lwsd")
    # stop timer loop
    s.stop()
    assert s.lwsdok is True

    zipfile = s.collect("zipfile.zip", (r'/tmp/csv/.*\.csv', r'/tmp/json/.*\.json'), 1647502470, 1647502570)
    assert zipfile is not None


def test_symptomdata_collect(monkeypatch):
    myos = MockOs(walk=[('mydir', (), ('file1.csv', 'file2.csv', 'file3.txt', 'file.json'))], st_ctime=1647502471)

    def mock_requests_get(uri, headers, proxies):
        return MockResponse(200, [{'service': 'xapp_other'}, {'service': 'xapp'}])

    def mock_os_walk(path):
        return myos.walk(path)

    def mock_os_stat(filename):
        return myos.stat(filename)

    def mock_zipfile_write(me, fromfile, tofile):
        return

    # mock the http get
    monkeypatch.setattr(requests, 'get', mock_requests_get)
    # mock the os walk
    monkeypatch.setattr(os, 'walk', mock_os_walk)
    # mock the os stat
    monkeypatch.setattr(os, 'stat', mock_os_stat)

    # mock the zipfile stat
    monkeypatch.setattr(ZipFile, 'write', mock_zipfile_write)

    # this will return not found
    s = Symptomdata("xapp", "xapp.ricxapp.service", "tmp", "http://lwsd.ricplt:8089/ric/v1/lwsd")
    # stop timer loop
    s.stop()
    assert s.lwsdok is True

    zipfile = s.collect("zipfile.zip", ('/tmp/csv/.*.csv', '/tmp/json/.*.json'), 0, 0)
    assert zipfile is not None
