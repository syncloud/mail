import imaplib
import json
import os
import smtplib
import ssl
import time
from email.mime.text import MIMEText
from os.path import dirname, join
from subprocess import check_output

import pytest
import requests
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.installer import local_install
from syncloudlib.integration.ssh import run_scp

from test.util.helper import retry_func

TMP_DIR = '/tmp/syncloud'
DIR = dirname(__file__)
SERVICES = ['stalwart', 'bulwark', 'nginx']
TUNNEL_SOCKET = '/var/snap/mail/current/spool/public/tunnel'
ADMIN_SOCKET = '/var/snap/mail/current/stalwart/admin.sock'
PUBLIC_SOCKET = '/var/snap/mail/current/stalwart.sock'
SMTP_TOOL = '/tmp/smtp'
DOMAIN_GET = '/tmp/domain-get.json'
LISTENER_GET = '/tmp/listener-get.json'
GTUBE = 'XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X'


@pytest.fixture(scope="session")
def module_setup(request, device, data_dir, platform_data_dir, artifact_dir):
    def module_teardown():
        platform_log_dir = join(artifact_dir, 'platform')
        os.mkdir(platform_log_dir)
        device.scp_from_device('{0}/log/*'.format(platform_data_dir), platform_log_dir)
        device.run_ssh('ls -la /var/snap/mail/current/ > {0}/data.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /var/snap/mail/current/migration > {0}/migration.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ss -nlpx > {0}/sockets.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ss -nltp > {0}/ports.log'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl > {0}/journalctl.log'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl -u snap.mail.stalwart > {0}/stalwart.log'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl -u snap.mail.bulwark > {0}/bulwark.log'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl -u snap.mail.migrate > {0}/migrate.log'.format(TMP_DIR), throw=False)
        device.run_ssh('cp -r /var/snap/mail/current/config {0}/config'.format(TMP_DIR), throw=False)
        device.scp_from_device('{0}/*'.format(TMP_DIR), artifact_dir)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, device_host, app, domain, device):
    add_host_alias(app, device_host, domain)
    device.run_ssh('date', retries=100)
    device.run_ssh('snap watch --last=auto-refresh?', throw=False)
    device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)


def test_activate_device(device, domain):
    device.run_ssh('snap run platform.cli config set redirect.domain {0}'.format(domain))
    device.run_ssh('snap run platform.cli config set redirect.api_url http://redirect.{0}'.format(domain))
    response = device.activate()
    assert response.status_code == 200, response.text


def test_platform_key_is_private(device):
    device.run_ssh('chmod 600 /var/snap/platform/current/syncloud.key')


def test_install(app_archive_path, domain, device_password):
    local_install(domain, device_password, app_archive_path)


@pytest.mark.parametrize('port', [25, 587, 465, 143, 993, 110, 995, 4190])
def test_port(device_host, port):
    cmd = 'nc -zv -w 1 {0} {1}'.format(device_host, port)
    retry_func(lambda: check_output(cmd, shell=True), message=cmd, retries=10, sleep=5)


def test_web(app_domain):
    retry_func(lambda: assert_status('https://{0}/'.format(app_domain), 200), message='web', retries=30, sleep=5)


@pytest.mark.parametrize('service', SERVICES)
def test_service_started_cleanly(device, service):
    restarts = device.run_ssh('systemctl show -p NRestarts --value snap.mail.{0}.service'.format(service))
    assert restarts.strip() == '0', service


def test_services_run_as_mail(device):
    owners = device.run_ssh("ps -eo user:20,args | grep -E '/snap/mail/[^ ]*/(stalwart/stalwart|node/|nginx/)' | grep -v grep")
    lines = [line.split(None, 1) for line in owners.strip().splitlines()]
    assert lines, owners
    assert {user for user, _ in lines} == {'mail'}, owners


def test_internal_traffic_uses_sockets(device):
    sockets = device.run_ssh('ss -nlx')
    for socket in ['/var/snap/mail/current/stalwart.sock', '/var/snap/mail/current/bulwark.sock',
                   '/var/snap/mail/common/web.socket', TUNNEL_SOCKET, ADMIN_SOCKET]:
        assert socket in sockets, socket
    ports = device.run_ssh('ss -nlt')
    for port in [':8080 ', ':3000 ']:
        assert port not in ports, ports


