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

from syncloudlib.integration.hosts import add_host_alias_by_ip
from syncloudlib.integration.installer import local_install, local_remove, wait_for_installer
from syncloudlib.integration.ssh import run_scp, run_ssh
from integration.util.helper import retry_func
TMP_DIR = '/tmp/syncloud'
DIR = dirname(__file__)
OPENSSL = join(DIR, "openssl", "bin", "openssl")


@pytest.fixture(scope="session")
def module_setup(request, device, app_dir, data_dir, platform_data_dir, artifact_dir):
    def module_teardown(): 
        platform_log_dir = join(artifact_dir, 'platform')
        os.mkdir(platform_log_dir)
        device.scp_from_device('{0}/log/*'.format(platform_data_dir), platform_log_dir)
        mail_log_dir = join(artifact_dir, 'mail_log')
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
        device.run_ssh('DATA_DIR={1} {0}/bin/php -i > {2}/php.info.log'.format(app_dir, data_dir, TMP_DIR), throw=False)
    
        device.scp_from_device('{0}/log/*.log'.format(data_dir), mail_log_dir, throw=False)
        device.scp_from_device('/var/log/mail*', mail_log_dir, throw=False)
        device.scp_from_device('/var/log/mail/errors', '{0}/var.log.mail.errors.log'.format(mail_log_dir), throw=False)
        device.run_ssh('netstat -nlp > {0}/netstat.log'.format(mail_log_dir), throw=False)
        device.run_ssh('journalctl > {0}/journalctl.log'.format(mail_log_dir), throw=False)
        device.run_ssh('cp /var/log/syslog {0}/syslog.log'.format(mail_log_dir), throw=False)
        device.run_ssh('cp /var/log/messages {0}/messages.log'.format(mail_log_dir), throw=False)
        device.run_ssh('ls -la {0}/opendkim/keys {1}/opendkim.keys.log'.format(data_dir, mail_log_dir), throw=False)
        config_dir = join(artifact_dir, 'config')
        os.mkdir(config_dir)
        device.scp_from_device('{0}/config/*'.format(data_dir), config_dir, throw=False)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, device_host, app, domain, device):
    add_host_alias_by_ip(app, domain, device_host)
    print(check_output('date', shell=True))
    device.run_ssh('date', retries=20)


def test_activate_device(device):
    response = device.activate()
    assert response.status_code == 200, response.text


def test_platform_rest(device_host):
    session = requests.session()
    session.mount('https://{0}'.format(device_host), HTTPAdapter(max_retries=5))
    response = session.get('https://{0}'.format(device_host), timeout=60, verify=False)
    assert response.status_code == 200


def test_install(app_archive_path, device_host, device_password, device_session):
    local_install(device_host, device_password, app_archive_path)
    wait_for_installer(device_session, device_host)


def test_access_change_event(device, app_domain):
    device.run_ssh(
            '/snap/platform/current/python/bin/python /snap/mail/current/hooks/access-change.py')


def test_running_smtp(device_host):
    cmd = 'nc -zv -w 1 {0} 25'.format(device_host)
    func = lambda: check_output(cmd, shell=True)
    result=retry_func(func, message=cmd, retries=5, sleep=10)
    print(result)


def test_running_pop3(device_host):
    cmd = 'nc -zv -w 1 {0} 110'.format(device_host)
    func = lambda: check_output(cmd, shell=True)
    result=retry_func(func, message=cmd, retries=5, sleep=10)
    print(result)


def test_running_roundcube(app_domain):
    print(check_output('nc -zv -w 1 {0} 443'.format(app_domain), shell=True))


def test_postfix_status(device, app_domain, app_dir, data_dir):
    device.run_ssh(
            '{0}/postfix/usr/sbin/postfix.sh -c {1}/config/postfix -v status > {1}/log/postfix.status.log 2>&1'.format(
                app_dir, data_dir), throw=False)


def test_postfix_check(device, app_dir, data_dir):
    device.run_ssh(
            '{0}/postfix/usr/sbin/postfix.sh -c {1}/config/postfix -v check > {1}/log/postfix.check.log 2>&1'.format(
                app_dir, data_dir), throw=False)


