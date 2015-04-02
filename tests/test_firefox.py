from seleniumrequests import Firefox


def test_window_handling():
    webdriver = Firefox()
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
