__version__ = "2.0.3"

from selenium.webdriver import Chrome as _Chrome
from selenium.webdriver import ChromiumEdge as _ChromiumEdge
from selenium.webdriver import Edge as _Edge
from selenium.webdriver import Firefox as _Firefox
from selenium.webdriver import Ie as _Ie
from selenium.webdriver import Remote as _Remote
from selenium.webdriver import Safari as _Safari
from selenium.webdriver import WebKitGTK as _WebKitGTK
from selenium.webdriver import WPEWebKit as _WPEWebKit

from seleniumrequests.request import RequestsSessionMixin


class Chrome(RequestsSessionMixin, _Chrome):
    pass


class ChromiumEdge(RequestsSessionMixin, _ChromiumEdge):
    pass


class Edge(RequestsSessionMixin, _Edge):
    pass


class Firefox(RequestsSessionMixin, _Firefox):
    pass


class Ie(RequestsSessionMixin, _Ie):
    pass


class Remote(RequestsSessionMixin, _Remote):
    pass


class Safari(RequestsSessionMixin, _Safari):
    pass


class WebKitGTK(RequestsSessionMixin, _WebKitGTK):
    pass


class WPEWebKit(RequestsSessionMixin, _WPEWebKit):
    pass
