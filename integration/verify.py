import imaplib
import os
import shutil
import smtplib
import time
from email.mime.text import MIMEText
from os.path import dirname, join
from subprocess import check_output

import pytest
import requests
from requests.adapters import HTTPAdapter

from integration.util.helper import retry_func
from syncloudlib.integration.installer import local_install, wait_for_sam, wait_for_rest, local_remove, \
    get_data_dir, get_app_dir, get_service_prefix, get_ssh_env_vars
from syncloudlib.integration.loop import loop_device_cleanup
from syncloudlib.integration.ssh import run_scp, run_ssh

SYNCLOUD_INFO = 'syncloud.info'
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
DEFAULT_DEVICE_PASSWORD = 'syncloud'
LOGS_SSH_PASSWORD = DEFAULT_DEVICE_PASSWORD
DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')


@pytest.fixture(scope="session")
def platform_data_dir(installer):
    return get_data_dir(installer, 'platform')


@pytest.fixture(scope="session")
def data_dir(installer):
    return get_data_dir(installer, 'mail')
         

@pytest.fixture(scope="session")
def app_dir(installer):
    return get_app_dir(installer, 'mail')


@pytest.fixture(scope="session")
def service_prefix(installer):
    return get_service_prefix(installer)


@pytest.fixture(scope="session")
def module_setup(request, user_domain):
    request.addfinalizer(lambda: module_teardown(user_domain))


def module_teardown(user_domain):
    platform_log_dir = join(LOG_DIR, 'platform_log')
    os.mkdir(platform_log_dir)
    run_scp('root@{0}:/opt/data/platform/log/* {1}'.format(user_domain, platform_log_dir), password=LOGS_SSH_PASSWORD, throw=False)
    run_scp('root@{0}:/var/log/sam.log {1}'.format(user_domain, platform_log_dir), password=LOGS_SSH_PASSWORD, throw=False)

    mail_log_dir = join(LOG_DIR, 'mail_log')
    os.mkdir(mail_log_dir)
    run_scp('root@{0}:/opt/data/mail/log/*.log {1}'.format(user_domain, mail_log_dir), password=LOGS_SSH_PASSWORD, throw=False)
    
    run_ssh(user_domain, 'ls -la /opt/data/mail/log/', password=LOGS_SSH_PASSWORD, throw=False)

    print('systemd logs')
    run_ssh(user_domain, 'journalctl | tail -200', password=LOGS_SSH_PASSWORD)


@pytest.fixture(scope='function')
def syncloud_session(device_host):
    session = requests.session()
    session.post('http://{0}/rest/login'.format(device_host), data={'name': DEVICE_USER, 'password': DEVICE_PASSWORD})
    return session


def test_start(module_setup):
    shutil.rmtree(LOG_DIR, ignore_errors=True)
    os.mkdir(LOG_DIR)


def test_activate_device(auth, user_domain):
    email, password, domain, release = auth

    response = requests.post('http://{0}:81/rest/activate'.format(user_domain),
                             data={'main_domain': SYNCLOUD_INFO, 'redirect_email': email, 'redirect_password': password,
                                   'user_domain': domain, 'device_username': DEVICE_USER, 'device_password': DEVICE_PASSWORD})
    assert response.status_code == 200, response.text
    global LOGS_SSH_PASSWORD
    LOGS_SSH_PASSWORD = DEVICE_PASSWORD


def test_running_platform_web(user_domain):
    print(check_output('nc -zv -w 1 {0} 80'.format(user_domain), shell=True))


def test_platform_rest(device_host):
    session = requests.session()
    session.mount('http://{0}'.format(device_host), HTTPAdapter(max_retries=5))
    response = session.get('http://{0}'.format(device_host), timeout=60)
    assert response.status_code == 200


# def test_external_mode(syncloud_session):
#     response = syncloud_session.get('http://localhost/rest/settings/set_external_access',
#                                     params={'external_access': 'true'},
#                                     timeout=60)
#     assert '"success": true' in response.text
#     assert response.status_code == 200


def test_install(app_archive_path, device_host):
    __local_install(app_archive_path, device_host)


def test_running_smtp(user_domain):
    print(check_output('nc -zv -w 1 {0} 25'.format(user_domain), shell=True))


def test_running_pop3(user_domain):
    cmd = 'nc -zv -w 1 {0} 110'.format(user_domain)
    func = lambda: check_output(cmd, shell=True)
    result=retry_func(func, message=cmd, retries=5)
    print(result)


def test_running_roundcube(user_domain):
    print(check_output('nc -zv -w 1 {0} 80'.format(user_domain), shell=True))


def test_dovecot_auth(user_domain, app_dir, data_dir):
    run_ssh(user_domain,
            '{0}/dovecot/bin/doveadm -c {1}/config/dovecot/dovecot.conf auth test {2} {3}'
            .format(app_dir, data_dir, DEVICE_USER, DEVICE_PASSWORD), password=DEVICE_PASSWORD)


def test_postfix_auth(user_domain):
    server = smtplib.SMTP(user_domain, timeout=10)
    server.set_debuglevel(1)
    server.login(DEVICE_USER, DEVICE_PASSWORD)


def test_mail_sending(user_domain, device_domain):
    server = smtplib.SMTP('{0}:587'.format(user_domain), timeout=10)
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


