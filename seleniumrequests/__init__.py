from selenium.webdriver import Firefox, Chrome, Ie, Edge, Opera, Safari, BlackBerry, PhantomJS, Android, Remote

from seleniumrequests.request import RequestsSessionMixin


class Firefox(RequestsSessionMixin, Firefox):
    pass


class Chrome(RequestsSessionMixin, Chrome):
    pass


class Ie(RequestsSessionMixin, Ie):
    pass


class Edge(RequestsSessionMixin, Edge):
    pass


class Opera(RequestsSessionMixin, Opera):
    pass


class Safari(RequestsSessionMixin, Safari):
    pass


class BlackBerry(RequestsSessionMixin, BlackBerry):
    pass


class PhantomJS(RequestsSessionMixin, PhantomJS):
    pass


class Android(RequestsSessionMixin, Android):
    pass


class Remote(RequestsSessionMixin, Remote):
    pass
