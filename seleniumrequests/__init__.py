from selenium.webdriver import Firefox, Chrome, Ie, Opera, Safari, PhantomJS, Android, Remote

from .request import request


# Monkey patch Selenium webdriver classes and make them easily importable
for class_ in Firefox, Chrome, Ie, Opera, Safari, PhantomJS, Android, Remote:
    class_.request = request
