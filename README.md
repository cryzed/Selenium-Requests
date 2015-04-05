Selenium Requests
=================

Extends Selenium WebDriver classes to include the [request](http://docs.python-requests.org/en/latest/api/#requests.request) function from the [Requests](http://python-requests.org/) library, while doing all the needed cookie and request headers handling.

Before the actual request is made, a local HTTP server is started that serves a single request made by the webdriver instance to get the "standard" HTTP request headers sent by this webdriver; these are cached (only happens once during its lifetime) and later used in conjunction with the Requests library to make the requests look identical to those that would have been sent by the webdriver. Cookies held by the webdriver instance are added to the request headers and those returned in a response automatically set for the webdriver instance.


Usage
-----
```python
# Import any WebDriver class that you would usually import from
# selenium.webdriver from the seleniumrequests module
from seleniumrequests import Firefox


webdriver = Firefox()
response = webdriver.request('GET', 'http://google.com/')
print(response)
```


Installation
------------
```pip install selenium-requests```


Details
-------

The request method supports two additional arguments:
  * ```find_window_handle_timeout``` (default: -1 seconds)
  * ```page_load_timeout``` (default: -1 seconds)

If the timeout is negative, then the script will be allowed to run indefinitely (similarly to Selenium WebDriver's default behaviour)

The first is needed because there is no reliable way to create a new window handle with the Selenium WebDriver interface, so a new handle has to be spawned via JavaScript and subsequently found to be able to get or set cookies with the WebDriver. There are two methods to do this: The first involves simply comparing the set of window handles before and after the JavaScript was executed and finding the difference. If the difference is unreliable (0 or more than 1 window handles found) an alternative less reliable method is used: the top-level domain for each frame is compared to the requested domain. If no results are found, an additional GET request is made to the requested domain to check for a potential redirect. Whether there was a redirect or not, the old or new domain will now be searched for ```find_window_handle_timeout``` seconds until it is either found or a ```TimeoutException``` is raised.

The second is needed mostly because of [PhantomJS](http://phantomjs.org/). Every other webdriver blocks until the current window handle is loaded, except PhantomJS. If the new window handle was found via the first method (see above) and then cookies should be set, it's possible that an exception is raised, because the webdriver has to have switched to a window handle with the correct domain prior to setting cookies. Thus the method waits ```page_load_timeout``` seconds before raising a ```TimeoutException```.
