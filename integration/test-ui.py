from os.path import dirname, join

import pytest
from selenium.webdriver.common.keys import Keys
from syncloudlib.integration.hosts import add_host_alias_by_ip

DIR = dirname(__file__)
TMP_DIR = '/tmp/syncloud/ui'


@pytest.fixture(scope="session")
def module_setup(request, device, artifact_dir, ui_mode):
    def module_teardown():
        device.activated()
        device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl > {0}/journalctl.ui.{1}.log'.format(TMP_DIR, ui_mode), throw=False)
        device.run_ssh('cp /var/log/syslog {0}/syslog.ui.{1}.log'.format(TMP_DIR, ui_mode), throw=False)
      
        device.scp_from_device('{0}/*'.format(TMP_DIR), join(artifact_dir, 'log'))

    request.addfinalizer(module_teardown)


def test_start(module_setup, app, device_host, domain):
    add_host_alias_by_ip(app, domain, device_host)


def test_web(selenium, device_user, device_password):

    selenium.open_app()
    selenium.screenshot('login')
    selenium.find_by_id("rcmloginuser").send_keys(device_user)
    password = selenium.find_by_id("rcmloginpwd")
    password.send_keys(device_password)
    selenium.screenshot('login-filled')
    password.send_keys(Keys.RETURN)
    selenium.screenshot('login_progress')
    selenium.find_by_xpath("//ul[@id='mailboxlist']")
    selenium.screenshot('main')
