from setuptools import setup


with open("README.md") as file:
    readme = file.read()

setup(
    name="selenium-requests",
    version="1.3.1",
    description=(
        "Extends Selenium WebDriver classes to include the request function "
        "from the Requests library, while doing all the needed cookie and "
        "request headers handling."
    ),
    long_description=readme,
    author="Chris Braun",
    author_email="cryzed@googlemail.com",
    url="https://github.com/cryzed/Selenium-Requests",
    packages=("seleniumrequests",),
    install_requires=("requests", "selenium", "six", "tldextract"),
    license="MIT",
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
)
