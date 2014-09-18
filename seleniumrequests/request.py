import BaseHTTPServer
import socket
import threading
import urlparse

import requests

_headers = None
_update_headers_mutex = threading.Semaphore()
_update_headers_mutex.acquire()


# Using a global value to pass around the headers dictionary reference seems to
# be the easiest way to get access to it, since the HTTPServer doesn't keep an
# object of the instance of the _HTTPRequestHandler
class _HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        global _headers
        _headers = self.headers.dict
        _update_headers_mutex.release()

        self.send_response(200)
        self.end_headers()
        self.wfile.write('<script type="text/javascript">window.close();</script>')

    # Suppress unwanted logging to stderr
    def log_message(*args, **kwargs):
        pass


def _get_unused_port():
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_.bind(('', 0))
    address, port = socket_.getsockname()
    socket_.close()
    return port


def _get_webdriver_request_headers(webdriver):
    port = _get_unused_port()

    # There's a small chance that the port was taken since the call of
    # _get_unused_port()
    while True:
        try:
            server = BaseHTTPServer.HTTPServer(('', port), _HTTPRequestHandler)
            break
        except socket.error:
            port = _get_unused_port()

    threading.Thread(target=server.handle_request).start()
    webdriver.execute_script("window.open('http://127.0.0.1:%d/');" % port)

    _update_headers_mutex.acquire()
    global _headers
    headers = _headers
    _headers = None

    del headers['host']
    return headers


def _prepare_requests_cookies(webdriver_cookies):
    return dict((str(cookie['name']), str(cookie['value'])) for cookie in webdriver_cookies)


def _get_domain(url):
    return '.'.join(urlparse.urlparse(url).netloc.rsplit('.', 2)[-2:])


def _find_window_handle(webdriver, callback):
    original_window_handle = webdriver.current_window_handle
    if callback(webdriver):
        return original_window_handle

    # Start search beginning with the most recently added window handle, the
    # chance is higher that this is the correct one in most cases
    window_handles = webdriver.window_handles[::-1]
    window_handles.remove(original_window_handle)
    for window_handle in window_handles:
        webdriver.switch_to.window(window_handle)
        if callback(webdriver):
            return window_handle

    # Simply switch back to the original window handle and return None by
    # default if no matching window handle was found
    webdriver.switch_to.window(original_window_handle)


def request(self, method, url, **kwargs):
    # Create a requests session object for this instance that sends the
    # webdriver's default request headers
    if not hasattr(self, '_seleniumrequests_request_headers'):
        self._betterselenium_request_headers = _get_webdriver_request_headers(self)

    headers = self._betterselenium_request_headers.copy()
    if 'headers' in kwargs:
        headers.update(kwargs['headers'])
    kwargs['headers'] = headers

    original_window_handle = None
    opened_window_handle = None
    requested_domain = _get_domain(url)
    if not _get_domain(self.current_url) == requested_domain:
        original_window_handle = self.current_window_handle

        # Try to find an existing window handle that matches the requested
        # domain
        condition = lambda webdriver: _get_domain(webdriver.current_url) == requested_domain
        window_handle = _find_window_handle(self, condition)

        # Create a new window handle manually in case it wasn't found
        if window_handle is None:
            components = urlparse.urlparse(url)
            self.execute_script("window.open('http://%s');" % components.netloc)
            opened_window_handle = _find_window_handle(self, condition)

            # Some webdrivers take some time until the new window handle has
            # loaded the correct URL
            while opened_window_handle is None:
                opened_window_handle = _find_window_handle(self, condition)

    # Acquire webdriver's instance cookies and merge them with potentially
    # passed cookies
    cookies = _prepare_requests_cookies(self.get_cookies())
    if 'cookies' in kwargs:
        cookies.update(kwargs['cookies'])
    kwargs['cookies'] = cookies

    response = requests.request(method, url, **kwargs)

    # Set cookies set by the HTTP response within the webdriver instance
    for cookie in response.cookies:
        cookie_dict = {'name': cookie.name, 'value': cookie.value, 'secure': cookie.secure}
        if cookie.expires is not None:
            cookie_dict['expiry'] = cookie.expires
        if cookie.path_specified:
            cookie_dict['path'] = cookie.path
        if cookie.domain_specified:
            cookie_dict['domain'] = cookie.domain
        self.add_cookie(cookie_dict)

    if opened_window_handle is not None:
        self.close()

    if original_window_handle is not None:
        self.switch_to.window(original_window_handle)

    return response