def test_tls_key_is_private(device):
    assert device.run_ssh("stat -c '%U:%G %a' /var/snap/mail/current/stalwart/tls/syncloud.key").strip() == 'mail:mail 600'


def test_admin_socket_is_private(device):
    assert device.run_ssh("stat -c '%U:%G %a' {0}".format(ADMIN_SOCKET)).strip() == 'mail:mail 660'


def test_admin_password_is_gone(device):
    assert 'admin.password' not in device.run_ssh('ls /var/snap/mail/current/stalwart')


@pytest.fixture(scope="session")
def domain_get(device, device_host):
    run_scp('{0}/jmap/domain-get.json root@{1}:{2}'.format(DIR, device_host, DOMAIN_GET),
            password=device.ssh_password)
    return DOMAIN_GET


@pytest.fixture(scope="session")
def listener_get(device, device_host):
    run_scp('{0}/jmap/listener-get.json root@{1}:{2}'.format(DIR, device_host, LISTENER_GET),
            password=device.ssh_password)
    return LISTENER_GET


def test_listeners_on_unix_sockets(device, listener_get):
    response = device.run_ssh('curl -s --unix-socket {0} -H Content-Type:application/json -d @{1} http://localhost/jmap/'.format(
        ADMIN_SOCKET, listener_get))
    listeners = {listener['name']: list(listener['bind']) for listener in json.loads(response)['methodResponses'][0][1]['list']}
    assert listeners.pop('http') == ['unix:{0}:443'.format(PUBLIC_SOCKET)], response
    assert listeners.pop('tunnel') == ['unix:{0}:25'.format(TUNNEL_SOCKET)], response
    assert not any(address.startswith('unix:') for bind in listeners.values() for address in bind), response


def test_admin_socket_is_admin(device, domain, domain_get):
    response = device.run_ssh('curl -s --unix-socket {0} -H Content-Type:application/json -d @{1} http://localhost/jmap/'.format(
        ADMIN_SOCKET, domain_get))
    assert '"x:Domain/get"' in response, response
    assert '"{0}"'.format(domain) in response, response


def test_admin_socket_session_has_account(device):
    response = device.run_ssh('curl -s --unix-socket {0} http://localhost/jmap/session'.format(ADMIN_SOCKET))
    assert '"primaryAccounts":{"' in response, response


def test_public_socket_is_not_admin(device, domain_get):
    response = device.run_ssh("curl -s -o /dev/null -w '%{{http_code}}' --unix-socket {0} -H Content-Type:application/json -d @{1} http://localhost/jmap/".format(
        PUBLIC_SOCKET, domain_get))
    assert response.strip() == '401', response


def test_anonymous_jmap_session_has_no_accounts(app_domain):
    response = requests.get('https://{0}/jmap/session'.format(app_domain), verify=False)
    assert response.status_code == 200, response.text
    assert response.json()['accounts'] == {}, response.text


def test_jmap_session(app_domain, device_user, device_password, domain):
    response = requests.get('https://{0}/jmap/session'.format(app_domain), verify=False,
                            auth=(device_user, device_password))
    assert response.status_code == 200, response.text
    assert response.json()['username'] == '{0}@{1}'.format(device_user, domain), response.text


def test_stalwart_admin_ui(app_domain):
    response = requests.get('https://{0}/stalwart/'.format(app_domain), verify=False)
    assert response.status_code == 200, response.text
    assert '<base href="/stalwart/"' in response.text, response.text


def test_webmail_admin_is_bulwark(app_domain):
    response = requests.get('https://{0}/admin'.format(app_domain), verify=False)
    assert response.status_code == 200, response.text
    assert '<base href=' not in response.text, response.text[:500]


def test_oidc_client_is_registered(device, app_domain):
    config = device.run_ssh('cat /var/snap/platform/current/config/authelia/config.yml')
    assert "client_id: 'mail'" in config, config
    assert "- 'https://{0}/en/auth/callback'".format(app_domain) in config, config


@pytest.mark.parametrize('kind', ['card', 'cal'])
def test_dav(app_domain, device_user, device_password, domain, kind):
    response = requests.request('PROPFIND', 'https://{0}/dav/{1}/{2}@{3}/'.format(app_domain, kind, device_user, domain),
                                verify=False, auth=(device_user, device_password), headers={'Depth': '1'})
    assert response.status_code == 207, response.text


