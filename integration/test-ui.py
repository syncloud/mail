from os.path import dirname, join

import pytest
from selenium.webdriver.common.keys import Keys
from subprocess import check_output
from syncloudlib.integration.hosts import add_host_alias
from integration import lib

DIR = dirname(__file__)
TMP_DIR = '/tmp/syncloud/ui'


@pytest.fixture(scope="session")
def module_setup(request, device, artifact_dir, ui_mode, data_dir):
    def module_teardown():
        device.activated()
        device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl > {0}/journalctl.log'.format(TMP_DIR), throw=False)
        device.run_ssh('cp -r {0}/log/*.log {1}'.format(data_dir, TMP_DIR), throw=False)
        device.scp_from_device('{0}/*'.format(TMP_DIR), join(artifact_dir, ui_mode))
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)
    request.addfinalizer(module_teardown)


def test_start(module_setup, app, device_host, domain):
    add_host_alias(app, device_host, domain)


def test_web(selenium, device_user, device_password):

    lib.login(selenium, device_user, device_password)
    selenium.screenshot('main')


def test_teardown(driver):
    driver.quit()