def test_dovecot_auth(device, app_dir, data_dir, device_user, device_password):
    device.run_ssh(
            '{0}/dovecot/bin/doveadm -D -c {1}/config/dovecot/dovecot.conf auth test {2} {3} > {1}/log/doveadm.auth.test.log 2>&1'
            .format(app_dir, data_dir, device_user, device_password), 
            env_vars='LD_LIBRARY_PATH={0}/dovecot/lib/dovecot DOVECOT_BINDIR={0}/dovecot/bin'.format(app_dir))


def test_postfix_smtp_shell(app_domain, device_user, device_password, artifact_dir):
    print(check_output('{0}/expect.submission.sh {1} 25 {2} {3} > {4}/expect.smtp.log 2>&1'.format(
        DIR, app_domain, device_user, device_password, artifact_dir), shell=True))


def test_postfix_submission_shell(app_domain, device_user, device_password, artifact_dir):
    print(check_output('{0}/expect.submission.sh {1} 587 {2} {3} > {4}/expect.submission.log 2>&1'.format(
        DIR, app_domain, device_user, device_password, artifact_dir), shell=True))


def test_postfix_auth(app_domain, device_user, device_password):
    server = smtplib.SMTP(app_domain, timeout=10)
    server.set_debuglevel(1)
    server.login(device_user, device_password)


def test_postfix_submission_lib(app_domain, device_domain, device_user, device_password):
    server = smtplib.SMTP('{0}:587'.format(app_domain), timeout=10)
    server.set_debuglevel(1)
    server.ehlo()
    #server.starttls()
    server.login(device_user, device_password)
    msg = MIMEText('test')
    mail_from = '{0}@{1}'.format(device_user, device_domain)
    mail_to = mail_from
    msg['Subject'] = 'test subject'
    msg['From'] = mail_from
    msg['To'] = mail_to
    server.sendmail(mail_from, [mail_to], msg.as_string())
    server.quit()


def test_filesystem_mailbox(device, data_dir):
    device.run_ssh('find {0}/box'.format(data_dir))


def test_mail_receiving(app_domain, device_user, device_password):

    message_count = 0
    retry = 0
    retries = 3
    while retry < retries:
        message_count = retry_func(lambda: get_message_count(app_domain, device_user, device_password), message='get message count', retries=5)
        if message_count > 0:
            break
        retry += 1
        time.sleep(1)

    assert message_count == 1


def get_message_count(app_domain, device_user, device_password):
    imaplib.Debug = 4
    server = imaplib.IMAP4_SSL(app_domain)
    server.login(device_user, device_password)
    selected = server.select('inbox')
    server.logout()
    # assert selected[0] == 'OK'
    return int(selected[1][0])


def test_postfix_ldap_aliases(device, app_domain, app_dir, data_dir, device_user, device_password):
    device.run_ssh(
            '{0}/postfix/usr/sbin/postmap -c {3}/config/postfix -q {1}@{2} ldap:{3}/config/postfix/ldap-aliases.cf'
            .format(app_dir, device_user, app_domain, data_dir))


def test_imap_openssl(device, platform_data_dir, artifact_dir):
    
    device.run_ssh("{0} version -a".format(OPENSSL))
    output = device.run_ssh("echo \"A Logout\" | "
                                  "{0} s_client -CAfile {1}/syncloud.ca.crt -CApath /etc/ssl/certs -connect localhost:143 "
                                  "-servername localhost -verify 3 -starttls imap".format(OPENSSL, platform_data_dir))
    with open('{0}/openssl.log'.format(artifact_dir), 'w') as f:
        f.write(output)
    assert 'Verify return code: 0 (ok)' in output


def test_remove(device_session, device_host):
    response = device_session.get('https://{0}/rest/remove?app_id=mail'.format(device_host),
                                  allow_redirects=False, verify=False)
    assert response.status_code == 200, response.text
    wait_for_installer(device_session, device_host)


def test_reinstall(app_archive_path, app_domain, device_password):
    local_install(app_domain, device_password, app_archive_path)