def test_submission_requires_tls(app_domain, device_user, device_password):
    server = smtplib.SMTP(app_domain, 587, timeout=10)
    server.ehlo()
    assert not server.has_extn('auth'), server.esmtp_features
    server.quit()


def test_submission(app_domain, domain, device_user, device_password):
    send(app_domain, device_user, device_password, '{0}@{1}'.format(device_user, domain), 'test subject', 'test')
    retry_func(lambda: assert_in(app_domain, device_user, device_password, 'INBOX', 'test subject'),
               message='submission delivery', retries=20, sleep=3)


def test_imap_certificate(device, artifact_dir):
    output = device.run_ssh("echo \"A Logout\" | openssl s_client "
                            "-CAfile /var/snap/platform/current/syncloud.ca.crt "
                            "-CApath /etc/ssl/certs "
                            "-connect localhost:143 "
                            "-servername syncloud "
                            "-verify 3 "
                            "-starttls imap", throw=False)
    with open('{0}/openssl.log'.format(artifact_dir), 'w') as f:
        f.write(output)
    assert 'Verify return code: 0 (ok)' in output


def test_pop3(app_domain, device_user, device_password):
    import poplib
    server = poplib.POP3(app_domain, 110, timeout=10)
    server.stls(context=insecure())
    server.user(device_user)
    server.pass_(device_password)
    count, _ = server.stat()
    server.quit()
    assert count > 0


def test_access_change(device):
    device.run_ssh('snap run mail.access-change > {0}/access-change.hook.log'.format(TMP_DIR))


def test_storage_change(device):
    device.run_ssh('snap run mail.storage-change > {0}/storage-change.hook.log'.format(TMP_DIR))


def test_certificate_change(device, device_host):
    device.run_ssh('snap run mail.certificate-change > {0}/certificate-change.hook.log'.format(TMP_DIR))
    retry_func(lambda: check_output('nc -zv -w 1 {0} 993'.format(device_host), shell=True),
               message='imaps after certificate change', retries=20, sleep=3)


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


def test_mail_relay_disabled_does_not_use_relay(device, domain, app_domain, device_user, device_password):
    requests.delete(faker_url(domain, 'reset'), timeout=10)
    set_mail_relay(device, domain, device_user, device_password, False)
    send(app_domain, device_user, device_password, 'outside@example.com', 'direct', 'relay body')
    time.sleep(10)
    assert faker_messages(domain) == []


def test_mail_relay_enabled_delivers_through_relay(device, domain, app_domain, device_user, device_password):
    requests.delete(faker_url(domain, 'reset'), timeout=10)
    set_mail_relay(device, domain, device_user, device_password, True)
    send(app_domain, device_user, device_password, 'outside@example.com', 'relayed', 'relay body')

    messages = retry_func(lambda: assert_relayed(domain), message='relay delivery', retries=20, sleep=3)
    assert messages[0]['login'] == domain, messages
    assert messages[0]['recipients'] == ['outside@example.com'], messages
    assert 'relayed' in messages[0]['body'], messages
    assert 'd={0}'.format(domain) in messages[0]['body'], messages[0]['body']
    assert 's=mail' in messages[0]['body'], messages[0]['body']


def assert_relayed(domain):
    messages = faker_messages(domain)
    assert len(messages) > 0, 'relay received nothing'
    return messages


@pytest.fixture(scope="session")
def smtp(device, device_host):
    run_scp('{0}/../build/smtp root@{1}:{2}'.format(DIR, device_host, SMTP_TOOL),
            password=device.ssh_password)
    device.run_ssh('chmod +x {0}'.format(SMTP_TOOL))
    return SMTP_TOOL


def tunnel_smtp(device, sender, recipient, subject='', body='', proxy=''):
    command = "{0} -socket {1} -from '{2}' -rcpt '{3}'".format(SMTP_TOOL, TUNNEL_SOCKET, sender, recipient)
    if subject:
        command += " -subject '{0}' -body '{1}'".format(subject, body)
    if proxy:
        command += " -proxy {0}".format(proxy)
    return device.run_ssh(command, throw=False)


