from selenium.webdriver import Firefox, Chrome, Ie, Opera, Safari, PhantomJS, Android, Remote

from .request import request


# Monkey patch Selenium webdriver classes and make them easily importable
Firefox.request = request
Chrome.request = request
Ie.request = request
Opera.request = request
Safari.request = request
PhantomJS.request = request
Android.request = request
Remote.request = request
