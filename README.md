Selenium-Requests
=================

Monkey patches Selenium WebDrivers to include the request method from the "requests" library, while doing all the needed cookie and request headers handling.


Details
-------

Before the actual request is made, a local HTTP server is started that serves a single request made by the running webdriver to get the "standard" HTTP request headers sent by this webdriver instance; these are cached (only happens once during its lifetime) and later used in conjunction with the requests library to make the requests look identical to that of the webdriver. Additionally cookies held by the webdriver instance are automatically added to the request headers and those returned by a requests library response object automatically set for the webdriver instance.


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
