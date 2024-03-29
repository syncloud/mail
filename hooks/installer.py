import logging
import re
import shutil
from os.path import join
from subprocess import check_output

from syncloudlib import fs, linux, gen, logger
from syncloudlib.application import paths, urls, storage, service
from syncloudlib.application.config import set_dkim_key
from tzlocal import get_localzone

import postgres
from config import Config
from config import UserConfig

SYSTEMD_DOVECOT = 'mail.dovecot'

USER_NAME = 'mail'
APP_NAME = 'mail'
PSQL_PORT = 5432
DB_NAME = 'mail'
DB_USER = 'mail'
DB_PASS = 'mail'


class Installer:
    def __init__(self):
        if not logger.factory_instance:
            logger.init(logging.DEBUG, True)
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
        self.opendkim_dir = join(self.app_data_dir, 'opendkim')
        self.opendkim_keys_dir = join(self.opendkim_dir, 'keys')
        self.opendkim_keys_domain_dir = join(self.opendkim_keys_dir, self.device_domain_name)
        self.log_dir = join(self.app_data_dir, 'log')

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

        templates_path = join(self.app_dir, 'config')
        
        gen.generate_files(templates_path, self.config_path, variables)
        
        self.log.info(fs.chownpath(self.config_path, USER_NAME, recursive=True))

    def init_config(self):

        linux.useradd('maildrop')
        linux.useradd('dovecot')
        linux.useradd(USER_NAME)
        fs.makepath(join(self.app_data_dir, 'nginx'))
        
        self.regenerate_configs()
        
        data_dirs = [
            join(self.app_data_dir, 'config'),
            self.log_dir,
            join(self.app_data_dir, 'spool'),
            join(self.app_data_dir, 'dovecot'),
            join(self.app_data_dir, 'dovecot', 'private'),
            join(self.app_data_dir, 'data'),
            self.opendkim_dir,
            self.opendkim_keys_dir,
            self.opendkim_keys_domain_dir
        ]

        for data_dir in data_dirs:
            fs.makepath(data_dir)

        dkim_key = self.generate_dkim_key()
        set_dkim_key(dkim_key)

        fs.chownpath(self.app_data_dir, USER_NAME, recursive=True)

        box_data_dir = join(self.app_data_dir, 'box')
        fs.makepath(box_data_dir)
        self.log.info(check_output('chown -R dovecot.dovecot {0}'.format(box_data_dir), shell=True))
      
        self.log.info("setup configs")

    def generate_dkim_key(self):
        check_output('{0}/opendkim/bin/opendkim-genkey -s mail -d {1}'.format(self.app_dir, self.device_domain_name),
                     cwd=self.opendkim_keys_domain_dir, shell=True)
        mail_txt_file = join(self.opendkim_keys_domain_dir, 'mail.txt')
        mail_txt = open(mail_txt_file, 'r').read().strip()
        key = re.match(r'.*p=(.*?)".*', mail_txt, re.DOTALL | re.MULTILINE).group(1)
        return key

    def install(self):
        self.init_config()
        self.database_init(self.database_path, USER_NAME)

    def post_refresh(self):
        self.init_config()
        check_output(f'rm -rf {self.log_dir}/*.log', shell=True)
    
    def configure(self):
    
        if not self.user_config.is_activated():
            self.initialize(self.config, self.user_config, DB_NAME, DB_USER, DB_PASS)

        self.prepare_storage()
           
    def database_init(self, database_path, user_name):

        self.log.info("initializing database")
        psql_initdb = join(self.app_dir, 'postgresql/bin/initdb.sh')
        self.log.info(check_output(['sudo', '-H', '-u', user_name, psql_initdb, database_path]))
        postgresql_conf_to = join(database_path, 'postgresql.conf')
        postgresql_conf_from = join(self.app_data_dir, 'config', 'postgresql', 'postgresql.conf')
        shutil.copy(postgresql_conf_from, postgresql_conf_to)

    def initialize(self, config, user_config, db_name, db_user, db_pass):
        self.log.info("initialization")
        postgres.execute_sql(config, "ALTER USER {0} WITH PASSWORD '{0}';".format(db_user, db_pass),
                             database="postgres")
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
        service.restart(SYSTEMD_DOVECOT)
        
    def certificate_change(self):
        service.restart(SYSTEMD_DOVECOT)

    def storage_change(self):
        pass
