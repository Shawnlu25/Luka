from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import validators

class SeleniumSandbox(object):
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.set_window_size(1024, 768)

    def visit(self, url):
        url = url if url.startswith("http") else "http://" + url
        if not validators.url(url):
            raise ValueError("error: visiting invalid URL")

        self.driver.get(url)


if __name__ == "__main__":
    sandbox = SeleniumSandbox()
    sandbox.visit("www.google.com")
    

