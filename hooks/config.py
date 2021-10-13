from configparser import ConfigParser
from os.path import isfile, join


class Config:

    def __init__(self, config_dir):
        filename = join(config_dir, 'mail.cfg')
        self.parser = ConfigParser()
        self.filename = filename

    def app_name(self):
        self.parser.read(self.filename)
        return self.parser.get('mail', 'app_name')

    def install_path(self):
        self.parser.read(self.filename)
        return self.parser.get('mail', 'install_path')

    def data_dir(self):
        self.parser.read(self.filename)
        return self.parser.get('mail', 'data_dir')

    def bin_dir(self):
        self.parser.read(self.filename)
        return self.parser.get('mail', 'bin_dir')

    def root_path(self):
        self.parser.read(self.filename)
        return self.parser.get('mail', 'root_path')

    def port(self):
        self.parser.read(self.filename)
        return self.parser.getint('mail', 'port')

    def psql(self):
        self.parser.read(self.filename)
        return self.parser.get('mail', 'psql')

    def db_socket(self):
        self.parser.read(self.filename)
        return self.parser.get('mail', 'db_socket')

    def postfix_main_config_file(self):
        self.parser.read(self.filename)
        return self.parser.get('mail', 'postfix_main_config_file')

    def roundcube_config_file_template(self):
        self.parser.read(self.filename)
        return self.parser.get('mail', 'roundcube_config_file_template')

    def roundcube_config_file(self):
        self.parser.read(self.filename)
        return self.parser.get('mail', 'roundcube_config_file')

    def dovecot_config_file(self):
        self.parser.read(self.filename)
        return self.parser.get('mail', 'dovecot_config_file')

    def db_init_file(self):
        self.parser.read(self.filename)
        return self.parser.get('mail', 'db_init_file')

    def php_ini(self):
        self.parser.read(self.filename)
        return self.parser.get('mail', 'php_ini')



class UserConfig:

    def __init__(self, config_dir):
        filename = join(config_dir, 'user_mail.cfg')
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
        with open(self.filename, 'w') as f:
            self.parser.write(f)

