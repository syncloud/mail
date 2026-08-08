import imaplib
import os
import pytest
import requests
import smtplib
import ssl
import time
from email.mime.text import MIMEText
from os.path import dirname, join
from ssl import SSLContext
from subprocess import check_output
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.installer import local_install

from test.util.helper import retry_func

TMP_DIR = '/tmp/syncloud'
DIR = dirname(__file__)
OPENSSL = "openssl"


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
    device.run_ssh('date', retries=100)
    device.run_ssh('snap watch --last=auto-refresh?', throw=False)
    device.run_ssh('mkdir {0}'.format(TMP_DIR), throw=False)


def test_activate_device(device, domain):
    device.run_ssh('snap run platform.cli config set redirect.domain {0}'.format(domain))
    device.run_ssh('snap run platform.cli config set redirect.api_url http://redirect.{0}'.format(domain))
    response = device.activate()
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


def faker_url(domain, path):
    return 'http://mail-relay.{0}/faker/{1}'.format(domain, path)


def faker_messages(domain):
    response = requests.get(faker_url(domain, 'messages'), timeout=10)
    assert response.status_code == 200, response.text
    return response.json()


def platform_session(device, domain, device_user, device_password):
    token = device.run_ssh('snap run platform.cli login {0} {1}'.format(device_user, device_password)).strip()
    session = requests.session()
    response = session.post('https://{0}/rest/login/token'.format(domain), verify=False,
                            allow_redirects=False, json={'token': token})
    assert response.status_code == 200, response.text
    return session


def set_mail_relay(device, domain, device_user, device_password, enabled):
    session = platform_session(device, domain, device_user, device_password)
    response = session.post('https://{0}/rest/mail_relay'.format(domain),
                            json={'enabled': enabled}, verify=False)
    assert response.status_code == 200, response.text
    assert response.json()['success'], response.text


def send_outgoing(app_domain, device_user, device_password, mail_domain, subject):
    server = smtplib.SMTP('{0}:587'.format(app_domain), timeout=10)
    server.ehlo()
    server.login(device_user, device_password)
    msg = MIMEText('relay body')
    msg['Subject'] = subject
    msg['From'] = '{0}@{1}'.format(device_user, mail_domain)
    msg['To'] = 'outside@example.com'
    server.sendmail(msg['From'], [msg['To']], msg.as_string())
    server.quit()


def test_mail_relay_disabled_does_not_use_relay(device, domain, app_domain, device_user, device_password):
    requests.delete(faker_url(domain, 'reset'), timeout=10)
    set_mail_relay(device, domain, device_user, device_password, False)
    send_outgoing(app_domain, device_user, device_password, domain, 'direct')
    time.sleep(10)
    assert faker_messages(domain) == []


def test_mail_relay_enabled_delivers_through_relay(device, domain, app_domain, device_user, device_password):
    requests.delete(faker_url(domain, 'reset'), timeout=10)
    set_mail_relay(device, domain, device_user, device_password, True)
    send_outgoing(app_domain, device_user, device_password, domain, 'relayed')

    messages = retry_func(lambda: assert_relayed(domain), message='relay delivery', retries=20, sleep=3)
    assert messages[0]['login'] == domain, messages
    assert messages[0]['recipients'] == ['outside@example.com'], messages
    assert 'relayed' in messages[0]['body'], messages


def assert_relayed(domain):
    messages = faker_messages(domain)
    assert len(messages) > 0, 'relay received nothing'
    return messages


TUNNEL_SOCKET = '/var/snap/mail/current/spool/public/tunnel'


@pytest.fixture(scope="session")
def socat(device):
    device.run_ssh(
        'command -v socat || (apt-get update -qq && apt-get install -y -qq socat)',
        throw=False)
    installed = device.run_ssh('command -v socat', throw=False)
    assert 'socat' in installed, installed


def tunnel_smtp(device, script):
    return device.run_ssh(
        '{{ {0} }} | timeout 20 socat - UNIX-CONNECT:{1}'.format(script, TUNNEL_SOCKET),
        throw=False)


def test_tunnel_listens_on_a_socket_not_a_port(device):
    listening = device.run_ssh("ss -lnt || true", throw=False)
    assert ':10025' not in listening, listening

    socket = device.run_ssh("ls -l {0}".format(TUNNEL_SOCKET), throw=False)
    assert 'srw' in socket, socket


def test_tunnel_delivers_to_a_local_user(socat, device, domain, device_user, app_domain,
                                         device_password):
    before = get_message_count(app_domain, device_user, device_password)
    out = tunnel_smtp(device, '''
printf 'EHLO tunnel.test\\r\\nMAIL FROM:<outside@example.com>\\r\\nRCPT TO:<{user}@{domain}>\\r\\nDATA\\r\\n'
sleep 2
printf 'Subject: tunnel-delivery\\r\\nFrom: outside@example.com\\r\\nTo: {user}@{domain}\\r\\n\\r\\nthrough the tunnel\\r\\n.\\r\\nQUIT\\r\\n'
'''.format(user=device_user, domain=domain))
    assert 'queued' in out, out

    after = retry_func(
        lambda: assert_arrived(app_domain, device_user, device_password, before),
        message='tunnel delivery', retries=20, sleep=3)
    assert after > before


def assert_arrived(app_domain, device_user, device_password, before):
    count = get_message_count(app_domain, device_user, device_password)
    assert count > before, 'nothing arrived through the tunnel'
    return count


def test_tunnel_refuses_to_relay_elsewhere(socat, device):
    out = tunnel_smtp(device, '''
printf 'EHLO tunnel.test\\r\\nMAIL FROM:<outside@example.com>\\r\\nRCPT TO:<victim@example.com>\\r\\nQUIT\\r\\n'
''')
    assert '554' in out or '550' in out, out


def latest_message(app_domain, device_user, device_password):
    server = imaplib.IMAP4_SSL(app_domain, ssl_context=(SSLContext(ssl.PROTOCOL_TLS)))
    server.login(device_user, device_password)
    server.select('inbox')
    _, data = server.search(None, 'SUBJECT', '"tunnel-delivery"')
    ids = data[0].split()
    assert ids, 'the tunnel delivered message is not in the mailbox'
    _, fetched = server.fetch(ids[-1], '(RFC822)')
    server.logout()
    return fetched[0][1].decode('utf-8', 'replace')


def test_tunnel_does_not_sign_incoming_mail(app_domain, domain, device_user, device_password):
    message = latest_message(app_domain, device_user, device_password)
    signed_by_us = 'd={0}'.format(domain)
    assert signed_by_us not in message, message[:2000]
