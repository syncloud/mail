from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time


def login(selenium, device_user, device_password):

    selenium.open_app()
    selenium.screenshot('login')
    selenium.find_by_id("rcmloginuser").send_keys(device_user)
    password = selenium.find_by_id("rcmloginpwd")
    password.send_keys(device_password)
    selenium.screenshot('login-filled')
    password.send_keys(Keys.RETURN)
    selenium.screenshot('login_progress')
    selenium.find_by_xpath("//span[contains(.,'test subject')]")
    
