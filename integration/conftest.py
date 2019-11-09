from os.path import dirname, join, exists
import os
from syncloudlib.integration.conftest import *

DIR = dirname(__file__)


@pytest.fixture(scope="session")
def log_dir():
    return join(DIR, 'log')


@pytest.fixture(scope="session")
def artifact_dir():
    dir =  join(DIR, '..', 'artifact')
    if not exists(dir):
        os.mkdir(dir)
    return dir


@pytest.fixture(scope="session")
def screenshot_dir(artifact_dir):
    dir = join(artifact_dir, 'screenshot')
    if not exists(dir):
        os.mkdir(dir)
    return dir


