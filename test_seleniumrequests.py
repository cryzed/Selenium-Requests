import json
import socket
import threading

from seleniumrequests import Firefox
from seleniumrequests.request import get_unused_port
from six.moves import BaseHTTPServer, http_cookies
import requests
import six


class EchoHeaderRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        # Python 2's HTTPMessage class contains the actual data in its
        # "dict"-attribute, whereas in Python 3 HTTPMessage is itself the
        # container. Treat headers as case-insensitive
        data = json.dumps(dict(self.headers) if six.PY3 else self.headers.dict)
        self.send_response(200)

        # Send JSON data in a header instead of the body field, because some
        # browsers add additional markup which is ugly to parse out
        self.send_header('Echo', data)
        self.end_headers()

        # This is needed so the WebDriver instance allows setting of cookies
        self.wfile.write(six.b('<html></html>'))

    # Suppress unwanted logging to stderr
    def log_message(self, format, *args):
        pass


# TODO: Preferably only use websites served by the localhost
def test_window_handling():
    webdriver = Firefox()
    webdriver.get('https://www.google.com/')
    webdriver.execute_script("window.open('https://www.facebook.com/');")

    original_window_handle = webdriver.current_window_handle
    original_window_handles = set(webdriver.window_handles)

    webdriver.request('GET', 'https://www.youtube.com/')

    # Make sure that the window handle was switched back to the original one
    # after making a request that caused a new window to open
    assert webdriver.current_window_handle == original_window_handle

    # Make sure that all additional window handles that were opened during the
    # request were closed again
    assert set(webdriver.window_handles) == original_window_handles

    webdriver.quit()


def test_headers():
    while True:
        port = get_unused_port()
        try:
            server = BaseHTTPServer.HTTPServer(('', port), EchoHeaderRequestHandler)
            break
        except socket.error:
            pass

    def handle_requests():
        while True:
            server.handle_request()

    threading.Thread(target=handle_requests, daemon=True).start()
    webdriver = Firefox()
    server_url = 'http://127.0.0.1:%d/' % port
    webdriver.get(server_url)

    # TODO: Add more cookie examples with additional fields, such as
    # expires, path, comment, max-age, secure, version, httponly
    cookies = (
        {'name': 'Hello', 'value': 'World'},
        {'name': 'Another', 'value': 'Cookie'}
    )

    for cookie in cookies:
        webdriver.add_cookie(cookie)

    response = webdriver.request('GET', server_url, headers={'Extra': 'Header'}, cookies={'Extra': 'Cookie'})
    sent_headers = requests.structures.CaseInsensitiveDict(json.loads(response.headers['Echo']))

    # These are the default headers sent for the Mozilla Firefox browser, it's
    # easier to simply check that the values are not empty instead of comparing
    # them to constants, since those would change frequently with each
    # iteration of the used browser. Additionally the existence of headers such
    # as Accept-Language and Referer confirms that these are not simply the
    # default headers sent by the requests library itself
    assert 'cookie' in sent_headers and sent_headers['cookie']
    assert 'accept' in sent_headers and sent_headers['accept']
    assert 'host' in sent_headers and sent_headers['host']
    assert 'connection' in sent_headers and sent_headers['connection']
    assert 'accept-language' in sent_headers and sent_headers['accept-language']
    assert 'accept-encoding' in sent_headers and sent_headers['accept-encoding']
    assert 'user-agent' in sent_headers and sent_headers['user-agent']
    assert 'referer' in sent_headers and sent_headers['referer']

    # Check if the additional header was sent as well
    assert 'extra' in sent_headers and sent_headers['extra'] == 'Header'

    cookies = http_cookies.SimpleCookie()
    cookies.load(sent_headers['Cookie'])

    assert 'Hello' in cookies and cookies['Hello'].value == 'World'
    assert 'Another' in cookies and cookies['Another'].value == 'Cookie'

    # Check if the additional cookie was sent as well
    assert 'Extra' in cookies and cookies['Extra'].value == 'Cookie'

    webdriver.quit()
