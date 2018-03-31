from os.path import dirname, join, abspath, isdir
from os import listdir
import sys

app_path = abspath(join(dirname(__file__), '..'))

lib_path = join(app_path, 'lib')
libs = [join(lib_path, item) for item in listdir(lib_path) if isdir(join(lib_path, item))]
map(lambda l: sys.path.insert(0, l), libs)

from os.path import isdir, join
import shutil

from subprocess import check_output
from syncloud_app import logger

from syncloud_platform.application import api
from syncloud_platform.gaplib import fs, linux, gen
from syncloudlib.application import paths, urls, storage, ports

from config import Config
from config import UserConfig
import postgres
from tzlocal import get_localzone


SYSTEMD_POSTFIX = 'mail.postfix'
SYSTEMD_DOVECOT = 'mail.dovecot'
SYSTEMD_NGINX = 'mail.nginx'
SYSTEMD_PHP_FPM = 'mail.php-fpm'
SYSTEMD_POSTGRES = 'mail.postgresql'

USER_NAME = 'mail'
APP_NAME = 'mail'
PSQL_PORT = 5432
DB_NAME = 'mail'
DB_USER = 'mail'
DB_PASS = 'mail'


class MailInstaller:
    def __init__(self):
        self.log = logger.get_logger('mail_installer')
        self.app_dir = paths.get_app_dir(APP_NAME)
        self.app_data_dir = paths.get_data_dir(APP_NAME)
        self.app_url = urls.get_app_url(APP_NAME)
        self.app_domain_name = urls.get_app_domain_name(APP_NAME)
        self.platform_data_dir = paths.get_data_dir('platform')
        self.device_domain_name = urls.get_device_domain_name()
        
        self.database_path = '{0}/database'.format(self.app_data_dir)
        self.config_path = join(self.app_data_dir, 'config')
        self.config = Config(self.config_path)
        self.user_config = UserConfig(self.app_data_dir)


    def regenerate_configs(self):
    
        variables = {
            'app_dir': self.app_dir,
            'app_data_dir': self.app_data_dir,
            'db_psql_path': self.database_path,
            'db_psql_port': PSQL_PORT,
            'db_name': DB_NAME,
            'db_user': DB_USER,
            'db_password': DB_PASS,
            'platform_data_dir': self.platform_data_dir,
            'device_domain_name': self.device_domain_name,
            'app_domain_name': self.app_domain_name,
            'timezone': get_localzone()
        }

        templates_path = join(self.app_dir, 'config.templates')
        
        gen.generate_files(templates_path, self.config_path, variables)
        
        self.log.info(fs.chownpath(self.config_path, USER_NAME, recursive=True))

    def install(self):

        linux.fix_locale()

        linux.useradd('maildrop')
        linux.useradd('dovecot')
        linux.useradd(USER_NAME)
        
        self.regenerate_configs()
        
        self.log.info(fs.chownpath(self.app_dir, USER_NAME, recursive=True))

        fs.chownpath(self.app_data_dir, USER_NAME)

        data_dirs = [
            join(self.app_data_dir, 'config'),
            join(self.app_data_dir, 'log'),
            join(self.app_data_dir, 'spool'),
            join(self.app_data_dir, 'dovecot'),
            join(self.app_data_dir, 'dovecot', 'private'),
            join(self.app_data_dir, 'data')
        ]

        for data_dir in data_dirs:
            fs.makepath(data_dir)
            fs.chownpath(data_dir, USER_NAME)

        box_data_dir = join(self.app_data_dir, 'box')
        fs.makepath(box_data_dir)
        fs.chownpath(box_data_dir, 'dovecot')

        dovecot_lda_error_log = join(self.app_data_dir, 'log', 'dovecot-lda.error.log')
        fs.touchfile(dovecot_lda_error_log)
        fs.chownpath(dovecot_lda_error_log, 'dovecot')

        dovecot_lda_info_log = join(self.app_data_dir, 'log', 'dovecot-lda.info.log')
        fs.touchfile(dovecot_lda_info_log)
        fs.chownpath(dovecot_lda_info_log, 'dovecot')

        self.log.info("setup configs")

        if not self.user_config.is_activated():
            self.database_init(self.database_path, USER_NAME)

    def start(self):
        app = api.get_app_setup(APP_NAME)
        self.log.info("setup systemd")
        app.add_service(SYSTEMD_POSTGRES)
        app.add_service(SYSTEMD_POSTFIX)
        app.add_service(SYSTEMD_DOVECOT)
        app.add_service(SYSTEMD_PHP_FPM)
        app.add_service(SYSTEMD_NGINX)

    def configure(self):
    
        if not self.user_config.is_activated():
            self.initialize(self.config, self.user_config, DB_NAME, DB_USER, DB_PASS)

        self.prepare_storage()
        try:
            ports.add_port(25, 'TCP')
            ports.add_port(110, 'TCP')
            ports.add_port(143, 'TCP')
            ports.add_port(587, 'TCP')
        except Exception, e:
            self.log.warn("failed to add ports: {0}".format(e.message))
   
    def database_init(self, database_path, user_name):

        self.log.info("initializing database")
        psql_initdb = join(self.app_dir, 'postgresql/bin/initdb')
        self.log.info(check_output(['sudo', '-H', '-u', user_name, psql_initdb, database_path]))
        postgresql_conf_to = join(database_path, 'postgresql.conf')
        postgresql_conf_from = join(self.app_data_dir, 'config', 'postgresql', 'postgresql.conf')
        shutil.copy(postgresql_conf_from, postgresql_conf_to)

    def remove(self):
        app = api.get_app_setup(APP_NAME)
        app.remove_service(SYSTEMD_NGINX)
        app.remove_service(SYSTEMD_PHP_FPM)
        app.remove_service(SYSTEMD_DOVECOT)
        app.remove_service(SYSTEMD_POSTFIX)
        app.remove_service(SYSTEMD_POSTGRES)

        if isdir(self.app_dir):
            shutil.rmtree(self.app_dir)

    def initialize(self, config, user_config, db_name, db_user, db_pass):
        self.log.info("initialization")
        postgres.execute_sql(config, "ALTER USER {0} WITH PASSWORD '{0}';".format(db_user, db_pass), database="postgres")
        postgres.execute_sql(config, "create database {0};".format(db_name), database="postgres")
        postgres.execute_file(config, config.db_init_file(), database=db_name)
        user_config.set_activated(True)

    def prepare_storage(self):
        app_storage_dir = storage.init_storage(APP_NAME, USER_NAME)
        tmp_storage_path = join(app_storage_dir, 'tmp')
        fs.makepath(tmp_storage_path)
        fs.chownpath(tmp_storage_path, USER_NAME)

    def update_domain(self):

        self.regenerate_configs()
        self.app.restart_service(SYSTEMD_DOVECOT)
        