import imaplib
import os
import pytest
import smtplib
import ssl
import time
from email.mime.text import MIMEText
from os.path import dirname, join
from ssl import SSLContext
from subprocess import check_output
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.installer import local_install

from integration.util.helper import retry_func

TMP_DIR = '/tmp/syncloud'
DIR = dirname(__file__)
OPENSSL = join(DIR, "openssl", "bin", "openssl")


@pytest.fixture(scope="session")
def module_setup(request, device, app_dir, data_dir, platform_data_dir, artifact_dir, domain):
    def module_teardown(): 
        platform_log_dir = join(artifact_dir, 'platform')
        os.mkdir(platform_log_dir)
        device.scp_from_device('{0}/log/*'.format(platform_data_dir), platform_log_dir)
        mail_log_dir = join(artifact_dir, 'mail_log')
        os.mkdir(mail_log_dir)
        device.run_ssh('ls -la {0}/ > {1}/ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/dovecot/ > {1}/data.dovecot.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('{0}/postfix/bin/postfix.sh -c {1}/config/postfix -v status > '
                       '{2}/postfix.status.teardowm.log 2>&1'.format(app_dir, data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/ > {1}/data.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/box/ > {1}/data.box.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/log/ > {1}/log.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/roundcubemail/ > {2}/roundcubemail.ls.log'
                       .format(app_dir, data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/roundcubemail/config/ > {2}/roundcubemail.config.ls.log'
                       .format(app_dir, data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/roundcubemail/logs/ > {2}/roundcubemail.logs.ls.log'
                       .format(app_dir, data_dir, TMP_DIR), throw=False)
        device.run_ssh('DATA_DIR={1} {0}/bin/php.sh -i > {2}/php.info.log'.format(app_dir, data_dir, TMP_DIR), throw=False)
    
        device.scp_from_device('{0}/log/*.log'.format(data_dir), mail_log_dir, throw=False)
        device.run_ssh('ls -la /var/log/ > {0}/var.log.ls.log'.format(TMP_DIR), throw=False)
        device.scp_from_device('/var/log/mail.err', '{0}/var.log.mail.err.log'.format(mail_log_dir), throw=False)
        device.scp_from_device('/var/log/mail.info', '{0}/var.log.mail.info.log'.format(mail_log_dir), throw=False)
        device.scp_from_device('/var/log/mail.log', '{0}/var.log.mail.log.log'.format(mail_log_dir), throw=False)
        device.scp_from_device('/var/log/mail.warn', '{0}/var.log.mail.warn.log'.format(mail_log_dir), throw=False)
        device.scp_from_device('/var/log/mail/errors', '{0}/var.log.mail.errors.log'.format(mail_log_dir), throw=False)
        device.run_ssh('netstat -nlp > {0}/netstat.log'.format(mail_log_dir), throw=False)
        device.run_ssh('journalctl > {0}/journalctl.log'.format(mail_log_dir), throw=False)
        device.run_ssh('cp /var/log/syslog {0}/syslog.log'.format(mail_log_dir), throw=False)
        device.run_ssh('cp /var/log/messages {0}/messages.log'.format(mail_log_dir), throw=False)
        device.run_ssh('ls -la {0}/opendkim/keys > {1}/opendkim.keys.log'.format(data_dir, mail_log_dir), throw=False)
        device.run_ssh('ls -la {0}/opendkim/keys/{1} > {2}/opendkim.keys.domain.log'
                       .format(data_dir, domain, mail_log_dir), throw=False)
        device.run_ssh('cp {0}/opendkim/keys/{1}/mail.txt {2}/opendkim.keys.domain.mail.txt.log'
                       .format(data_dir, domain, mail_log_dir), throw=False)
        device.run_ssh('cp {0}/opendkim/keys/{1}/mail.private {2}/opendkim.keys.domain.mail.private.log'
                       .format(data_dir, domain, mail_log_dir), throw=False)
        config_dir = join(artifact_dir, 'config')
        os.mkdir(config_dir)
        device.scp_from_device('{0}/config/*'.format(data_dir), config_dir, throw=False)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, device_host, app, domain, device):
    add_host_alias(app, device_host, domain)
    print(check_output('date', shell=True))
    device.run_ssh('date', retries=20)
    device.run_ssh('mkdir {0}'.format(TMP_DIR), throw=False)


def test_activate_device(device):
    response = device.activate_custom()
    assert response.status_code == 200, response.text


def test_install(app_archive_path, domain, device_password):
    local_install(domain, device_password, app_archive_path)


def test_running_smtp(device_host):
    cmd = 'nc -zv -w 1 {0} 25'.format(device_host)
    print(retry_func(lambda: check_output(cmd, shell=True), message=cmd, retries=5, sleep=10))


def test_running_pop3(device_host):
    cmd = 'nc -zv -w 1 {0} 110'.format(device_host)
    print(retry_func(lambda: check_output(cmd, shell=True), message=cmd, retries=5, sleep=10))


def test_running_roundcube(app_domain):
    print(check_output('nc -zv -w 1 {0} 443'.format(app_domain), shell=True))


def test_postfix_status(device, app_dir, data_dir):
    device.run_ssh(
            '{0}/postfix/bin/postfix.sh -c {1}/config/postfix -v status > {1}/log/postfix.status.log 2>&1'.format(
                app_dir, data_dir), throw=False)


def test_postfix_check(device, app_dir, data_dir):
    device.run_ssh(
            '{0}/postfix/bin/postfix.sh -c {1}/config/postfix -v check > {1}/log/postfix.check.log 2>&1'.format(
                app_dir, data_dir), throw=False)


def test_dovecot_auth(device, app_dir, data_dir, device_user, device_password):
    device.run_ssh(
            '{0}/dovecot/bin/doveadm.sh -D -c {1}/config/dovecot/dovecot.conf auth test {2} {3} > '
            '{1}/log/doveadm.auth.test.log 2>&1'
            .format(app_dir, data_dir, device_user, device_password), 
            env_vars='DOVECOT_BINDIR={0}/dovecot/bin'.format(app_dir))


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


def test_postfix_submission_lib(app_domain, domain, device_user, device_password):
    server = smtplib.SMTP('{0}:587'.format(app_domain), timeout=10)
    server.set_debuglevel(1)
    server.ehlo()
    # server.starttls()
    server.login(device_user, device_password)
    msg = MIMEText('test')
    mail_from = '{0}@{1}'.format(device_user, domain)
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
        message_count = retry_func(lambda: get_message_count(app_domain, device_user, device_password),
                                   message='get message count', retries=5)
        if message_count > 0:
            break
        retry += 1
        time.sleep(1)

    assert message_count == 1


def get_message_count(app_domain, device_user, device_password):
    imaplib.Debug = 4
    server = imaplib.IMAP4_SSL(app_domain, ssl_context=(SSLContext(ssl.PROTOCOL_TLS)))
    server.login(device_user, device_password)
    selected = server.select('inbox')
    server.logout()
    # assert selected[0] == 'OK'
    return int(selected[1][0])


def test_postfix_ldap_aliases(device, app_domain, app_dir, data_dir, device_user):
    device.run_ssh(
            '{0}/postfix/bin/postmap.sh -c {3}/config/postfix -q {1}@{2} ldap:{3}/config/postfix/ldap-aliases.cf'
            .format(app_dir, device_user, app_domain, data_dir))


def test_imap_openssl(device, artifact_dir):
    
    device.run_ssh("{0} version -a".format(OPENSSL))
    output = device.run_ssh("echo \"A Logout\" | "
                            "{0} s_client "
                            "-CAfile /var/snap/platform/current/syncloud.ca.crt "
                            "-CApath /etc/ssl/certs "
                            "-connect localhost:143 "
                            "-servername syncloud "
                            "-verify 3 "
                            "-starttls imap".format(OPENSSL))
    with open('{0}/openssl.log'.format(artifact_dir), 'w') as f:
        f.write(output)
    assert 'Verify return code: 0 (ok)' in output


def test_access_change(device):
    device.run_ssh('snap run mail.access-change > {0}/access-change.hook.log'.format(TMP_DIR))


def test_storage_change(device):
    device.run_ssh('snap run mail.storage-change > {0}/storage-change.hook.log'.format(TMP_DIR))


def test_certificate_change(device):
    device.run_ssh('snap run mail.certificate-change > {0}/certificate-change.hook.log'.format(TMP_DIR))
