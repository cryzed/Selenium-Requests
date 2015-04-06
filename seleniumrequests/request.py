import socket
import threading
import time
import warnings

from selenium.common.exceptions import NoSuchWindowException, TimeoutException, WebDriverException
from six.moves import BaseHTTPServer
from six.moves.urllib.parse import urlparse
import requests
import six
import tld


FIND_WINDOW_HANDLE_WARNING = (
    'Created window handle could not be found reliably. Using less reliable '
    'alternative method. JavaScript redirects are not supported and an '
    'additional GET request might be made to the requested domain.'
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

        # Python 2's HTTPMessage class contains the actual data in its
        # "dict"-attribute, whereas in Python 3 HTTPMessage is itself the
        # container. Treat headers as case-insensitive
        headers = requests.structures.CaseInsensitiveDict(self.headers if six.PY3 else self.headers.dict)
        update_headers_mutex.release()

        self.send_response(200)
        self.end_headers()

        # Immediately close the window again as soon as it is loaded
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
    # get_unused_port()
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

    # Remove the Host-header which will simply contain the localhost address of
    # the HTTPRequestHandler instance
    del headers_['host']
    return headers_


def prepare_requests_cookies(webdriver_cookies):
    return dict((str(cookie['name']), str(cookie['value'])) for cookie in webdriver_cookies)


def get_domain(url):
    try:
        domain = tld.get_tld(url)
    except (tld.exceptions.TldBadUrl, tld.exceptions.TldDomainNotFound):
        return url

    return domain


def find_window_handle(webdriver, callback):
    original_window_handle = webdriver.current_window_handle
    if callback(webdriver):
        return original_window_handle

    # Start search beginning with the most recently added window handle, the
    # chance is higher that this is the correct one in most cases
    for window_handle in reversed(webdriver.window_handles):
        if window_handle == original_window_handle:
            continue

        # It's possible that one of the valid window handles is closed during
        # checking
        try:
            webdriver.switch_to.window(window_handle)
        except NoSuchWindowException:
            continue

        if callback(webdriver):
            return window_handle

    # Simply switch back to the original window handle and return None by
    # default if no matching window handle was found
    webdriver.switch_to.window(original_window_handle)


def make_find_domain_condition(webdriver, requested_domain):
    def condition(webdriver):
        try:
            return get_domain(webdriver.current_url) == requested_domain

        # This exception can apparently occur in PhantomJS if the window handle
        # wasn't closed "properly", which seems to happen sometimes due to the
        # JavaScript returned by the HTTPRequestHandler
        except NoSuchWindowException:
            pass

    return condition


class RequestMixin(object):

    def request(self, method, url, find_window_handle_timeout=-1, page_load_timeout=-1, **kwargs):
        # Create a requests session object for this instance that sends the
        # webdriver's default request headers
        if not hasattr(self, '_seleniumrequests_session'):
            self._seleniumrequests_session = requests.Session()
            self._seleniumrequests_session.headers = get_webdriver_request_headers(self)

            # Delete Cookie header from the request headers, to prevent
            # overwriting manually set cookies later. This should only happen
            # during testing or when working with requests to localhost
            if 'cookie' in self._seleniumrequests_session.headers:
                del self._seleniumrequests_session.headers['cookie']

        original_window_handle = None
        opened_window_handle = None
        requested_domain = get_domain(url)
        # If a NoSuchWindowException occurs here (see
        # make_find_domain_condition) it's the concern of the calling code to
        # handle it, since the exception is only potentially generated
        # internally by get_webdriver_request_headers
        if not get_domain(self.current_url) == requested_domain:
            original_window_handle = self.current_window_handle

            # Try to find an existing window handle that matches the requested
            # domain
            condition = make_find_domain_condition(self, requested_domain)
            window_handle = find_window_handle(self, condition)

            # Create a new window handle manually in case it wasn't found
            if not window_handle:
                components = urlparse(url)

                previous_window_handles = set(self.window_handles)
                self.execute_script("window.open('%s://%s/');" % (components.scheme, components.netloc))
                difference = set(self.window_handles) - set(previous_window_handles)

                if len(difference) == 1:
                    opened_window_handle = tuple(difference)[0]

                    # Will automatically wait until the new window handle has
                    # finished loading
                    self.switch_to.window(opened_window_handle)
                else:
                    warnings.warn(FIND_WINDOW_HANDLE_WARNING)
                    opened_window_handle = find_window_handle(self, condition)

                    # Window handle could not be found during first pass.
                    # Either the WebDriver didn't wait for the page load
                    # (PhantomJS) or there was a redirect
                    if not opened_window_handle:
                        response = self._seleniumrequests_session.get(url, stream=True)
                        domain = tld.get_tld(response.url)
                        if domain != requested_domain:
                            condition = make_find_domain_condition(self, get_domain(response.url))

                    # Some webdrivers (PhantomJS) take some time until the new
                    # window handle has loaded the correct URL
                    start = time.time()
                    while not opened_window_handle:
                        opened_window_handle = find_window_handle(self, condition)
                        if find_window_handle_timeout >= 0 and time.time() - start > find_window_handle_timeout:
                            raise TimeoutException('window handle could not be found')

        # Acquire webdriver's instance cookies and merge them with potentially
        # passed cookies
        cookies = prepare_requests_cookies(self.get_cookies())
        if 'cookies' in kwargs:
            cookies.update(kwargs['cookies'])
        kwargs['cookies'] = cookies

        response = self._seleniumrequests_session.request(method, url, **kwargs)

        # Set cookies set by the HTTP response within the webdriver instance
        for cookie in response.cookies:
            cookie_dict = {'name': cookie.name, 'value': cookie.value, 'secure': cookie.secure}
            if cookie.expires:
                cookie_dict['expiry'] = cookie.expires
            if cookie.path_specified:
                cookie_dict['path'] = cookie.path

            # PhantomJS's GhostDriver doesn't block until the active window has
            # loaded, thus we have to do this:
            start = time.time()
            while page_load_timeout < 0 or time.time() - start <= page_load_timeout:
                try:
                    self.add_cookie(cookie_dict)
                    break
                except WebDriverException:
                    pass
            else:
                raise TimeoutException('page took too long to load')

        # We don't actually want to keep cookies in the RequestCookieJar, the
        # session object is mostly useful for performance when making requests
        # (persistent connections to the host). After transferring the response
        # cookies, the WebDriver instance should have and manage all cookies.
        # A possible scenario: Someone is using a WebDriver instance and then
        # decides to delete a certain cookie in some way, during the next
        # request that is made, the old cookie would still be sent by the
        # session
        self._seleniumrequests_session.cookies.clear()

        if opened_window_handle:
            self.close()

        if original_window_handle:
            self.switch_to.window(original_window_handle)

        return response