def test_filesystem_mailbox(user_domain):
    run_ssh(user_domain, 'find /opt/data/mail/box', password=DEVICE_PASSWORD)
    

def test_mail_receiving(user_domain):

    message_count = 0
    retry = 0
    retries = 3
    while retry < retries:
        message_count = get_message_count(user_domain)
        if message_count > 0:
            break
        retry += 1
        time.sleep(1)

    assert message_count == 1


def get_message_count(user_domain):
    imaplib.Debug = 4
    server = imaplib.IMAP4_SSL(user_domain)
    server.login(DEVICE_USER, DEVICE_PASSWORD)
    selected = server.select('inbox')
    server.logout()
    # assert selected[0] == 'OK'
    return int(selected[1][0])


def test_postfix_ldap_aliases(user_domain, app_dir, data_dir):
    run_ssh(user_domain,
            '{0}/postfix/usr/sbin/postmap -q {1}@{2} ldap:{3}/config/postfix/ldap-aliases.cf'
            .format(app_dir, DEVICE_USER, user_domain, data_dir), password=DEVICE_PASSWORD)

def test_imap_openssl_self_signed(user_domain, platform_data_dir, service_prefix):
    enable_self_signed_cert(user_domain, platform_data_dir, service_prefix)
    imap_openssl(user_domain, '-CAfile {0}/syncloud.ca.crt'.format(platform_data_dir), 'selfsigned')


def test_imap_openssl_real(user_domain, platform_data_dir, service_prefix):
    enable_real_cert(user_domain, platform_data_dir, service_prefix)
    imap_openssl(user_domain, '-CAfile /etc/certs/DST_Root_CA_X3.pem', 'real')
    
    
def imap_openssl(user_domain, ca_file, name):
    run_ssh(user_domain, "/openssl/bin/openssl version -a", password=DEVICE_PASSWORD)
    output = run_ssh(user_domain,
            "echo \"A Logout\" | /openssl/bin/openssl s_client {0} -connect localhost:143 -verify 3 -starttls imap".format(ca_file),
            password=DEVICE_PASSWORD)
    with open('{0}/openssl.{1}.log'.format(LOG_DIR, name), 'w') as f:
        f.write(output)


def test_imap_php_self_signed(user_domain, platform_data_dir, service_prefix, app_dir):

    enable_self_signed_cert(user_domain, platform_data_dir, service_prefix)
    imap_php(user_domain, platform_data_dir, app_dir, 'selfsigned')

    
def test_imap_php_real(user_domain, platform_data_dir, service_prefix, app_dir):

    enable_real_cert(user_domain, platform_data_dir, service_prefix)
    imap_php(user_domain, platform_data_dir, app_dir, 'selfsigned')
    
    
def imap_php(user_domain, platform_data_dir, app_dir, name):
  
    run_scp('{0}/config/roundcube/config.inc.php root@{1}:/'.format(roundcube_config, user_domain), password=LOGS_SSH_PASSWORD)
    run_scp('{0}/php.ssl.imap.test.php root@{1}:/'.format(DIR, user_domain, platform_data_dir), password=LOGS_SSH_PASSWORD)
    output = run_ssh(user_domain, "{0}/bin/php -f /php.ssl.imap.test.php".format(app_dir), password=DEVICE_PASSWORD, throw=False)
    with open('{0}/php.{1}.log'.format(LOG_DIR, name), 'w') as f:
        f.write(output)
        

def enable_self_signed_cert(user_domain, platform_data_dir, service_prefix):
    run_ssh(user_domain, 'cp {0}/config/tls/default.crt {0}/syncloud.crt'.format(platform_data_dir), password=LOGS_SSH_PASSWORD)
    run_ssh(user_domain, 'cp {0}/config/tls/default.key {0}/syncloud.key'.format(platform_data_dir), password=LOGS_SSH_PASSWORD)
    run_ssh(user_domain, "systemctl restart {0}mail-dovecot".format(service_prefix), password=DEVICE_PASSWORD)


def enable_real_cert(user_domain, platform_data_dir, service_prefix):
    run_scp('{0}/build.syncloud.info/fullchain.pem root@{1}:{2}/syncloud.crt'.format(DIR, user_domain, platform_data_dir), password=LOGS_SSH_PASSWORD)
    run_scp('{0}/build.syncloud.info/privkey.pem root@{1}:{2}/syncloud.key'.format(DIR, user_domain, platform_data_dir), password=LOGS_SSH_PASSWORD)
    run_ssh(user_domain, "systemctl restart {0}mail-dovecot".format(service_prefix), password=DEVICE_PASSWORD)


def test_upgrade(app_archive_path, user_domain):
    run_ssh(user_domain, '/opt/app/sam/bin/sam --debug remove mail', password=DEVICE_PASSWORD)
    __local_install(app_archive_path, user_domain)


def __local_install(app_archive_path, device_host):
    run_scp('{0} root@{1}:/app.tar.gz'.format(app_archive_path, device_host), password=DEVICE_PASSWORD)
    run_ssh(device_host, '/opt/app/sam/bin/sam --debug install /app.tar.gz', password=DEVICE_PASSWORD)
    time.sleep(3)
