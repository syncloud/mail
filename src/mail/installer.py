from os.path import isdir, join
import shutil

from syncloud_app import logger

from syncloud_platform.systemd.systemctl import remove_service, add_service, restart_service
from syncloud_platform.api import info
from syncloud_platform.api import port

from syncloud_platform.gaplib import fs, linux

from syncloud_platform.application import api

from mail.config import Config
from mail.config import UserConfig
from mail import postgres
from tzlocal import get_localzone


SYSTEMD_POSTFIX = 'mail-postfix'
SYSTEMD_DOVECOT = 'mail-dovecot'
SYSTEMD_NGINX = 'mail-nginx'
SYSTEMD_PHP_FPM = 'mail-php-fpm'
SYSTEMD_POSTGRES = 'mail-postgres'

USER_NAME = 'mail'
APP_NAME = 'mail'


class MailInstaller:
    def __init__(self):
        self.log = logger.get_logger('mail_installer')
        self.config = Config()
        self.device_domain_name = info.domain()
        self.app_domain_name = '{0}.{1}'.format(APP_NAME, self.device_domain_name)

    def install(self):

        linux.fix_locale()

        linux.useradd('maildrop')
        linux.useradd('dovecot')
        linux.useradd(USER_NAME)

        self.log.info(fs.chownpath(self.config.install_path(), USER_NAME, recursive=True))

        app_setup = api.get_app_setup(APP_NAME)
        app_data_dir = app_setup.get_data_dir()
        fs.chownpath(app_data_dir, USER_NAME)

        data_dirs = [
            join(app_data_dir, 'config'),
            join(app_data_dir, 'log'),
            join(app_data_dir, 'spool'),
            join(app_data_dir, 'dovecot'),
            join(app_data_dir, 'dovecot', 'private'),
            join(app_data_dir, 'data'),
            join(app_data_dir, 'postgresql'),
            join(app_data_dir, 'config')
        ]

        for data_dir in data_dirs:
            fs.makepath(data_dir)
            fs.chownpath(data_dir, USER_NAME)

        box_data_dir = join(app_data_dir, 'box')
        fs.makepath(box_data_dir)
        fs.chownpath(box_data_dir, 'dovecot')

        dovecot_lda_error_log = join(app_data_dir, 'log', 'dovecot-lda.error.log')
        fs.touchfile(dovecot_lda_error_log)
        fs.chownpath(dovecot_lda_error_log, 'dovecot')

        dovecot_lda_info_log = join(app_data_dir, 'log', 'dovecot-lda.info.log')
        fs.touchfile(dovecot_lda_info_log)
        fs.chownpath(dovecot_lda_info_log, 'dovecot')

        print("setup configs")
        self.generate_postfix_config()
        self.generate_roundcube_config()
        self.generate_dovecot_config()
        self.generate_php_config()

        print("setup systemd")
        add_service(self.config.install_path(), SYSTEMD_POSTGRES)
        add_service(self.config.install_path(), SYSTEMD_POSTFIX)
        add_service(self.config.install_path(), SYSTEMD_DOVECOT)
        add_service(self.config.install_path(), SYSTEMD_PHP_FPM)
        add_service(self.config.install_path(), SYSTEMD_NGINX)

        user_config = UserConfig()
        if not user_config.is_activated():
            self.initialize(user_config)
        self.log.info(fs.chownpath(self.config.install_path(), USER_NAME, recursive=True))

        app_storage_dir = app_setup.init_storage(USER_NAME)
        self.prepare_storage(app_storage_dir)

        app_setup.register_web(self.config.port())
        port.add_port(25, 'TCP')
        port.add_port(110, 'TCP')
        port.add_port(143, 'TCP')
        port.add_port(587, 'TCP')

    def remove(self):

        app_setup = api.get_app_setup(APP_NAME)
        app_setup.unregister_web()
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

    def prepare_storage(self, app_storage_dir):
        tmp_storage_path = join(app_storage_dir, 'tmp')
        fs.makepath(tmp_storage_path)
        fs.chownpath(tmp_storage_path, USER_NAME)

    def update_domain(self):
        self.generate_postfix_config()
        self.generate_roundcube_config()
        self.generate_dovecot_config()
        restart_service(SYSTEMD_POSTFIX)

    def generate_roundcube_config(self):
        shutil.copyfile(self.config.roundcube_config_file_template(), self.config.roundcube_config_file())
        with open(self.config.roundcube_config_file(), "a") as config_file:
            config_file.write('\n')
            config_file.write("$config['mail_domain'] = '{0}';\n".format(self.device_domain_name))
            config_file.write("$config['imap_conn_options']['ssl']['peer_name'] = '{0}';\n".format(self.device_domain_name))

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
            config_file.write("date.timezone = '{0}'\n".format(get_localzone()))