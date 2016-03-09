import os
from os import environ
from os.path import isdir, join, isfile
import shutil
from subprocess import check_output

import pwd
from syncloud_app import logger

from syncloud_platform.systemd.systemctl import remove_service, add_service, reload_service
from syncloud_platform.tools import app
from syncloud_platform.api import storage
from syncloud_platform.tools import chown, locale
from syncloud_platform.api import info
from syncloud_platform.api import app as platform_app
from mail.config import Config
from mail.config import UserConfig
from mail import postgres

SYSTEMD_POSTFIX = 'mail-postfix'
SYSTEMD_DOVECOT = 'mail-dovecot'
SYSTEMD_NGINX = 'mail-nginx'
SYSTEMD_PHP_FPM = 'mail-php-fpm'
SYSTEMD_POSTGRES = 'mail-postgres'


class MailInstaller:
    def __init__(self):
        self.log = logger.get_logger('mail_installer')
        self.config = Config()
        self.device_domain_name = info.domain()

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

        if not isdir(join(app_data_dir, 'box')):
            app.create_data_dir(app_data_dir, 'box', self.config.app_name())

        if not isdir(join(app_data_dir, 'data')):
            app.create_data_dir(app_data_dir, 'data', self.config.app_name())

        if not isdir(join(app_data_dir, 'postgresql')):
            app.create_data_dir(app_data_dir, 'postgresql', self.config.app_name())

        useradd('maildrop')

        print("setup systemd")
        self.generate_postfix_config()
        self.generate_roundcube_config()

        add_service(self.config.install_path(), SYSTEMD_POSTGRES)
        add_service(self.config.install_path(), SYSTEMD_POSTFIX)
        add_service(self.config.install_path(), SYSTEMD_DOVECOT)
        add_service(self.config.install_path(), SYSTEMD_PHP_FPM)
        add_service(self.config.install_path(), SYSTEMD_NGINX)

        user_config = UserConfig()
        if not user_config.is_activated():
            self.initialize()
        self.log.info(chown.chown(self.config.app_name(), self.config.install_path()))

        self.prepare_storage()

        platform_app.register_app('mail', self.config.port())

    def remove(self):

        platform_app.unregister_app('mail')
        remove_service(SYSTEMD_NGINX)
        remove_service(SYSTEMD_PHP_FPM)
        remove_service(SYSTEMD_DOVECOT)
        remove_service(SYSTEMD_POSTFIX)
        remove_service(SYSTEMD_POSTGRES)

        if isdir(self.config.install_path()):
            shutil.rmtree(self.config.install_path())

    def initialize(self):
        print("initialization")
        postgres.execute("ALTER USER mail WITH PASSWORD 'mail';", database="postgres")
        postgres.execute("create database mail;", database="postgres")
        user_config = UserConfig()
        user_config.set_activated(True)

    def prepare_storage(self):
        app_storage_dir = storage.init(self.config.app_name(), self.config.app_name())
        app.create_data_dir(app_storage_dir, 'tmp', self.config.app_name())

    def update_domain(self):
        self.generate_postfix_config()
        self.generate_roundcube_config()
        reload_service(SYSTEMD_POSTFIX)

    def generate_roundcube_config(self):
        shutil.copyfile(self.config.roundcube_config_file_template(), self.config.roundcube_config_file())
        #with open(self.config.roundcube_config_file(), "a") as config_file:
            #config_file.write("$config['default_host'] = '{0}';\n".format(self.app_domain))

    def generate_postfix_config(self):
        
        template_file_name = '{0}.template'.format(self.config.postfix_main_config_file())
        shutil.copyfile(template_file_name, self.config.postfix_main_config_file())
        with open(self.config.postfix_main_config_file(), "a") as config_file:
            config_file.write('\n')
            config_file.write('mydomain = {0}\n'.format(self.device_domain_name))
            config_file.write('myhostname = {0}\n'.format(self.device_domain_name))


def useradd(user):
    try:
        pwd.getpwnam(user)
        return 'user {0} exists'.format(user)
    except KeyError:
        return check_output('/usr/sbin/useradd -r -s /bin/false {0}'.format(user), shell=True)
