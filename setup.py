from setuptools import setup

try:
    import pypandoc
except ImportError:
    pypandoc = None


if pypandoc:
    long_description = pypandoc.convert('README.md', 'rst')
else:
    with open('README.md') as file:
        long_description = file.read()


setup(
    name='selenium-requests',
    version='1.0.2',
    description='Extends Selenium WebDriver classes to include the request function from the Requests library, while doing all the needed cookie and request headers handling.',
    long_description=long_description,
    author='Chris Braun',
    author_email='cryzed@googlemail.com',
    url='https://github.com/cryzed/Selenium-Requests',
    packages=('seleniumrequests',),
    zip_safe=False,
    install_requires=(
        'requests',
        'selenium',
        'six',
        'tld'
    ),
    license='MIT'
)
