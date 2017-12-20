import os
import shutil
from os.path import dirname, join, exists

import time

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
log_dir = join(LOG_DIR, 'app_log')
screenshot_dir = join(DIR, 'screenshot')


@pytest.fixture(scope="module")
def driver():

    if exists(screenshot_dir):
        shutil.rmtree(screenshot_dir)
    os.mkdir(screenshot_dir)

    firefox_path = '{0}/firefox/firefox'.format(DIR)
    caps = DesiredCapabilities.FIREFOX
    caps["marionette"] = True
    caps['acceptSslCerts'] = True

    binary = FirefoxBinary(firefox_path)

    profile = webdriver.FirefoxProfile()
    profile.add_extension('{0}/JSErrorCollector.xpi'.format(DIR))
    profile.set_preference('app.update.auto', False)
    profile.set_preference('app.update.enabled', False)
    driver = webdriver.Firefox(profile, capabilities=caps, log_path="{0}/firefox.log".format(LOG_DIR),
                               firefox_binary=binary, executable_path=join(DIR, 'geckodriver/geckodriver'))
    #driver.set_page_load_timeout(30)
    #print driver.capabilities['version']
    return driver


def test_web_with_selenium(driver, user_domain, device_domain):

    wait_driver = WebDriverWait(driver, 20)

    screenshot_dir = join(DIR, 'screenshot')
    if exists(screenshot_dir):
        shutil.rmtree(screenshot_dir)
    os.mkdir(screenshot_dir)

    driver.get("http://{0}".format(user_domain))
    
    time.sleep(2)
    driver.get_screenshot_as_file(join(screenshot_dir, 'login.png'))

    print(driver.page_source.encode("utf-8"))

    user = driver.find_element_by_id("rcmloginuser")
    user.send_keys(DEVICE_USER)
    password = driver.find_element_by_id("rcmloginpwd")
    password.send_keys(DEVICE_PASSWORD)
    driver.get_screenshot_as_file(join(screenshot_dir, 'login.png'))
    password.send_keys(Keys.RETURN)

    #time.sleep(10)

    username = '{0}@{1}'.format(DEVICE_USER, device_domain)
    #print('found: {0}'.format(username in page))
    wait_driver.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, '.username'), username))

    driver.get_screenshot_as_file(join(screenshot_dir, 'main.png'))

    page = driver.page_source.encode("utf-8")
    print(page)