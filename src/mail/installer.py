from os.path import isdir, join
import shutil

from subprocess import check_output
from syncloud_app import logger

from syncloud_platform.gaplib import fs, linux, gen

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
PSQL_PORT = 5432
DB_NAME = 'mail'
DB_USER = 'mail'
DB_PASS = 'mail'


class MailInstaller:
    def __init__(self):
        self.log = logger.get_logger('mail_installer')
        self.app = api.get_app_setup(APP_NAME)
        self.platform_app = api.get_app_setup('platform')
        self.device_domain_name = self.app.device_domain_name()
        self.app_domain_name = self.app.app_domain_name()
        self.app_dir = self.app.get_install_dir()

    def install(self):

        linux.fix_locale()

        linux.useradd('maildrop')
        linux.useradd('dovecot')
        linux.useradd(USER_NAME)

        app_data_dir = self.app.get_data_dir()
        database_path = '{0}/database'.format(app_data_dir)

        variables = {
            'app_dir': self.app_dir,
            'app_data_dir': app_data_dir,
            'db_psql_path': database_path,
            'db_psql_port': PSQL_PORT,
            'db_name': DB_NAME,
            'db_user': DB_USER,
            'db_password': DB_PASS,
            'platform_data_dir': self.platform_app.get_data_dir()
        }

        templates_path = join(self.app_dir, 'config.templates')
        config_path = join(self.app_dir, 'config')

        gen.generate_files(templates_path, config_path, variables)

        self.log.info(fs.chownpath(self.app_dir, USER_NAME, recursive=True))

        fs.chownpath(app_data_dir, USER_NAME)

        data_dirs = [
            join(app_data_dir, 'config'),
            join(app_data_dir, 'log'),
            join(app_data_dir, 'spool'),
            join(app_data_dir, 'dovecot'),
            join(app_data_dir, 'dovecot', 'private'),
            join(app_data_dir, 'data'),
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

        config = Config()

        self.log.info("setup configs")
        self.generate_postfix_config(config)
        self.generate_roundcube_config(config)
        self.generate_dovecot_config(config)
        self.generate_php_config(config)

        user_config = UserConfig()

        is_first_time = not user_config.is_activated()

        if is_first_time:
            self.database_init(self.app_dir, database_path, USER_NAME)

        self.log.info("setup systemd")
        self.app.add_service(SYSTEMD_POSTGRES)
        self.app.add_service(SYSTEMD_POSTFIX)
        self.app.add_service(SYSTEMD_DOVECOT)
        self.app.add_service(SYSTEMD_PHP_FPM)
        self.app.add_service(SYSTEMD_NGINX)

        if is_first_time:
            self.initialize(config,user_config, DB_NAME, DB_USER, DB_PASS)

        self.prepare_storage()

        self.app.register_web(config.port())
        self.app.add_port(25, 'TCP')
        self.app.add_port(110, 'TCP')
        self.app.add_port(143, 'TCP')
        self.app.add_port(587, 'TCP')

    def database_init(self, app_install_dir, database_path, user_name):

        self.log.info("initializing database")
        psql_initdb = join(app_install_dir, 'postgresql/bin/initdb')
        self.log.info(check_output(['sudo', '-H', '-u', user_name, psql_initdb, database_path]))
        postgresql_conf_to = join(database_path, 'postgresql.conf')
        postgresql_conf_from = join(app_install_dir, 'config', 'postgresql', 'postgresql.conf')
        shutil.copy(postgresql_conf_from, postgresql_conf_to)

    def remove(self):

        self.app.unregister_web()
        self.app.remove_service(SYSTEMD_NGINX)
        self.app.remove_service(SYSTEMD_PHP_FPM)
        self.app.remove_service(SYSTEMD_DOVECOT)
        self.app.remove_service(SYSTEMD_POSTFIX)
        self.app.remove_service(SYSTEMD_POSTGRES)

        if isdir(self.app_dir):
            shutil.rmtree(self.app_dir)

    def initialize(self, config, user_config, db_name, db_user, db_pass):
        self.log.info("initialization")
        postgres.execute_sql("ALTER USER {0} WITH PASSWORD '{0}';".format(db_user, db_pass), database="postgres")
        postgres.execute_sql("create database {0};".format(db_name), database="postgres")
        postgres.execute_file(config.db_init_file(), database=db_name)
        user_config.set_activated(True)

    def prepare_storage(self):
        app_storage_dir = self.app.init_storage(USER_NAME)
        tmp_storage_path = join(app_storage_dir, 'tmp')
        fs.makepath(tmp_storage_path)
        fs.chownpath(tmp_storage_path, USER_NAME)

    def update_domain(self):
        config = Config()
        self.generate_postfix_config(config)
        self.generate_roundcube_config(config)
        self.generate_dovecot_config(config)
        self.app.restart_service(SYSTEMD_POSTFIX)

    def generate_roundcube_config(self, config):
        shutil.copyfile(config.roundcube_config_file_template(), config.roundcube_config_file())
        with open(config.roundcube_config_file(), "a") as config_file:
            config_file.write('\n')
            config_file.write("$config['mail_domain'] = '{0}';\n".format(self.device_domain_name))
            config_file.write("$config['imap_conn_options']['ssl']['peer_name'] = '{0}';\n".format(self.device_domain_name))

    def generate_postfix_config(self, config):
        
        template_file_name = '{0}.template'.format(config.postfix_main_config_file())
        shutil.copyfile(template_file_name, config.postfix_main_config_file())
        with open(config.postfix_main_config_file(), "a") as config_file:
            config_file.write('\n')
            config_file.write('mydomain = {0}\n'.format(self.device_domain_name))
            config_file.write('myhostname = {0}\n'.format(self.app_domain_name))
            config_file.write('virtual_mailbox_domains = {0}\n'.format(self.device_domain_name))

    def generate_dovecot_config(self, config):

        template_file_name = '{0}.template'.format(config.dovecot_config_file())
        shutil.copyfile(template_file_name, config.dovecot_config_file())
        with open(config.dovecot_config_file(), "a") as config_file:
            config_file.write('\n')
            config_file.write('postmaster_address = postmaster@{0}\n'.format(self.device_domain_name))

    def generate_php_config(self, config):
        
        template_file_name = '{0}.template'.format(config.php_ini())
        shutil.copyfile(template_file_name, config.php_ini())
        with open(config.php_ini(), "a") as config_file:
            config_file.write('\n')
            config_file.write("date.timezone = '{0}'\n".format(get_localzone()))