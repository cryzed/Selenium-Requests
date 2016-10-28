from selenium.webdriver import Firefox, Chrome, Ie, Edge, Opera, Safari, BlackBerry, PhantomJS, Android, Remote

from seleniumrequests.request import RequestMixin


class Firefox(RequestMixin, Firefox):
    pass


class Chrome(RequestMixin, Chrome):
    pass


class Ie(RequestMixin, Ie):
    pass


class Edge(RequestMixin, Edge):
    pass


class Opera(RequestMixin, Opera):
    pass


class Safari(RequestMixin, Safari):
    pass


class BlackBerry(RequestMixin, BlackBerry):
    pass


class PhantomJS(RequestMixin, PhantomJS):
    pass


class Android(RequestMixin, Android):
    pass


class Remote(RequestMixin, Remote):
    pass