def test_tunnel_delivers_to_a_local_user(smtp, device, domain, device_user, app_domain, device_password):
    out = tunnel_smtp(device, 'outside@example.com', '{0}@{1}'.format(device_user, domain),
                      subject='tunnel-delivery', body='through the tunnel', proxy='192.0.2.77')
    assert 'queued' in out.lower(), out
    retry_func(lambda: delivered(app_domain, device_user, device_password, 'tunnel-delivery'),
               message='tunnel delivery', retries=20, sleep=3)


def test_tunnel_takes_the_proxied_client_address(app_domain, device_user, device_password):
    message = delivered(app_domain, device_user, device_password, 'tunnel-delivery')
    assert '[192.0.2.77]' in message.split('\r\n\r\n')[0], message[:3000]
    assert 'client-ip=192.0.2.77' in message, message[:3000]


def test_tunnel_does_not_sign_incoming_mail(app_domain, domain, device_user, device_password):
    message = delivered(app_domain, device_user, device_password, 'tunnel-delivery')
    assert 'd={0}'.format(domain) not in message, message[:3000]


def test_tunnel_refuses_to_relay_elsewhere(smtp, device):
    out = tunnel_smtp(device, 'outside@example.com', 'victim@example.com', proxy='192.0.2.78')
    assert '550' in out or '554' in out or '553' in out, out


def test_spam_does_not_reach_the_inbox(smtp, device, domain, device_user, app_domain, device_password):
    tunnel_smtp(device, 'spammer@example.com', '{0}@{1}'.format(device_user, domain),
                subject='gtube-probe', body=GTUBE, proxy='192.0.2.79')
    time.sleep(10)
    assert not search(app_domain, device_user, device_password, 'INBOX', 'gtube-probe')


def test_owner_mail_is_not_filtered(app_domain, domain, device_user, device_password):
    send(app_domain, device_user, device_password, '{0}@{1}'.format(device_user, domain), 'owner-submission', 'owner')
    retry_func(lambda: assert_in(app_domain, device_user, device_password, 'INBOX', 'owner-submission'),
               message='owner submission', retries=20, sleep=3)
    assert not search(app_domain, device_user, device_password, 'Junk Mail', 'owner-submission')


def insecure():
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def send(app_domain, user, password, recipient, subject, body):
    server = smtplib.SMTP(app_domain, 587, timeout=10)
    server.ehlo()
    server.starttls(context=insecure())
    server.ehlo()
    server.login(user, password)
    message = MIMEText(body)
    message['Subject'] = subject
    message['From'] = '{0}@{1}'.format(user, app_domain.split('.', 1)[1])
    message['To'] = recipient
    server.send_message(message)
    server.quit()


def imap(app_domain, user, password):
    server = imaplib.IMAP4_SSL(app_domain, ssl_context=insecure())
    server.login(user, password)
    return server


def search(app_domain, user, password, folder, subject):
    server = imap(app_domain, user, password)
    try:
        status, _ = server.select('"{0}"'.format(folder))
        if status != 'OK':
            return []
        _, data = server.search(None, 'SUBJECT', '"{0}"'.format(subject))
        return data[0].split()
    finally:
        server.logout()


def fetch(app_domain, user, password, folder, subject):
    server = imap(app_domain, user, password)
    try:
        server.select('"{0}"'.format(folder))
        _, data = server.search(None, 'SUBJECT', '"{0}"'.format(subject))
        ids = data[0].split()
        assert ids, subject
        _, fetched = server.fetch(ids[-1], '(RFC822)')
        return fetched[0][1].decode('utf-8', 'replace')
    finally:
        server.logout()


def delivered(app_domain, user, password, subject):
    for folder in ['INBOX', 'Junk Mail']:
        if search(app_domain, user, password, folder, subject):
            return fetch(app_domain, user, password, folder, subject)
    raise AssertionError('{0} was not delivered'.format(subject))


def assert_in(app_domain, user, password, folder, subject):
    assert search(app_domain, user, password, folder, subject), '{0} is not in {1}'.format(subject, folder)


def assert_status(url, status):
    response = requests.get(url, verify=False, allow_redirects=False)
    assert response.status_code == status, '{0} {1}'.format(response.status_code, response.text[:500])
