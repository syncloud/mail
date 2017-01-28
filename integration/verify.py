import os
import sys
from os import listdir
from os.path import dirname, join, abspath, isdir
import time
from subprocess import check_output

import pytest
import re

app_path = join(dirname(__file__), '..')
sys.path.append(join(app_path, 'src'))

lib_path = join(app_path, 'lib')
libs = [abspath(join(lib_path, item)) for item in listdir(lib_path) if isdir(join(lib_path, item))]
map(lambda x: sys.path.insert(0, x), libs)

import requests
import shutil
import smtplib
from email.mime.text import MIMEText
from integration.util.ssh import run_scp, ssh_command, SSH, run_ssh, set_docker_ssh_port
from requests.adapters import HTTPAdapter
import getpass, imaplib

DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
SYNCLOUD_INFO = 'syncloud.info'
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
DEFAULT_DEVICE_PASSWORD = 'syncloud'
LOGS_SSH_PASSWORD = DEFAULT_DEVICE_PASSWORD


@pytest.fixture(scope="session")
def module_setup(request):
    request.addfinalizer(module_teardown)


def module_teardown():
    os.mkdir(LOG_DIR)

    platform_log_dir = join(LOG_DIR, 'platform_log')
    os.mkdir(platform_log_dir)
    run_scp('root@localhost:/opt/data/platform/log/* {0}'.format(platform_log_dir), password=LOGS_SSH_PASSWORD)

    mail_log_dir = join(LOG_DIR, 'mail_log')
    os.mkdir(mail_log_dir)
    run_ssh('ls -la /opt/data/mail/log', password=DEVICE_PASSWORD)
    run_scp('root@localhost:/opt/data/mail/log/* {0}'.format(mail_log_dir), password=DEVICE_PASSWORD)

    run_ssh('netstat -l', password=DEVICE_PASSWORD)

    print('postfix systems logs')
    run_ssh('journalctl | grep postfix', password=DEVICE_PASSWORD)

    print('dovecot systems logs')
    run_ssh('journalctl | grep dovecot', password=DEVICE_PASSWORD)
    
    print('-------------------------------------------------------')
    print('syncloud docker image is running')
    print('connect using: {0}'.format(ssh_command(DEVICE_PASSWORD, SSH)))
    print('-------------------------------------------------------')


@pytest.fixture(scope='function')
def syncloud_session():
    session = requests.session()
    session.post('http://localhost/rest/login', data={'name': DEVICE_USER, 'password': DEVICE_PASSWORD})
    return session


def test_start(module_setup):
    shutil.rmtree(LOG_DIR, ignore_errors=True)


def test_activate_device(auth):
    email, password, domain, release, version, arch = auth

    run_ssh('/opt/app/sam/bin/sam update --release {0}'.format(release), password=DEFAULT_DEVICE_PASSWORD)
    run_ssh('/opt/app/sam/bin/sam --debug upgrade platform', password=DEFAULT_DEVICE_PASSWORD)

    response = requests.post('http://localhost:81/rest/activate',
                             data={'main_domain': 'syncloud.info', 'redirect_email': email, 'redirect_password': password,
                                   'user_domain': domain, 'device_username': DEVICE_USER, 'device_password': DEVICE_PASSWORD})
    assert response.status_code == 200
    global LOGS_SSH_PASSWORD
    LOGS_SSH_PASSWORD = DEVICE_PASSWORD


def test_running_platform_web():
    print(check_output('nc -zv -w 1 localhost 80', shell=True))


def test_platform_rest():
    session = requests.session()
    session.mount('http://localhost', HTTPAdapter(max_retries=5))
    response = session.get('http://localhost', timeout=60)
    assert response.status_code == 200


def test_external_mode(syncloud_session):
    response = syncloud_session.get('http://localhost/rest/settings/set_external_access',
                                    params={'external_access': 'true'},
                                    timeout=60)
    assert '"success": true' in response.text
    assert response.status_code == 200


def test_install(auth):
    __local_install(auth)


def test_running_smtp():
    print(check_output('nc -zv -w 1 localhost 25', shell=True))


def test_running_pop3():
    print(check_output('nc -zv -w 1 localhost 110', shell=True))


def test_running_roundcube():
    print(check_output('nc -zv -w 1 localhost 1100', shell=True))


def test_dovecot_auth():
    run_ssh('/opt/app/mail/dovecot/bin/doveadm -c /opt/app/mail/config/dovecot/dovecot.conf  auth test {0} {1}'
            .format(DEVICE_USER, DEVICE_PASSWORD), password=DEVICE_PASSWORD)


def test_postfix_auth():
    server = smtplib.SMTP('localhost', timeout=10)
    server.set_debuglevel(1)
    server.login(DEVICE_USER, DEVICE_PASSWORD)


def test_mail_sending(device_domain):
    server = smtplib.SMTP('localhost:587', timeout=10)
    server.set_debuglevel(1)
    server.ehlo()
    #server.starttls()
    server.login(DEVICE_USER, DEVICE_PASSWORD)
    msg = MIMEText('test')
    mail_from = '{0}@{1}'.format(DEVICE_USER, device_domain)
    mail_to = mail_from
    msg['Subject'] = 'test subject'
    msg['From'] = mail_from
    msg['To'] = mail_to
    server.sendmail(mail_from, [mail_to], msg.as_string())
    server.quit()


def test_filesystem_mailbox():
    run_ssh('find /opt/data/mail/box', password=DEVICE_PASSWORD)


def test_starttls():
    run_ssh("echo \"A Logout\" | openssl s_client -connect localhost:143 -starttls imap", password=DEVICE_PASSWORD)


def test_mail_receiving():

    message_count = 0
    retry = 0
    retries = 3
    while retry < retries:
        message_count = get_message_count()
        if message_count > 0:
            break
        retry += 1
        time.sleep(1)

    assert message_count == 1


def get_message_count():
    imaplib.Debug = 4
    server = imaplib.IMAP4_SSL('localhost')
    server.login(DEVICE_USER, DEVICE_PASSWORD)
    selected = server.select('inbox')
    server.logout()
    # assert selected[0] == 'OK'
    return int(selected[1][0])


def test_postfix_ldap_aliases(user_domain):
    run_ssh('/opt/app/mail/postfix/usr/sbin/postmap -q {0}@{1} ldap:/opt/app/mail/config/postfix/ldap-aliases.cf'
            .format(DEVICE_USER, user_domain), password=DEVICE_PASSWORD)


def test_upgrade(auth):
    run_ssh('/opt/app/sam/bin/sam --debug remove mail', password=DEVICE_PASSWORD)
    __local_install(auth)


def __local_install(auth, action='install'):
    email, password, domain, release, version, arch = auth
    run_scp('{0}/../mail-{1}-{2}.tar.gz root@localhost:/'.format(DIR, version, arch), password=DEVICE_PASSWORD)
    run_ssh('/opt/app/sam/bin/sam --debug {0} /mail-{1}-{2}.tar.gz'.format(action, version, arch), password=DEVICE_PASSWORD)
    time.sleep(3)
