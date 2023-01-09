import http.server
import socket
import threading
import time
import urllib.parse
import warnings

import requests
import tldextract
from selenium.common.exceptions import NoSuchWindowException

FIND_WINDOW_HANDLE_WARNING = (
    "Created window handle could not be found reliably. Using less reliable "
    "alternative method. JavaScript redirects are not supported and an "
    "additional GET request might be made for the requested URL."
)

HEADERS = None
UPDATER_HEADERS_MUTEX = threading.Semaphore()
UPDATER_HEADERS_MUTEX.acquire()


class SeleniumRequestsException(Exception):
    pass


# Using a global value to pass around the headers dictionary reference seems to be the easiest way to get access to it,
# since the HTTPServer doesn't keep an object of the instance of the HTTPRequestHandler
class HTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global HEADERS
        HEADERS = requests.structures.CaseInsensitiveDict(self.headers)
        UPDATER_HEADERS_MUTEX.release()

        self.send_response(200)
        self.end_headers()
        # Immediately close the window as soon as it is loaded
        self.wfile.write('<script type="text/javascript">window.close();</script>'.encode("utf-8"))

    # Suppress unwanted logging to stderr
    def log_message(self, format, *args):
        pass


def get_unused_port():
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_.bind(("", 0))
    address, port = socket_.getsockname()
    socket_.close()
    return port


def get_webdriver_request_headers(webdriver, proxy_host="127.0.0.1"):
    # There's a small chance that the port was taken since the call of get_unused_port(), so make sure we try as often
    # as needed
    while True:
        port = get_unused_port()
        try:
            server = http.server.HTTPServer(("", port), HTTPRequestHandler)
            break
        except socket.error:
            pass

    threading.Thread(target=server.serve_forever, daemon=True).start()
    original_window_handle = webdriver.current_window_handle
    webdriver.execute_script("window.open('http://%s:%d/', '_blank');" % (proxy_host, port))

    UPDATER_HEADERS_MUTEX.acquire()
    # XXX: .shutdown() seems to block indefinitely and not shut down the server
    # server.shutdown()

    # Not optional: Make sure that the webdriver didn't switch the window handle to the newly opened window. Behaviors
    # of different webdrivers seem to differ here. Workaround for Firefox: If a new window is opened via JavaScript as a
    # new tab, requesting self.current_url never returns. Explicitly switching to the current window handle again seems
    # to fix this issue.

    # Workaround for buggy Chrome/Chromedriver combination: https://github.com/cryzed/Selenium-Requests/issues/53
    needs_chrome_workaround = webdriver.name == "chrome" and int(webdriver.capabilities["browserVersion"].split(".", maxsplit=1)[0]) >= 106
    if not needs_chrome_workaround:
        webdriver.switch_to.window(original_window_handle)

    global HEADERS
    headers = HEADERS
    HEADERS = None

    # Remove the host header, which will simply contain the localhost address of the HTTPRequestHandler instance
    del headers["host"]
    return headers


def prepare_requests_cookies(webdriver_cookies):
    return {str(cookie["name"]): str(cookie["value"]) for cookie in webdriver_cookies}


def get_tld(url):
    components = tldextract.extract(url)
    # Since the registered domain could not be extracted, assume that it's simply an IP and strip away the protocol
    # prefix and potentially trailing rest after "/" away. If it isn't, this fails gracefully for unknown domains, e.g.:
    # "http://domain.onion/" -> "domain.onion". If it doesn't look like a valid address at all, return the URL
    # unchanged.
    if not components.registered_domain:
        try:
            return url.split("://", 1)[1].split(":", 1)[0].split("/", 1)[0]
        except IndexError:
            return url

    return components.registered_domain


