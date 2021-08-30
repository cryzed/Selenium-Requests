__version__ = "1.3.3"

from selenium.webdriver import Android as _Android
from selenium.webdriver import BlackBerry as _BlackBerry
from selenium.webdriver import Chrome as _Chrome
from selenium.webdriver import Edge as _Edge
from selenium.webdriver import Firefox as _Firefox
from selenium.webdriver import Ie as _Ie
from selenium.webdriver import Opera as _Opera
from selenium.webdriver import PhantomJS as _PhantomJS
from selenium.webdriver import Remote as _Remote
from selenium.webdriver import Safari as _Safari
from seleniumrequests.request import RequestsSessionMixin


class Firefox(RequestsSessionMixin, _Firefox):
    pass


class Chrome(RequestsSessionMixin, _Chrome):
    pass


class Ie(RequestsSessionMixin, _Ie):
    pass


class Edge(RequestsSessionMixin, _Edge):
    pass


class Opera(RequestsSessionMixin, _Opera):
    pass


class Safari(RequestsSessionMixin, _Safari):
    pass


class BlackBerry(RequestsSessionMixin, _BlackBerry):
    pass


class PhantomJS(RequestsSessionMixin, _PhantomJS):
    pass


class Android(RequestsSessionMixin, _Android):
    pass


class Remote(RequestsSessionMixin, _Remote):
    pass
