from ConfigParser import ConfigParser
from os.path import isfile, join

default_config_path = '/opt/app/mail/config'
default_config_file = join(default_config_path, 'mail.cfg')

default_user_config_path = '/opt/data/mail'
default_user_config_file = join(default_user_config_path, 'user_mail.cfg')


class Config:

    def __init__(self, filename=default_config_file):
        self.parser = ConfigParser()
        self.parser.read(filename)
        self.filename = filename

    def app_name(self):
        return self.parser.get('mail', 'app_name')

    def install_path(self):
        return self.parser.get('mail', 'install_path')

    def data_dir(self):
        return self.parser.get('mail', 'data_dir')

    def bin_dir(self):
        return self.parser.get('mail', 'bin_dir')

    def root_path(self):
        return self.parser.get('mail', 'root_path')

    def port(self):
        return self.parser.getint('mail', 'port')

    def psql(self):
        return self.parser.get('mail', 'psql')

    def db_socket(self):
        return self.parser.get('mail', 'db_socket')

    def postfix_main_config_file(self):
        return self.parser.get('mail', 'postfix_main_config_file')


class UserConfig:

    def __init__(self, filename=default_user_config_file):
        self.parser = ConfigParser()
        self.parser.read(filename)
        self.filename = filename
        if not isfile(self.filename):
            self.parser.add_section('mail')
            self.__save()
        else:
            self.parser.read(self.filename)

        if not self.parser.has_section('mail'):
            self.parser.add_section('mail')

    def is_activated(self):
        self.parser.read(self.filename)
        if self.parser.has_option('mail', 'activated'):
            return self.parser.getboolean('mail', 'activated')
        return False

    def set_activated(self, activated):
        self.parser.read(self.filename)
        self.parser.set('mail', 'activated', activated)
        self.__save()

    def __save(self):
        with open(self.filename, 'wb') as f:
            self.parser.write(f)
