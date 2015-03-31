from selenium.webdriver import Firefox, Chrome, Ie, Opera, Safari, PhantomJS, Android, Remote

from seleniumrequests.request import RequestMixin


class Firefox(Firefox, RequestMixin):
    pass


class Chrome(Chrome, RequestMixin):
    pass


class Ie(Ie, RequestMixin):
    pass


class Opera(Opera, RequestMixin):
    pass


class Safari(Safari, RequestMixin):
    pass


class PhantomJS(PhantomJS, RequestMixin):
    pass


class Android(Android, RequestMixin):
    pass


class Remote(Remote, RequestMixin):
    pass
