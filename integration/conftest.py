import pytest

SYNCLOUD_INFO = 'syncloud.info'
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'


def pytest_addoption(parser):
    parser.addoption("--email", action="store")
    parser.addoption("--password", action="store")
    parser.addoption("--domain", action="store")
    parser.addoption("--release", action="store")
    parser.addoption("--installer", action="store")
    parser.addoption("--device-host", action="store")
    parser.addoption("--app-archive-path", action="store")


@pytest.fixture(scope="session")
def auth(request):
    config = request.config
    return config.getoption("--email"), \
           config.getoption("--password"), \
           config.getoption("--domain"), \
           config.getoption("--release")


@pytest.fixture(scope='session')
def device_domain(request):
    return '{0}.{1}'.format(request.config.getoption("--domain"), SYNCLOUD_INFO)
    
    
@pytest.fixture(scope='session')
def user_domain(device_domain):
    return 'mail.{0}'.format(device_domain, SYNCLOUD_INFO)


@pytest.fixture(scope='session')
def app_archive_path(request):
    return request.config.getoption("--app-archive-path")


@pytest.fixture(scope='session')
def installer(request):
    return request.config.getoption("--installer")


@pytest.fixture(scope='session')
def device_host(request):
    return request.config.getoption("--device-host")
    

SAM_PLATFORM_DATA_DIR='/opt/data/platform'
SNAPD_PLATFORM_DATA_DIR='/var/snap/platform/common'
DATA_DIR=''

SAM_DATA_DIR='/opt/data/nextcloud'
SNAPD_DATA_DIR='/var/snap/nextcloud/common'
DATA_DIR=''

SAM_APP_DIR='/opt/app/nextcloud'
SNAPD_APP_DIR='/snap/nextcloud/current'
APP_DIR=''

@pytest.fixture(scope="session")
def platform_data_dir(installer):
    if installer == 'sam':
        return SAM_PLATFORM_DATA_DIR
    else:
        return SNAPD_PLATFORM_DATA_DIR
        
@pytest.fixture(scope="session")
def data_dir(installer):
    if installer == 'sam':
        return SAM_DATA_DIR
    else:
        return SNAPD_DATA_DIR


@pytest.fixture(scope="session")
def app_dir(installer):
    if installer == 'sam':
        return SAM_APP_DIR
    else:
        return SNAPD_APP_DIR


@pytest.fixture(scope="session")
def service_prefix(installer):
    if installer == 'sam':
        return ''
    else:
        return 'snap.'


@pytest.fixture(scope="session")
def ssh_env_vars(installer):
    if installer == 'sam':
        return ''
    if installer == 'snapd':
        return 'SNAP_COMMON={0} '.format(SNAPD_DATA_DIR)
