import json
import socket
import threading

from seleniumrequests import Firefox, Chrome, PhantomJS
from seleniumrequests.request import get_unused_port
from six.moves import BaseHTTPServer, http_cookies
import requests
import six


ENCODING = 'UTF-8'


class DummyRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(six.b('<html></html>'))

    # Suppress unwanted logging to stderr
    def log_message(self, format, *args):
        pass


class EchoHeaderRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        # Python 2's HTTPMessage class contains the actual data in its
        # "dict"-attribute, whereas in Python 3 HTTPMessage is itself the
        # container. Treat headers as case-insensitive
        data = json.dumps(dict(self.headers) if six.PY3 else self.headers.dict)
        self.send_response(200)

        # Send JSON data in a header instead of the body field, because some
        # browsers add additional markup which is ugly to parse out
        self.send_header('echo', data)
        self.end_headers()

        # This is needed so the WebDriver instance allows setting of cookies
        self.wfile.write(six.b('<html></html>'))

    # Suppress unwanted logging to stderr
    def log_message(self, format, *args):
        pass


class SetCookieRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        if 'set-cookie' in (self.headers if six.PY3 else self.headers.dict):
            self.send_header('set-cookie', 'some=cookie')

        self.end_headers()

        # This is needed so the WebDriver instance allows setting of cookies
        self.wfile.write(six.b('<html></html>'))

    # Suppress unwanted logging to stderr
    def log_message(self, format, *args):
        pass


def run_http_server(request_handler_class):
    while True:
        port = get_unused_port()
        try:
            server = BaseHTTPServer.HTTPServer(('', port), request_handler_class)
            break
        except socket.error:
            pass

    def run():
        while True:
            server.handle_request()

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()

    return 'http://127.0.0.1:%d/' % port


dummy_server = run_http_server(DummyRequestHandler)
echo_header_server = run_http_server(EchoHeaderRequestHandler)
set_cookie_server = run_http_server(SetCookieRequestHandler)


# TODO: Preferably only use websites served by the localhost
def make_window_handling_test(webdriver_class):
    def test_window_handling():
        webdriver = webdriver_class()
        webdriver.get(dummy_server)

        original_window_handle = webdriver.current_window_handle
        webdriver.execute_script("window.open('%s');" % dummy_server)
        original_window_handles = set(webdriver.window_handles)

        # We need a different domain here to test the correct behaviour. Using
        # localhost isn't fool-proof because the hosts file is editable, so
        # make the most reliable choice we can: Google
        webdriver.request('GET', 'http://google.com/')

        # Make sure that the window handle was switched back to the original
        # one after making a request that caused a new window to open
        assert webdriver.current_window_handle == original_window_handle

        # Make sure that all additional window handles that were opened during
        # the request were closed again
        assert set(webdriver.window_handles) == original_window_handles

        webdriver.quit()

    return test_window_handling


def make_headers_test(webdriver_class):
    def test_headers():
        webdriver = webdriver_class()

        # TODO: Add more cookie examples with additional fields, such as
        # expires, path, comment, max-age, secure, version, httponly
        cookies = (
            {'name': 'hello', 'value': 'world'},
            {'name': 'another', 'value': 'cookie'}
        )

        # Open the server URL with the WebDriver instance initially so we can
        # set custom cookies
        webdriver.get(echo_header_server)
        for cookie in cookies:
            webdriver.add_cookie(cookie)

        response = webdriver.request('GET', echo_header_server, headers={'extra': 'header'}, cookies={'extra': 'cookie'})
        sent_headers = requests.structures.CaseInsensitiveDict(json.loads(response.headers['echo']))

        # Simply assert that the User-Agent isn't requests' default one, which
        # means that it and the rest of the headers must have been overwritten
        assert sent_headers['user-agent'] != requests.utils.default_user_agent()

        # Check if the additional header was sent as well
        assert 'extra' in sent_headers and sent_headers['extra'] == 'header'

        cookies = http_cookies.SimpleCookie()

        # Python 2's Cookie module expects a string object, not Unicode
        cookies.load(sent_headers['cookie'] if six.PY3 else sent_headers['cookie'].encode(ENCODING))

        assert 'hello' in cookies and cookies['hello'].value == 'world'
        assert 'another' in cookies and cookies['another'].value == 'cookie'

        # Check if the additional cookie was sent as well
        assert 'extra' in cookies and cookies['extra'].value == 'cookie'

        webdriver.quit()

    return test_headers


def make_set_cookie_test(webdriver_class):
    def test_set_cookie():
        webdriver = webdriver_class()

        # Make sure that the WebDriver itself doesn't receive the Set-Cookie
        # header, instead the requests request should receive it and set it
        # manually within the WebDriver instance.
        webdriver.request('GET', set_cookie_server, headers={'set-cookie': ''})

        # Open the URL so that we can actually get the cookies
        webdriver.get(set_cookie_server)

        cookie = webdriver.get_cookies()[0]
        assert cookie['name'] == 'some' and cookie['value'] == 'cookie'

        webdriver.quit()

    return test_set_cookie


test_firefox_window_handling = make_window_handling_test(Firefox)
test_firefox_headers = make_headers_test(Firefox)
test_firefox_set_cookie = make_set_cookie_test(Firefox)

test_chrome_window_handling = make_window_handling_test(Chrome)
test_chrome_headers = make_headers_test(Chrome)
test_chrome_set_cookie = make_set_cookie_test(Chrome)

test_phantomjs_window_handling = make_window_handling_test(PhantomJS)
test_phantomjs_headers = make_headers_test(PhantomJS)
test_phantomjs_set_cookie = make_set_cookie_test(PhantomJS)
