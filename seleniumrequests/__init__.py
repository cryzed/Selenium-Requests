from selenium.webdriver import _Firefox, _Chrome, _Ie, _Edge, _Opera, _Safari, _BlackBerry, _PhantomJS, _Android, \
    _Remote

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
