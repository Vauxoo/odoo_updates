# -*- coding: utf-8 -*-

import boto3
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
import json

logger = logging.getLogger('deployv')  # pylint: disable=C0103


def jsonify(states, command, customer_id, instance):
    """

    :param command:
    :param message:
    :return:
    """
    message = {
        'instance': instance,
        'customer_id': customer_id,
        'generated_at': datetime.now().strftime("%Y%m%d %H%M%S"),
        'command': command,
        'result': states
    }

    return json.dumps(message, indent=4, sort_keys=True)


def copy_list_dicts(lines):
    """
    Convert a lazy cursor from psycopg2 to a list of dictionaries to reduce the access times
    when a recurrent access is performed

    :param lines: The psycopg2 cursor with the query result
    :return: A list of dictionaries
    """
    res = list()
    for line in lines:
        dict_t = dict()
        for keys in line.keys():
            dict_t.update({keys: line[keys]})
        res.append(dict_t.copy())
    return res


class PostgresConnector(object):
    """ A simple helper to perform a postgres connection, execute simple sql sentences
    """
    __conn = None
    __cursor = None
    __allowed_keys = ['host', 'port', 'dbname', 'user', 'password']
    __str_conn = ''

    def __init__(self, config=None):
        if config is None:
            config = {}
        for key, value in config.items():
            if value is not None and key in self.__allowed_keys:
                self.__str_conn = '%s %s=%s' % (self.__str_conn, key, value)
            elif key == 'dbname' and value is None:
                self.__str_conn = '%s %s=%s' % (
                    self.__str_conn, 'dbname', 'postgres')
        logger.debug('Connection string: %s', self.__str_conn)
        try:
            logger.debug('Stabilishing connection with db server')
            self.__conn = psycopg2.connect(self.__str_conn)
            if config.get('isolation_level', False):
                self.__conn.set_isolation_level(0)
            self.__cursor = self.__conn.cursor(
                cursor_factory=psycopg2.extras.DictCursor)
        except Exception as e:
            # TODO: log this then raise
            logger.debug(
                'Connection to database not established: %s', e.message)
            # Proper cleanup
            self.disconnect()
            raise

    def _execute(self, sql_str, *args):
        try:
            logger.debug('SQL: %s', sql_str)
            self.__cursor.execute(sql_str, *args)
        except Exception:
            self.__conn.rollback()
            raise
        else:
            self.__conn.commit()

    def execute_select(self, sql_str, *args):
        """ This method basically wraps *execute* cursor method from psycopg2,
         see http://initd.org/psycopg/docs/usage.html#passing-parameters-to-sql-queries

        :param sql_str: Sql to be executed
        :param args: Args, all will be passed to
            `cursor.execute <http://initd.org/psycopg/docs/cursor.html#cursor.execute>`_
        :return: A dict if a select was performed, True if update/insert was success
        """
        self._execute(sql_str, args)
        return self.__cursor

    def execute_change(self, sql_str, *args):
        self._execute(sql_str, args)
        return True

    def check_config(self):
        """ Check if can connect to PostgreSQL server with the provided configuration

        :return: True if success, False otherwise
        """
        try:
            logger.debug('')
            res = self._execute("select version();")
            logger.debug('Postgres returned: %s', res)
        except Exception as error:  # pylint: disable=W0703
            logger.error('PostgreSQL connection test failed %s',
                         error.message.strip())
            return False
        return True

    def disconnect(self):
        if self.__cursor:
            logger.debug('disconnect: closing cursor')
            self.__cursor.close()
        if self.__conn:
            logger.debug('disconnect: closing connection')
            self.__conn.close()

    def __del__(self):
        self.disconnect()

    def __exit__(self, type, value, traceback):  # pylint: disable=W0622
        self.disconnect()

    def __enter__(self):
        return self


def send_message(message, queue_name):
    resource = boto3.resource('sqs')
    queue = resource.get_queue_by_name(QueueName=queue_name)
    response = queue.send_message(MessageBody=message)
    return response
