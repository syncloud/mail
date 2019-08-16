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

from syncloudlib.integration.installer import local_install, wait_for_rest, local_remove
from syncloudlib.integration.ssh import run_scp, run_ssh
from integration.util.helper import retry_func
TMP_DIR = '/tmp/syncloud'


@pytest.fixture(scope="session")
def module_setup(request, device, app_dir, data_dir, platform_data_dir, log_dir):
    def module_teardown(): 
        platform_log_dir = join(log_dir, 'platform')
        os.mkdir(platform_log_dir)
        device.scp_from_device('{0}/log/*'.format(platform_data_dir), platform_log_dir)
        mail_log_dir = join(log_dir, 'mail_log')
        os.mkdir(mail_log_dir)
        device.run_ssh('mkdir {0}'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/ > {1}/ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/dovecot/ > {1}/data.dovecot.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('{0}/postfix/usr/sbin/postfix.sh -c {1}/config/postfix -v status > {2}/postfix.status.teardowm.log 2>&1'.format(app_dir, data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/ > {1}/data.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/box/ > {1}/data.box.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/log/ > {1}/log.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/roundcubemail/ > {2}/roundcubemail.ls.log'.format(app_dir, data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/roundcubemail/config/ > {2}/roundcubemail.config.ls.log'.format(app_dir, data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/roundcubemail/logs/ > {2}/roundcubemail.logs.ls.log'.format(app_dir, data_dir, TMP_DIR), throw=False)
        device.run_ssh('journalctl > {1}/journalctl.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('netstat -nlp > {1}/netstat.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('DATA_DIR={1} {0}/bin/php -i > {2}/php.info.log'.format(app_dir, data_dir, TMP_DIR), throw=False)
    
        device.scp_from_device('{0}/log/*.log'.format(data_dir), mail_log_dir, throw=False)
        device.scp_from_device('/var/log/mail*', mail_log_dir, throw=False)
        device.scp_from_device('/var/log/mail/errors', '{0}/var.log.mail.errors.log'.format(mail_log_dir), throw=False)
        device.scp_from_device('/var/log/messages*', mail_log_dir, throw=False)
        device.scp_from_device('/var/log/*syslog*', mail_log_dir, throw=False) 
        config_dir = join(LOG_DIR, 'config')
        os.mkdir(config_dir)
        device.scp_from_device('{0}/config/*'.format(data_dir), config_dir, throw=False)

    request.addfinalizer(module_teardown)


def test_start(module_setup, device_host, log_dir, app, device):
    shutil.rmtree(log_dir, ignore_errors=True)
    os.mkdir(log_dir)
    add_host_alias(app, device_host)
    print(check_output('date', shell=True))
    device.run_ssh('date', retries=20)


def test_activate_device(device):
    response = device.activate()
    assert response.status_code == 200, response.text


def test_running_platform_web(app_domain):
    print(check_output('nc -zv -w 1 {0} 80'.format(app_domain), shell=True))


def test_platform_rest(device_host):
    session = requests.session()
    session.mount('https://{0}'.format(device_host), HTTPAdapter(max_retries=5))
    response = session.get('https://{0}'.format(device_host), timeout=60, verify=False)
    assert response.status_code == 200


def test_install(app_archive_path, device_host):
    local_install(device_host, DEVICE_PASSWORD, app_archive_path)


def test_access_change_event(app_domain):
    run_ssh(app_domain,
            '/snap/platform/current/python/bin/python /snap/mail/current/hooks/access-change.py',
             password=LOGS_SSH_PASSWORD)


def test_running_smtp(app_domain):
    print(check_output('nc -zv -w 1 {0} 25'.format(app_domain), shell=True))


def test_running_pop3(app_domain):
    cmd = 'nc -zv -w 1 {0} 110'.format(app_domain)
    func = lambda: check_output(cmd, shell=True)
    result=retry_func(func, message=cmd, retries=5)
    print(result)


def test_running_roundcube(app_domain):
    print(check_output('nc -zv -w 1 {0} 80'.format(app_domain), shell=True))


def test_postfix_status(app_domain, app_dir, data_dir):
    run_ssh(app_domain,
            '{0}/postfix/usr/sbin/postfix.sh -c {1}/config/postfix -v status > {1}/log/postfix.status.log 2>&1'.format(
                app_dir, data_dir),
            password=LOGS_SSH_PASSWORD, throw=False)


def test_postfix_check(app_domain, app_dir, data_dir):
    run_ssh(app_domain,
            '{0}/postfix/usr/sbin/postfix.sh -c {1}/config/postfix -v check > {1}/log/postfix.check.log 2>&1'.format(
                app_dir, data_dir),
            password=LOGS_SSH_PASSWORD, throw=False)


def test_dovecot_auth(app_domain, app_dir, data_dir):
    run_ssh(app_domain,
            '{0}/dovecot/bin/doveadm -D -c {1}/config/dovecot/dovecot.conf auth test {2} {3} > {1}/log/doveadm.auth.test.log 2>&1'
            .format(app_dir, data_dir, DEVICE_USER, DEVICE_PASSWORD), 
            password=DEVICE_PASSWORD, 
            env_vars='LD_LIBRARY_PATH={0}/dovecot/lib/dovecot DOVECOT_BINDIR={0}/dovecot/bin'.format(app_dir))


def test_postfix_smtp_shell(app_domain):
    print(check_output('{0}/expect.submission.sh {1} 25 {2} {3} > {4}/expect.smtp.log 2>&1'.format(
        DIR, app_domain, DEVICE_USER, DEVICE_PASSWORD, LOG_DIR), shell=True))


def test_postfix_submission_shell(app_domain):
    print(check_output('{0}/expect.submission.sh {1} 587 {2} {3} > {4}/expect.submission.log 2>&1'.format(
        DIR, app_domain, DEVICE_USER, DEVICE_PASSWORD, LOG_DIR), shell=True))


def test_postfix_auth(app_domain):
    server = smtplib.SMTP(app_domain, timeout=10)
    server.set_debuglevel(1)
    server.login(DEVICE_USER, DEVICE_PASSWORD)


def test_postfix_submission_lib(app_domain, device_domain):
    server = smtplib.SMTP('{0}:587'.format(app_domain), timeout=10)
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


def test_filesystem_mailbox(app_domain, data_dir):
        device.run_ssh('find {0}/box'.format(data_dir), password=DEVICE_PASSWORD)


def test_mail_receiving(app_domain):

    message_count = 0
    retry = 0
    retries = 3
    while retry < retries:
        message_count = retry_func(lambda: get_message_count(app_domain), message='get message count', retries=5)
        if message_count > 0:
            break
        retry += 1
        time.sleep(1)

    assert message_count == 1


def get_message_count(app_domain):
    imaplib.Debug = 4
    server = imaplib.IMAP4_SSL(app_domain)
    server.login(DEVICE_USER, DEVICE_PASSWORD)
    selected = server.select('inbox')
    server.logout()
    # assert selected[0] == 'OK'
    return int(selected[1][0])


def test_postfix_ldap_aliases(app_domain, app_dir, data_dir):
    run_ssh(app_domain,
            '{0}/postfix/usr/sbin/postmap -c {3}/config/postfix -q {1}@{2} ldap:{3}/config/postfix/ldap-aliases.cf'
            .format(app_dir, DEVICE_USER, app_domain, data_dir), password=DEVICE_PASSWORD)


def test_imap_openssl_generated(device, platform_data_dir, service_prefix):
    imap_openssl(app_domain, '-CAfile {0}/syncloud.ca.crt -CApath /etc/ssl/certs'.format(platform_data_dir),
                 'generated', 'localhost')


#def test_enable_real_cert(device, platform_data_dir, service_prefix):
#    run_scp('{0}/build.syncloud.info/fullchain.pem root@{1}:{2}/syncloud.crt'.format(DIR, app_domain, platform_data_dir), password=LOGS_SSH_PASSWORD)
#    run_scp('{0}/build.syncloud.info/privkey.pem root@{1}:{2}/syncloud.key'.format(DIR, app_domain, platform_data_dir), password=LOGS_SSH_PASSWORD)
#    device.run_ssh("systemctl restart {0}mail.dovecot".format(service_prefix))


#def test_imap_openssl_real(app_domain, platform_data_dir):
#    imap_openssl(app_domain, '-CAfile {0}/syncloud.ca.crt -CApath /etc/ssl/certs'.format(platform_data_dir),
#                 'real', 'build.syncloud.info')


def imap_openssl(device, ca, name, server_name):
    device.run_ssh("/openssl/bin/openssl version -a")
    output = device.run_ssh("echo \"A Logout\" | "
                                  "/openssl/bin/openssl s_client {0} -connect localhost:143 "
                                  "-servername {1} -verify 3 -starttls imap".format(ca, server_name))
    with open('{0}/openssl.{1}.log'.format(LOG_DIR, name), 'w') as f:
        f.write(output)
    assert 'Verify return code: 0 (ok)' in output


def test_upgrade(device_host, app_archive_path, app_domain):
    local_remove(device_host, DEVICE_PASSWORD, 'mail')
    local_install(device_host, DEVICE_PASSWORD, app_archive_path)

