from seleniumrequests import Firefox, PhantomJS


def make_window_handling_test(webdriver_class):
    def test_window_handling():
        webdriver = webdriver_class()
        webdriver.get('https://www.google.com/')
        webdriver.execute_script("window.open('https://www.facebook.com/');")

        original_window_handle = webdriver.current_window_handle
        original_window_handles = set(webdriver.window_handles)

        webdriver.request('GET', 'https://www.youtube.com/')

        # Make sure that the window handle was switched back to the original one
        # after making a request that caused a new window to open
        assert webdriver.current_window_handle == original_window_handle

        # Make sure that all additional window handles that were opened during the
        # request were closed again
        assert set(webdriver.window_handles) == original_window_handles

        webdriver.quit()

    return test_window_handling


test_window_handling_firefox = make_window_handling_test(Firefox)
test_window_handling_phantomjs = make_window_handling_test(PhantomJS)
