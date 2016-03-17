import os
from os import environ
from os.path import isdir, join, isfile
import shutil
from subprocess import check_output

import pwd
from syncloud_app import logger

from syncloud_platform.systemd.systemctl import remove_service, add_service, restart_service
from syncloud_platform.tools import app
from syncloud_platform.api import storage
from syncloud_platform.tools import chown, locale
from syncloud_platform.api import info
from syncloud_platform.api import app as platform_app
from syncloud_platform.api import port
from mail.config import Config
from mail.config import UserConfig
from mail import postgres
import grp
from dateutil.tz import gettz


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
        self.app_domain_name = '{0}.{1}'.format(self.config.app_name(), self.device_domain_name)

    def install(self):

        locale.fix_locale()

        self.log.info(chown.chown(self.config.app_name(), self.config.install_path()))

        app_data_dir = app.get_app_data_root(self.config.app_name(), self.config.app_name())

        useradd('maildrop')
        useradd('dovecot')

        if not isdir(join(app_data_dir, 'config')):
            app.create_data_dir(app_data_dir, 'config', self.config.app_name())

        if not isdir(join(app_data_dir, 'log')):
            app.create_data_dir(app_data_dir, 'log', self.config.app_name())

        if not isdir(join(app_data_dir, 'spool')):
            app.create_data_dir(app_data_dir, 'spool', self.config.app_name())

        if not isdir(join(app_data_dir, 'dovecot')):
            app.create_data_dir(app_data_dir, 'dovecot', self.config.app_name())

        if not isdir(join(app_data_dir, 'dovecot', 'private')):
            app.create_data_dir(join(app_data_dir, 'dovecot'), 'private', self.config.app_name())

        if not isdir(join(app_data_dir, 'box')):
            app.create_data_dir(app_data_dir, 'box', 'dovecot')

        if not isdir(join(app_data_dir, 'data')):
            app.create_data_dir(app_data_dir, 'data', self.config.app_name())

        if not isdir(join(app_data_dir, 'postgresql')):
            app.create_data_dir(app_data_dir, 'postgresql', self.config.app_name())

        dovecot_lda_error_log = join(app_data_dir, 'log', 'dovecot-lda.error.log')
        touch(dovecot_lda_error_log, 'dovecot')

        dovecot_lda_info_log = join(app_data_dir, 'log', 'dovecot-lda.info.log')
        touch(dovecot_lda_info_log, 'dovecot')

        print("setup systemd")
        self.generate_postfix_config()
        self.generate_roundcube_config()
        self.generate_dovecot_config()
        self.generate_php_config()

        add_service(self.config.install_path(), SYSTEMD_POSTGRES)
        add_service(self.config.install_path(), SYSTEMD_POSTFIX)
        add_service(self.config.install_path(), SYSTEMD_DOVECOT)
        add_service(self.config.install_path(), SYSTEMD_PHP_FPM)
        add_service(self.config.install_path(), SYSTEMD_NGINX)

        user_config = UserConfig()
        if not user_config.is_activated():
            self.initialize(user_config)
        self.log.info(chown.chown(self.config.app_name(), self.config.install_path()))

        self.prepare_storage()

        platform_app.register_app('mail', self.config.port())
        port.add_port(25)
        port.add_port(110)
        port.add_port(143)
        port.add_port(587)

    def remove(self):

        platform_app.unregister_app('mail')
        remove_service(SYSTEMD_NGINX)
        remove_service(SYSTEMD_PHP_FPM)
        remove_service(SYSTEMD_DOVECOT)
        remove_service(SYSTEMD_POSTFIX)
        remove_service(SYSTEMD_POSTGRES)

        if isdir(self.config.install_path()):
            shutil.rmtree(self.config.install_path())

    def initialize(self, user_config):
        print("initialization")
        postgres.execute_sql("ALTER USER mail WITH PASSWORD 'mail';", database="postgres")
        postgres.execute_sql("create database mail;", database="postgres")
        postgres.execute_file(self.config.db_init_file(), database="mail")
        user_config.set_activated(True)

    def prepare_storage(self):
        app_storage_dir = storage.init(self.config.app_name(), self.config.app_name())
        app.create_data_dir(app_storage_dir, 'tmp', self.config.app_name())

    def update_domain(self):
        self.generate_postfix_config()
        self.generate_roundcube_config()
        self.generate_dovecot_config()
        restart_service(SYSTEMD_POSTFIX)

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
            config_file.write('myhostname = {0}\n'.format(self.app_domain_name))
            config_file.write('virtual_mailbox_domains = {0}\n'.format(self.device_domain_name))

    def generate_dovecot_config(self):

        template_file_name = '{0}.template'.format(self.config.dovecot_config_file())
        shutil.copyfile(template_file_name, self.config.dovecot_config_file())
        with open(self.config.dovecot_config_file(), "a") as config_file:
            config_file.write('\n')
            config_file.write('postmaster_address = postmaster@{0}\n'.format(self.device_domain_name))

    def generate_php_config(self):
        
        template_file_name = '{0}.template'.format(self.config.php_ini())
        shutil.copyfile(template_file_name, self.config.php_ini())
        with open(self.config.php_ini(), "a") as config_file:
            config_file.write('\n')
            config_file.write('date.timezone = '{0}'\n'.format(gettz()))


def touch(file, user):
    with open(file, 'a'):
            os.utime(file, None)
    user_uid = pwd.getpwnam(user).pw_uid
    user_gid = grp.getgrnam(user).gr_gid
    os.chown(file, user_uid, user_gid)


def useradd(user):
    try:
        pwd.getpwnam(user)
        return 'user {0} exists'.format(user)
    except KeyError:
        return check_output('/usr/sbin/useradd -r -s /bin/false {0}'.format(user), shell=True)
