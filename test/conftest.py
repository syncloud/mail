from os.path import dirname, join
import os
from syncloudlib.integration.conftest import *

@pytest.fixture(scope="session")
def project_dir():
    return join(dirname(__file__), '..')
