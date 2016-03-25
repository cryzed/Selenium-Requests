import socket
import threading
import time
import warnings

import requests
import six
import tldextract
from selenium.common.exceptions import NoSuchWindowException, TimeoutException, WebDriverException
from selenium.webdriver import Chrome
from six.moves import BaseHTTPServer
from six.moves.urllib.parse import urlparse

FIND_WINDOW_HANDLE_WARNING = (
    'Created window handle could not be found reliably. Using less reliable '
    'alternative method. JavaScript redirects are not supported and an '
    'additional GET request might be made for the requested URL.'
)

headers = None
update_headers_mutex = threading.Semaphore()
update_headers_mutex.acquire()


# Using a global value to pass around the headers dictionary reference seems to
# be the easiest way to get access to it, since the HTTPServer doesn't keep an
# object of the instance of the HTTPRequestHandler
class HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        global headers

        headers = requests.structures.CaseInsensitiveDict(self.headers if six.PY3 else self.headers.dict)
        update_headers_mutex.release()

        self.send_response(200)
        self.end_headers()

        # Immediately close the window as soon as it is loaded
        self.wfile.write(six.b('<script type="text/javascript">window.close();</script>'))

    # Suppress unwanted logging to stderr
    def log_message(self, format, *args):
        pass


def get_unused_port():
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_.bind(('', 0))
    address, port = socket_.getsockname()
    socket_.close()
    return port


def get_webdriver_request_headers(webdriver):
    # There's a small chance that the port was taken since the call of
    # get_unused_port(), so make sure we try as often as needed
    while True:
        port = get_unused_port()
        try:
            server = BaseHTTPServer.HTTPServer(('', port), HTTPRequestHandler)
            break
        except socket.error:
            pass

    threading.Thread(target=server.handle_request).start()
    original_window_handle = webdriver.current_window_handle
    webdriver.execute_script("window.open('http://127.0.0.1:%d/');" % port)

    update_headers_mutex.acquire()

    # Possibly optional: Make sure that the webdriver didn't switch the window
    # handle to the newly opened window. Behaviors of different webdrivers seem
    # to differ greatly here
    if webdriver.current_window_handle != original_window_handle:
        webdriver.switch_to.window(original_window_handle)

    global headers
    headers_ = headers
    headers = None

    # Remove the host header, which will simply contain the localhost address
    # of the HTTPRequestHandler instance
    del headers_['host']
    return headers_


def prepare_requests_cookies(webdriver_cookies):
    return dict((str(cookie['name']), str(cookie['value'])) for cookie in webdriver_cookies)


def get_tld(url):
    components = tldextract.extract(url)
    return components.registered_domain or url


def find_window_handle(webdriver, callback):
    original_window_handle = webdriver.current_window_handle
    if callback(webdriver):
        return original_window_handle

    # Start search beginning with the most recently added window handle, the
    # chance is higher that this is the correct one in most cases
    for window_handle in reversed(webdriver.window_handles):
        if window_handle == original_window_handle:
            continue

        # This exception can occur if the current window handle was closed
        try:
            webdriver.switch_to.window(window_handle)
        except NoSuchWindowException:
            continue

        if callback(webdriver):
            return window_handle

    # Simply switch back to the original window handle and return None if no
    # matching window handle was found
    webdriver.switch_to.window(original_window_handle)


def make_find_domain_condition(webdriver, requested_domain):
    def condition(webdriver):
        try:
            return get_tld(webdriver.current_url) == requested_domain

        # This exception can occur if the current window handle was closed
        except NoSuchWindowException:
            pass

    return condition


class RequestMixin(object):
    def request(self, method, url, find_window_handle_timeout=-1, page_load_timeout=-1, **kwargs):
        if not hasattr(self, '_seleniumrequests_session'):
            self._seleniumrequests_session = requests.Session()

            # Workaround for https://github.com/cryzed/Selenium-Requests/issues/2
            if isinstance(self, Chrome):
                window_handles_before = len(self.window_handles)
                self._seleniumrequests_session.headers = get_webdriver_request_headers(self)

                # Wait until the newly opened window handle is closed again, to
                # prevent switching to it just as it is about to be closed
                while len(self.window_handles) > window_handles_before:
                    pass

            else:
                self._seleniumrequests_session.headers = get_webdriver_request_headers(self)

            # Delete cookies from the request headers, to prevent overwriting
            # manually set cookies later. This should only happen when the
            # webdriver has cookies set for the localhost
            if 'cookie' in self._seleniumrequests_session.headers:
                del self._seleniumrequests_session.headers['cookie']

        original_window_handle = None
        opened_window_handle = None
        requested_tld = get_tld(url)
        if not get_tld(self.current_url) == requested_tld:
            original_window_handle = self.current_window_handle

            # Try to find an existing window handle that matches the requested
            # top-level domain
            condition = make_find_domain_condition(self, requested_tld)
            window_handle = find_window_handle(self, condition)

            # Create a new window handle manually in case it wasn't found
            if not window_handle:
                components = urlparse(url)

                previous_window_handles = set(self.window_handles)
                self.execute_script("window.open('%s://%s/');" % (components.scheme, components.netloc))
                difference = set(self.window_handles) - set(previous_window_handles)

                if len(difference) == 1:
                    opened_window_handle = tuple(difference)[0]

                    # Most WebDrivers will automatically wait until the
                    # switched-to window handle has finished loading
                    self.switch_to.window(opened_window_handle)
                else:
                    warnings.warn(FIND_WINDOW_HANDLE_WARNING)
                    opened_window_handle = find_window_handle(self, condition)

                    # Window handle could not be found during first pass.
                    # Either the WebDriver didn't wait for the page to load
                    # completely (PhantomJS) or there was a redirect and the
                    # top-level domain changed
                    if not opened_window_handle:
                        response = self._seleniumrequests_session.get(url, stream=True)
                        current_tld = get_tld(response.url)
                        if current_tld != requested_tld:
                            condition = make_find_domain_condition(self, current_tld)

                    # Some WebDrivers (PhantomJS) take some time until the new
                    # window handle has loaded
                    start = time.time()
                    while not opened_window_handle:
                        opened_window_handle = find_window_handle(self, condition)
                        if find_window_handle_timeout >= 0 and time.time() - start > find_window_handle_timeout:
                            raise TimeoutException('window handle could not be found')

        # Acquire WebDriver's cookies and merge them with potentially passed
        # cookies
        cookies = prepare_requests_cookies(self.get_cookies())
        if 'cookies' in kwargs:
            cookies.update(kwargs['cookies'])
        kwargs['cookies'] = cookies

        response = self._seleniumrequests_session.request(method, url, **kwargs)

        # Set cookies received from the HTTP response in the WebDriver
        for cookie in response.cookies:
            cookie_dict = {'name': cookie.name, 'value': cookie.value, 'secure': cookie.secure}
            if cookie.expires:
                cookie_dict['expiry'] = cookie.expires
            if cookie.path_specified:
                cookie_dict['path'] = cookie.path

            # Some WebDrivers (PhantomJS) take some time until the new window
            # handle has loaded and cookies can be set
            start = time.time()
            while page_load_timeout < 0 or time.time() - start <= page_load_timeout:
                try:
                    self.add_cookie(cookie_dict)
                    break
                except WebDriverException:
                    pass
            else:
                raise TimeoutException('page took too long to load')

        # Don't keep cookies in the Requests session, only use the WebDriver's
        self._seleniumrequests_session.cookies.clear()

        if opened_window_handle:
            self.close()

        if original_window_handle:
            self.switch_to.window(original_window_handle)

        return response
