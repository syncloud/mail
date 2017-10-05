from syncloud_app import logger
from subprocess import check_output

USER = "mail"
DATABASE = "mail"


def execute_sql(config, sql, database=DATABASE):
    log = logger.get_logger('mail_postgres')

    log.info("executing: {0}".format(sql))
    log.info(check_output('{0} -U {1} -h {2} -d {3} -c "{4}"'.format(config.psql(), USER, config.db_socket(), database, sql), shell=True))


def execute_file(config, file, database=DATABASE):
    log = logger.get_logger('mail_postgres')

    log.info("executing: {0}".format(file))
    log.info(check_output('{0} -U {1} -h {2} -d {3} -f "{4}"'.format(config.psql(), USER, config.db_socket(), database, file), shell=True))
