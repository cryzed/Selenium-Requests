from setuptools import setup, find_packages


setup(
    name="SeleniumRequests",
    version="1.0.0",
    description="Extends Selenium WebDriver classes to include the request function from the Requests library, while doing all the needed cookie and request headers handling.",
    author="cryzed",
    url="https://github.com/cryzed/Selenium-Requests",
    packages=find_packages(),
    install_requires=[
        'selenium>=2.45.0',
        'requests>=2.6.0',
    ]
)
