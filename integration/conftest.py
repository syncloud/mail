import pytest


SYNCLOUD_INFO = 'syncloud.info'

def pytest_addoption(parser):
    parser.addoption("--email", action="store")
    parser.addoption("--password", action="store")
    parser.addoption("--domain", action="store")
    parser.addoption("--release", action="store")
    parser.addoption("--app-version", action="store")
    parser.addoption("--arch", action="store")


@pytest.fixture(scope="session")
def auth(request):
    config = request.config
    return config.getoption("--email"), \
           config.getoption("--password"), \
           config.getoption("--domain"), \
           config.getoption("--release"), \
           config.getoption("--app-version"), \
           config.getoption("--arch")


@pytest.fixture(scope='module')
def device_domain(auth):
    email, password, domain, release, version, arch = auth
    return '{0}.{1}'.format(domain, SYNCLOUD_INFO)


@pytest.fixture(scope='module')
def user_domain(device_domain):
    return 'mail.{0}'.format(device_domain)



