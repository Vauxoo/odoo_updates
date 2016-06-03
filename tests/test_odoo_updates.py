from unittest2 import TestCase
from odoo_updates import odoo_updates
import shlex
import spur


class TestOdooUpdates(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.shell = spur.LocalShell()
        cls.shell.run(shlex.split('psql test_original -f original_test_db.sql'))
        cls.shell.run(shlex.split('psql test_updated -f updated_test_db.sql'))

    def test_01_menu_tree(self):
        res = odoo_updates.menu_tree(1, 'test_original')
        self.assertIsInstance(res, dict)
        self.assertEquals(res['id'], 1)
        self.assertEquals(res['parent_id'], 2)

    def test_02_get_menus(self):
        res = odoo_updates.get_menus('test_original')
        self.assertIsInstance(res, dict)
        for xmlid, record in res.iteritems():
            self.assertIsInstance(record, dict)
            self.assertEquals(xmlid, record['xml_id'])

    def test_03_get_menus_diff(self):
        res = odoo_updates.get_menus_diff('test_original', 'test_updated')
        self.assertEquals(len(res['added']), 1)
        self.assertIsInstance(res['added'], list)
        self.assertIsInstance(res['added'][0], dict)
        self.assertEquals(res['added'][0]['name'], 'test_menu_4')
        self.assertEquals(len(res['deleted']), 1)
        self.assertIsInstance(res['deleted'], list)
        self.assertIsInstance(res['deleted'][0], dict)
        self.assertEquals(res['deleted'][0]['name'], 'test_menu_3')
        self.assertEquals(len(res['updated']), 1)
        self.assertIsInstance(res['updated'], list)
        self.assertIsInstance(res['updated'][0], dict)
        self.assertEquals(res['updated'][0]['original'], 'test_menu_1')
        self.assertNotEqual(res['updated'][0]['original'], res['updated'][0]['modified'])
        self.assertNotIn(res['added'][0], res['deleted'])
        self.assertNotIn(res['deleted'][0], res['added'])

    def test_04_get_translations(self):
        res = odoo_updates.get_translations('test_original')
        self.assertEquals(len(res), 2)
        self.assertIsInstance(res, list)
        for record in res:
            self.assertIsInstance(record, dict)

    def test_05_compare_translations(self):
        original = odoo_updates.get_translations('test_original')
        updated = odoo_updates.get_translations('test_updated')
        res = odoo_updates.compare_translations(original, updated)
        self.assertEquals(len(res['added']), 1)
        self.assertIsInstance(res['added'], list)
        self.assertIsInstance(res['added'][0], dict)
        self.assertEquals(res['added'][0]['name'], 'name')
        self.assertEquals(res['added'][0]['value'], 'added translation')
        self.assertEquals(len(res['deleted']), 1)
        self.assertIsInstance(res['deleted'], list)
        self.assertIsInstance(res['deleted'][0], dict)
        self.assertEquals(res['deleted'][0]['name'], 'surname')
        self.assertEquals(res['deleted'][0]['value'], 'translation number two')
        self.assertEquals(len(res['updated']), 1)
        self.assertIsInstance(res['updated'], list)
        self.assertIsInstance(res['updated'][0], dict)
        self.assertEquals(res['updated'][0]['name'], 'name')
        self.assertEquals(res['updated'][0]['original'], 'translation number one')
        self.assertNotEqual(res['updated'][0]['original'], res['updated'][0]['modified'])
        self.assertNotIn(res['added'][0], res['deleted'])
        self.assertNotIn(res['deleted'][0], res['added'])

    def test_06_get_translations_diff(self):
        res = odoo_updates.get_translations_diff('test_original', 'test_updated')
        self.assertEquals(len(res['added']), 1)
        self.assertIsInstance(res['added'], list)
        self.assertIsInstance(res['added'][0], dict)
        self.assertEquals(res['added'][0]['name'], 'name')
        self.assertEquals(res['added'][0]['value'], 'added translation')
        self.assertEquals(len(res['deleted']), 1)
        self.assertIsInstance(res['deleted'], list)
        self.assertIsInstance(res['deleted'][0], dict)
        self.assertEquals(res['deleted'][0]['name'], 'surname')
        self.assertEquals(res['deleted'][0]['value'], 'translation number two')
        self.assertEquals(len(res['updated']), 1)
        self.assertIsInstance(res['updated'], list)
        self.assertIsInstance(res['updated'][0], dict)
        self.assertEquals(res['updated'][0]['name'], 'name')
        self.assertEquals(res['updated'][0]['original'], 'translation number one')
        self.assertNotEqual(res['updated'][0]['original'], res['updated'][0]['modified'])
        self.assertNotIn(res['added'][0], res['deleted'])
        self.assertNotIn(res['deleted'][0], res['added'])

    def test_07_get_views(self):
        res = odoo_updates.get_views('test_original')
        self.assertEquals(len(res), 2)
        self.assertIsInstance(res, list)
        for record in res:
            self.assertIsInstance(record, dict)

    def test_08_compare_views(self):
        original = odoo_updates.get_views('test_original')
        updated = odoo_updates.get_views('test_updated')
        res = odoo_updates.compare_views(original, updated)
        self.assertEquals(len(res['added']), 1)
        self.assertIsInstance(res['added'], list)
        self.assertIsInstance(res['added'][0], dict)
        self.assertEquals(res['added'][0]['xml_id'], 'test_module.test_model_7')
        self.assertEquals(len(res['updated']), 1)
        self.assertIsInstance(res['updated'], list)
        self.assertIsInstance(res['updated'][0], dict)
        self.assertEquals(res['updated'][0]['xml_id'], 'test_module.test_model_5')
        self.assertNotEqual(res['updated'][0]['original'], res['updated'][0]['modified'])

    def test_09_get_views_diff(self):
        res = odoo_updates.get_views_diff('test_original', 'test_updated')
        self.assertEquals(len(res['added']), 1)
        self.assertIsInstance(res['added'], list)
        self.assertIsInstance(res['added'][0], dict)
        self.assertEquals(res['added'][0]['xml_id'], 'test_module.test_model_7')
        self.assertEquals(len(res['updated']), 1)
        self.assertIsInstance(res['updated'], list)
        self.assertIsInstance(res['updated'][0], dict)
        self.assertEquals(res['updated'][0]['xml_id'], 'test_module.test_model_5')
        self.assertNotEqual(res['updated'][0]['original'], res['updated'][0]['modified'])

    def test_10_get_branches(self):
        res = odoo_updates.get_branches()
        self.assertIsInstance(res, list)
        self.assertEquals(len(res), 1)
        self.assertIsInstance(res[0], dict)
        self.assertEquals(res[0]['name'], 'backupws')

    def test_11_diff_to_screen(self):
        views = odoo_updates.get_views_diff('test_original', 'test_updated')
        translations = odoo_updates.get_translations_diff('test_original', 'test_updated')
        menus = odoo_updates.get_menus_diff('test_original', 'test_updated')
        odoo_updates.diff_to_screen(views, 'test_views')
        odoo_updates.diff_to_screen(translations, 'Translations')
        odoo_updates.diff_to_screen(menus, 'test_menus')
        # TODO how to test this functions?

    def test_12_branches_to_screen(self):
        branches = odoo_updates.get_branches()
        odoo_updates.branches_to_screen(branches)
        # TODO how to test this function?

    def test_99_cleanup(self):
        self.shell.run(shlex.split('dropdb test_original'))
        self.shell.run(shlex.split('dropdb test_updated'))
