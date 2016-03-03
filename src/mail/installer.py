from os import environ
from os.path import isdir, join
import shutil
from subprocess import check_output

import pwd
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
SYSTEMD_DOVECOT = 'mail-dovecot'
SYSTEMD_NGINX = 'mail-nginx'
SYSTEMD_PHP_FPM = 'mail-php-fpm'
SYSTEMD_POSTGRES = 'mail-postgres'


class MailInstaller:
    def __init__(self):
        self.log = logger.get_logger('mail_installer')
        self.config = Config()
        self.user_config = UserConfig()

    def install(self):

        locale.fix_locale()

        self.log.info(chown.chown(self.config.app_name(), self.config.install_path()))

        app_data_dir = app.get_app_data_root(self.config.app_name(), self.config.app_name())

        if not isdir(join(app_data_dir, 'config')):
            app.create_data_dir(app_data_dir, 'config', self.config.app_name())

        if not isdir(join(app_data_dir, 'log')):
            app.create_data_dir(app_data_dir, 'log', self.config.app_name())

        if not isdir(join(app_data_dir, 'spool')):
            app.create_data_dir(app_data_dir, 'spool', self.config.app_name())

        if not isdir(join(app_data_dir, 'data')):
            app.create_data_dir(app_data_dir, 'data', self.config.app_name())

        useradd('maildrop')

        if not self.user_config.is_installed():
            self.initialize()

        print("setup systemd")

        add_service(self.config.install_path(), SYSTEMD_POSTGRES)
        add_service(self.config.install_path(), SYSTEMD_DOVECOT)
        add_service(self.config.install_path(), SYSTEMD_POSTFIX)
        add_service(self.config.install_path(), SYSTEMD_PHP_FPM)
        add_service(self.config.install_path(), SYSTEMD_NGINX)
        self.log.info(chown.chown(self.config.app_name(), self.config.install_path()))

        self.prepare_storage()

        platform_app.register_app('mail', self.config.port())

    def remove(self):

        platform_app.unregister_app('mail')
        remove_service(SYSTEMD_NGINX)
        remove_service(SYSTEMD_PHP_FPM)
        remove_service(SYSTEMD_POSTFIX)
        remove_service(SYSTEMD_DOVECOT)
        remove_service(SYSTEMD_POSTGRES)

        if isdir(self.config.install_path()):
            shutil.rmtree(self.config.install_path())

    def initialize(self):

            print("initialization")
            postgres.execute("ALTER USER mail WITH PASSWORD 'mail';", database="postgres")

    def prepare_storage(self):
        app_storage_dir = storage.init(self.config.app_name(), self.config.app_name())
        app.create_data_dir(app_storage_dir, 'tmp', self.config.app_name())


def useradd(user):
    try:
        pwd.getpwnam(user)
        return 'user {0} exists'.format(user)
    except KeyError:
        return check_output('/usr/sbin/useradd -r -s /bin/false {0}'.format(user), shell=True)
