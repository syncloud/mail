from ConfigParser import ConfigParser
from os.path import isfile, join

default_config_path = '/opt/app/mail/config'
default_config_file = join(default_config_path, 'mail.cfg')

default_user_config_path = '/opt/data/mail/config'
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



class UserConfig:

    def __init__(self, filename=default_user_config_file):
        self.parser = ConfigParser()
        self.parser.read(filename)
        self.filename = filename
        if not isfile(self.filename):
            self.parser.add_section('mail')
            self.set_activated(False)
            self.__save()
        else:
            self.parser.read(self.filename)

        if not self.parser.has_section('mail'):
            self.parser.add_section('mail')

    def __save(self):
        with open(self.filename, 'wb') as f:
            self.parser.write(f)