def find_window_handle(webdriver, predicate):
    original_window_handle = webdriver.current_window_handle
    if predicate(webdriver):
        return original_window_handle

    # Start search beginning with the most recently added window handle: the chance is higher that this is the correct
    # one in most cases
    for window_handle in reversed(webdriver.window_handles):
        if window_handle == original_window_handle:
            continue

        # This exception can occur if the window handle was closed between accessing the window handles and attempting
        # to switch to it, in which case it can be silently ignored.
        try:
            webdriver.switch_to.window(window_handle)
        except NoSuchWindowException:
            continue

        if predicate(webdriver):
            return window_handle

    # Simply switch back to the original window handle and return None if no matching window handle was found
    webdriver.switch_to.window(original_window_handle)


def make_match_domain_predicate(domain):
    def predicate(webdriver):
        try:
            return get_tld(webdriver.current_url) == domain
        # This exception can occur if the current window handle was closed
        except NoSuchWindowException:
            pass

    return predicate


class RequestsSessionMixin(object):
    def __init__(self, *args, proxy_host="127.0.0.1", **kwargs):
        super(RequestsSessionMixin, self).__init__(*args, **kwargs)
        self.requests_session = requests.Session()

        # Use double underscore to prevent name clashes with all subclasses
        self.__proxy_host = proxy_host
        self.__has_webdriver_request_headers = False

    def add_cookie(self, cookie_dict):
        super(RequestsSessionMixin, self).add_cookie(cookie_dict)

    def request(self, method, url, **kwargs):
        if not self.__has_webdriver_request_headers:
            self.requests_session.headers = get_webdriver_request_headers(self, proxy_host=self.__proxy_host)
            self.__has_webdriver_request_headers = True

            # Delete cookies from the request headers, to prevent overwriting manually set cookies later. This should
            # only happen when the webdriver has cookies set for the localhost
            if "cookie" in self.requests_session.headers:
                del self.requests_session.headers["cookie"]

        original_window_handle = None
        opened_window_handle = None
        requested_tld = get_tld(url)
        if not get_tld(self.current_url) == requested_tld:
            original_window_handle = self.current_window_handle

            # Try to find an existing window handle that matches the requested top-level domain
            predicate = make_match_domain_predicate(requested_tld)
            window_handle = find_window_handle(self, predicate)

            # Create a new window handle manually in case it wasn't found
            if not window_handle:
                previous_window_handles = set(self.window_handles)
                components = urllib.parse.urlsplit(url)
                self.execute_script("window.open('%s://%s/', '_blank');" % (components.scheme, components.netloc))
                difference = set(self.window_handles) - previous_window_handles

                if len(difference) == 1:
                    opened_window_handle = difference.pop()
                    self.switch_to.window(opened_window_handle)
                else:
                    warnings.warn(FIND_WINDOW_HANDLE_WARNING)
                    opened_window_handle = find_window_handle(self, predicate)

                    # Window handle could not be found during first pass. There might have been a redirect and the top-
                    # level domain changed
                    if not opened_window_handle:
                        response = self.requests_session.get(url, stream=True)
                        current_tld = get_tld(response.url)
                        if current_tld != requested_tld:
                            predicate = make_match_domain_predicate(current_tld)
                            opened_window_handle = find_window_handle(self, predicate)
                            if not opened_window_handle:
                                raise SeleniumRequestsException("window handle could not be found")

        # Acquire WebDriver's cookies and merge them with potentially passed cookies
        cookies = prepare_requests_cookies(self.get_cookies())
        if "cookies" in kwargs:
            cookies.update(kwargs["cookies"])
        kwargs["cookies"] = cookies

        response = self.requests_session.request(method, url, **kwargs)

        # Set cookies received from the HTTP response in the WebDriver
        current_tld = get_tld(self.current_url)
        for cookie in response.cookies:
            cookie_dict = {"domain": cookie.domain, "name": cookie.name, "value": cookie.value, "secure": cookie.secure}
            if cookie.expires:
                cookie_dict["expiry"] = cookie.expires
            if cookie.path_specified:
                cookie_dict["path"] = cookie.path

            self.add_cookie(cookie_dict)

        # Don't keep cookies in the Requests session, only use the WebDriver's
        self.requests_session.cookies.clear()
        if opened_window_handle:
            self.close()
        if original_window_handle:
            self.switch_to.window(original_window_handle)

        return response
