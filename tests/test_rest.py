import requests
import ricxappframe.xapp_rest


def doGetRequest(url):
    proxies = {"http": "", "https": ""}    # disable proxy usage
    return requests.get(url, proxies=proxies)


def doDeleteRequest(url):
    proxies = {"http": "", "https": ""}    # disable proxy usage
    return requests.delete(url, proxies=proxies)


def doPostRequest(url, data):
    proxies = {"http": "", "https": ""}    # disable proxy usage
    return requests.post(url, data, proxies=proxies)


def respPostHandler(name, path, data, ctype):
    response = ricxappframe.xapp_rest.initResponse()
    response['payload'] = data.decode("utf-8")
    return response


def respGetHandler(name, path, data, ctype):
    response = ricxappframe.xapp_rest.initResponse()
    response['payload'] = ('{ "Testitem": "Testdata"}')
    return response


def respDeleteHandler(name, path, data, ctype):
    response = ricxappframe.xapp_rest.initResponse()
    response['payload'] = None
    response['status'] = 204
    return response


def respGetEmptyHandler(name, path, data, ctype):
    response = ricxappframe.xapp_rest.initResponse()
    response['payload'] = None
    response['status'] = 204
    return response


def test_subscribe(monkeypatch):

    server = ricxappframe.xapp_rest.ThreadedHTTPServer("127.0.0.1", 18088)
    # trick to get the own handler with defined
    server.handler.add_handler(server.handler, "GET", "get", "/ric/v1/subscriptions", respGetHandler)
    server.handler.add_handler(server.handler, "GET", "getempty", "/ric/v1/empty", respGetEmptyHandler)
    server.handler.add_handler(server.handler, "POST", "post", "/ric/v1", respPostHandler)
    server.handler.add_handler(server.handler, "DELETE", "delete", "/ric/v1/delete", respDeleteHandler)
    server.start()

    resp = doGetRequest('http://127.0.0.1:18088/ric/v1/subscriptions')
    assert resp.text == '{ "Testitem": "Testdata"}'
    assert resp.status_code == 200

    resp = doGetRequest('http://127.0.0.1:18088/ric/v1/empty')
    assert resp.text == ""
    assert resp.status_code == 204

    resp = doPostRequest('http://127.0.0.1:18088/ric/v1', '{"Testdataitem": "foobar"}')
    assert resp.text == '{"Testdataitem": "foobar"}'
    assert resp.status_code == 200

    resp = doDeleteRequest('http://127.0.0.1:18088/ric/v1/delete')
    assert resp.text == ""
    assert resp.status_code == 204
    # not found case
    resp = doGetRequest('http://127.0.0.1:18088/ricci/v1/subscriptions')
    assert resp.text == ""
    assert resp.status_code == 404
