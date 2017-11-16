from selenium.webdriver import (
    Firefox as _Firefox, Chrome as _Chrome, Ie as _Ie, Edge as _Edge, Opera as _Opera, Safari as _Safari,
    BlackBerry as _BlackBerry, PhantomJS as _PhantomJS, Android as _Android, Remote as _Remote)

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
