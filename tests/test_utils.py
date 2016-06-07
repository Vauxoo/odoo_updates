# -*- coding: utf-8 -*-
from unittest2 import TestCase
from odoo_updates import utils
import simplejson as json
import psycopg2
import os


class TestUtils(TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ['AWS_DEFAULT_REGION'] = "us-east-1"
        cls.connector = utils.PostgresConnector({'dbname': 'tests'})

    def test_01_jsonify(self):
        states = {'added': 1, 'deleted': 2, 'updated': 3}
        json_res = utils.jsonify(states, 'test', 'test')
        res = json.loads(json_res)
        self.assertIsInstance(res, dict)
        self.assertEquals(res['customer_id'], 'test')
        self.assertEquals(res['command'], 'test')
        self.assertEquals(res['parameters'], states)

    def test_02_copy_list_dicts(self):
        dict_list = [{'key1': 'val1', 'key2': 'val2'},
                     {'key': 1, 'val': 2}]
        res = utils.copy_list_dicts(dict_list)
        self.assertIsInstance(res, list)
        self.assertEquals(res, dict_list)

    def test_03_postgres_connector_exception(self):
        with self.assertRaises(psycopg2.OperationalError):
            utils.PostgresConnector({'dbname': 'wrong_name'})

    def test_04_execute_select(self):
        res = self.connector.execute_select('SELECT tablename FROM pg_catalog.pg_tables')
        tables = res.fetchall()
        self.assertIsInstance(tables, list)
        self.assertTrue(tables)

    def test_04_execute_select_exception(self):
        with self.assertRaises(psycopg2.ProgrammingError):
            self.connector.execute_select('wrong query')

    def test_05_execute_change(self):
        res = self.connector.execute_change('SELECT tablename FROM pg_catalog.pg_tables')
        self.assertTrue(res)

    def test_06_check_config(self):
        res = self.connector.check_config()
        self.assertTrue(res)

    def test_07_disconnect(self):
        self.connector.disconnect()
        with self.assertRaises(psycopg2.InterfaceError):
            self.connector.execute_select('SELECT tablename FROM pg_catalog.pg_tables')

    def test_08_check_config_exception(self):
        res = self.connector.check_config()
        self.assertFalse(res)
