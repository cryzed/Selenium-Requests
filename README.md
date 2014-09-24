Selenium-Requests
=================

Extends Selenium WebDriver classes to include the [request](http://docs.python-requests.org/en/latest/api/#requests.request) function from the [Requests](http://python-requests.org/) library, while doing all the needed cookie and request headers handling.


Details
-------

Before the actual request is made, a local HTTP server is started that serves a single request made by the webdriver instance to get the "standard" HTTP request headers sent by this webdriver; these are cached (only happens once during its lifetime) and later used in conjunction with the Requests library to make the requests look identical to those that would have been sent by the webdriver. Cookies held by the webdriver instance are added to the request headers and those returned in a response automatically set for the webdriver instance.


Usage
-----
```python
# Import any WebDriver class that you would usually import from
# selenium.webdriver from the seleniumrequests module
from seleniumrequests import Firefox


webdriver = Firefox()
response = webdriver.request('get', 'http://google.de/')
print response
```
