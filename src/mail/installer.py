from os import environ
from os.path import isdir, join
import shutil
from subprocess import check_output

from syncloud_app import logger

from syncloud_platform.systemd.systemctl import remove_service, add_service
from syncloud_platform.tools import app
from syncloud_platform.api import storage
from syncloud_platform.tools import chown, locale
from syncloud_platform.api import info
from syncloud_platform.api import app as platform_app
from mail.config import Config
from mail.config import UserConfig

SYSTEMD_POSTFIX = 'mail-postfix'


class MailInstaller:
    def __init__(self):
        self.log = logger.get_logger('mail_installer')
        self.config = Config()

    def install(self):

        locale.fix_locale()

        self.log.info(chown.chown(self.config.app_name(), self.config.install_path()))

        app_data_dir = app.get_app_data_root(self.config.app_name(), self.config.app_name())

        if not isdir(join(app_data_dir, 'config')):
            app.create_data_dir(app_data_dir, 'config', self.config.app_name())

        if not isdir(join(app_data_dir, 'log')):
            app.create_data_dir(app_data_dir, 'log', self.config.app_name())

        print("setup systemd")

        add_service(self.config.install_path(), SYSTEMD_POSTFIX)
        self.log.info(chown.chown(self.config.app_name(), self.config.install_path()))

        self.prepare_storage()

        platform_app.register_app('diaspora', self.config.port())

    def remove(self):

        platform_app.unregister_app('mail')
        remove_service(SYSTEMD_POSTFIX)
        
        if isdir(self.config.install_path()):
            shutil.rmtree(self.config.install_path())


    def prepare_storage(self):
        storage.init(self.config.app_name(), self.config.app_name())

    def update_domain(self):
        self.update_configuraiton()
        self.recompile_assets()

