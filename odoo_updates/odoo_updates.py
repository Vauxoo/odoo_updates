# -*- coding: utf-8 -*-

import difflib
import click
import os
from .utils import PostgresConnector, copy_list_dicts
import json
import shlex
import spur


def menu_tree(menu_id, database):
    sql = """
    WITH RECURSIVE search_menu(id, parent_id, name, depth, hierarchypath) AS (
    SELECT menu.id, menu.parent_id, menu.name, 1, ppmenu.name || '->' || menu.name as hierarchypath
    FROM ir_ui_menu AS menu
    JOIN ir_ui_menu AS ppmenu
    ON menu.parent_id = ppmenu.id
    UNION ALL
        SELECT menu.id, menu.parent_id, menu.name, pmenu.depth + 1,
            hierarchypath || '->' || menu.name
        FROM ir_ui_menu as menu
        JOIN search_menu as pmenu
        ON menu.parent_id = pmenu.id
    )
    SELECT * FROM search_menu WHERE id = %s ORDER BY depth DESC LIMIT 1;
    """
    with PostgresConnector({'dbname': database}) as conn:
        tree = conn.execute_select(sql, (menu_id,))
        res = copy_list_dicts(tree)
    return res[0]


def get_menus(database):
    sql = """SELECT ir_model_data.module || '.' || ir_model_data.name AS xml_id,
                    res_id, ir_ui_menu.name
                FROM ir_model_data
                JOIN ir_ui_menu ON res_id = ir_ui_menu.id
                WHERE ir_model_data.model = 'ir.ui.menu';  """
    with PostgresConnector({'dbname': database}) as conn:
        menus = conn.execute_select(sql)
        menus = copy_list_dicts(menus)
    res = dict()
    for menu in menus:
        res.update({
            menu['xml_id']: menu
        })
    return res


def get_views(database):
    """
    Select the views contents and xml_id from the specified database.
    The xml_id is formed by joining the module name and the id_model_data name so it
    can be used for the comparison and for the report at the end.
    :param database: database name to query on
    :return: List of dicts with the xml_id and view content
    """
    sql = """SELECT ir_model_data.module || '.' || ir_model_data.name xml_id, arch
        FROM ir_model_data
        JOIN ir_ui_view ON res_id = ir_ui_view.id
        WHERE ir_model_data.model = 'ir.ui.view'
        ORDER BY xml_id;"""
    with PostgresConnector({'dbname': database}) as conn:
        cursor = conn.execute_select(sql)
        res = copy_list_dicts(cursor)
    return res


def get_branches():
    json_filename = '/tmp/branches.json'
    branches_file = os.path.expanduser('~/backupws/branches.py')
    instance_path = os.path.expanduser('~/instance')
    command = 'python {branches} -s -p {instance} -f {name}'.format(name=json_filename,
                                                                    branches=branches_file,
                                                                    instance=instance_path)
    shell = spur.LocalShell()
    shell.run(shlex.split(command))
    with open(json_filename, "r") as dest:
        branches = json.load(dest)
    return branches


def get_translations(database):
    """
    Select the translation values, ids, translated fields name and modules that contain those
    fields from the specified database. The translation value is needed to compare the different
    translations from different database, the id is to make sure we are comparing the same
    translated field of both databases and the translated field name and modules are just to
    display more information.
    :param database: database name to query on
    :return: List of dicts with the information obtained from the database
    """
    with PostgresConnector({'dbname': database}) as conn:
        cursor = conn.execute_select("""SELECT value,id,name,module FROM ir_translation""")
        res = copy_list_dicts(cursor)
    return res


def get_fields(database):
    """
    Selection fields model , name , field_description, ttype,
    to create a list of fields and their values
    :param database: database name to query on
    :return: List of dicts with the information get from database.
     List of dicts With the information get from the database as follows
     {'model': model ('ir.model'),
      'name': field ('field_id'),
      'description': description ('Fields')
      'type': data type ('integer')
      ,}
     model: Column having the model name
     name: A column that has the name of the model fields
     description: column that has the description of the model fields
     type: column that has the data type of model fields
    """
    sql = """
          select model, name, field_description as description,
          ttype as type from ir_model_fields;
          """
    with PostgresConnector({'dbname': database}) as conn:
        cursor = conn.execute_select(sql)
        res = copy_list_dicts(cursor)
    return res


def compare_views(original_views, modified_views):
    """
    Compare all the views from views_prod with the views_updates and returns a proper report
    :param original_views: This would be the views from production database (a copy of course)
    :param modified_views: This is are the views from the copy with
        all changes applied (-u all, -u app_module).
    :return: a dict with the added and updated views. In the case of updated will return the diff
        between the org_database and dst_database
    """
    pchecked = list()
    res = {
        'updated': list(),
        'added': list()
    }
    for view_modified in modified_views:
        for index, view_original in enumerate(original_views):
            if view_original['xml_id'] == view_modified['xml_id'] and index not in pchecked:
                if view_original['arch'] != view_modified['arch']:
                    res.get('updated').append({
                        'xml_id': view_original['xml_id'],
                        'original': view_original['arch'],
                        'modified': view_modified['arch']
                    })
                pchecked.append(index)
                break
        else:
            res.get('added').append(view_modified)
    return res


def compare_translations(original_translations, modified_translations):
    """
    Compare all the translated fields from two databases and returns a proper report
    :param original_translations: The translations contained in the production
        database (copy of course).
    :param modified_translations: The translations contained in the updates database with all the
        changes that will be applied in the production database.
    :return: A dict with the added, updated and removed translations between the production
        database and the updates database.
    """
    checked = list()
    res = {
        'updated': list(),
        'added': list(),
        'deleted': list()
    }
    for modified_translation in modified_translations:
        for original_translation in original_translations:
            if original_translation['id'] == modified_translation['id']:
                checked.append(original_translation)
                if original_translation['value'] != modified_translation['value']:
                    res.get('updated').append({
                        'name': original_translation['name'],
                        'module': original_translation['module'],
                        'original': original_translation['value'],
                        'modified': modified_translation['value']
                    })
                break
        else:
            res.get('added').append({
                'name': modified_translation['name'],
                'module': modified_translation['module'],
                'value': modified_translation['value']
            })
    for original_translation in original_translations:
        if original_translation not in checked:
            res.get('deleted').append({
                'name': original_translation['name'],
                'module': original_translation['module'],
                'value': original_translation['value'],
            })
    return res


def compare_fields(original_fields, modified_fields):
    """
    compares the fields of tables in a database and returns the direfencias
    :param original_fields: This would be the fields from the point of
     view of production database
    :modified_fields: This are the changes made in the fields of
    the database, the argument after the -u (-u all, -u app_module).
    :return: a dict with the added, updated and deleted fields.
    In the case of updated will return the diff between the org_database
    and dst_database
    """
    res = {
        'updated': list(), 'added': list(), 'deleted': list(),
    }
    records_updates = list()
    for modified in modified_fields:
        for original in original_fields:
            if modified['model'] == original['model']\
               and modified['name'] == original['name']:
                if modified['type'] != original['type']\
                   or modified['description']\
                   != original['description']:
                    records_updates.append(original)
                    records_updates.append(modified)
                    updated = {'model': original['model'],
                               'name': original['name'],
                               'original': {'type': original['type'],
                                            'description':
                                            original['description']},
                               'modified': {'type': modified['type'],
                                            'description':
                                            modified['description']},
                               }
                    res.get('updated').append(updated)
    for original in original_fields:
        if original not in modified_fields and original not in records_updates:
            res.get('deleted').append(original)

    for modified in modified_fields:
        if modified not in original_fields and modified not in records_updates:
            res.get('added').append(modified)
    return res


def get_fields_diff(original_database, modified_database):
    original_fields = get_fields(original_database)
    modified_fields = get_fields(modified_database)
    res = compare_fields(original_fields, modified_fields)
    return res


def get_views_diff(original_database, modified_database):
    """
    Receive the databases names, get the views and return a dict with the original and
        corresponding modified view in case of a modification or the new view in case of an
        addition
    :param original_database: The name of the unmodified database
    :param modified_database: The name of the updated database
    :return:
    """
    original_views = get_views(original_database)
    modified_views = get_views(modified_database)
    res = compare_views(original_views, modified_views)
    return res


def get_translations_diff(original_database, modified_database):
    """
    Receive the databases names, get the translations and return a dict with the added,
    modified and removed translations.
    :param original_database: The name of the unmodified database.
    :param modified_database: The name of the updated database.
    :return: dict with the added, modified and removed translations.
    """
    original_translations = get_translations(original_database)
    modified_translations = get_translations(modified_database)
    res = compare_translations(original_translations, modified_translations)
    return res


def get_menus_diff(original_database, modified_database):
    original_menus = get_menus(original_database)
    modified_menus = get_menus(modified_database)
    res = {
        'updated': list(),
        'added': list(),
        'deleted': list()
    }

    for uxml_id, urecord in modified_menus.iteritems():
        if uxml_id in original_menus \
                and original_menus[uxml_id]['name'] != urecord['name']:
            menu = menu_tree(urecord['res_id'], modified_database)
            res['updated'].append({
                'xml_id': uxml_id,
                'original': original_menus[uxml_id]['name'],
                'modified': urecord['name'],
                'hierarchypath': menu['hierarchypath']
            })
        if uxml_id not in original_menus:
            menu = menu_tree(urecord['res_id'], modified_database)
            res['added'].append({
                'xml_id': uxml_id,
                'name': urecord['name'],
                'hierarchypath': menu['hierarchypath']
            })
    for pxml_id, precord in original_menus.iteritems():
        if pxml_id not in modified_menus:
            menu = menu_tree(precord['res_id'], original_database)
            res['deleted'].append({
                'xml_id': precord['xml_id'],
                'name': precord['name'],
                'hierarchypath': menu['hierarchypath']
            })

    return res


def diff_to_screen(views_states, title):
    for state, values in views_states.iteritems():
        click.secho('+ {state} {title}'.format(state=state.title(), title=title), fg='yellow')
        for view in values:
            if state == 'updated':
                diff = difflib.unified_diff(
                    view['original'].split('\n'),
                    view['modified'].split('\n')
                )
            elif title == 'Translations':
                diff = view.get('value').split('\\n')
            else:
                diff = view.get('arch' if 'arch' in view else 'name').split('\\n')
            xml_id = view.get('xml_id' if 'xml_id' in view else 'name')
            click.secho('+++ {title} {xml_id}'.format(title=title, xml_id=xml_id),
                        fg='yellow')
            if 'hierarchypath' in view:
                click.secho('++++ Check it in: {hi}'.format(hi=view.get('hierarchypath')),
                            fg='yellow')
            for line in diff:
                if line.startswith('+'):
                    click.secho(line, fg='green')
                elif line.startswith('-'):
                    click.secho(line, fg='red')
                else:
                    click.secho(line)


def fields_to_screen(fields_states, title):
    show_model_field = dict()
    for state, values in fields_states.iteritems():
        click.secho('+ {state} {title}'.
                    format(state=state.title(), title=title), fg='yellow')
        for field in values:
            if state == 'updated':
                diff = {'type': list(difflib.unified_diff(
                        field['original'].get('type', '').split('\n'),
                        field['modified'].get('type', '').split('\n'))),
                        'description': list(difflib.unified_diff(
                            field['original']
                            .get('description', '').split('\n'),
                            field['modified']
                            .get('description', '').split('\n'))), }
            else:
                diff = {'type': field['type'].split('\n'),
                        'description':
                            field['description'].split('\n'), }
            if field.get('model') not in show_model_field:
                show_model_field[field.get('model')] = []
                click.secho('+++ {title} {model}'.
                            format(title='model',
                                   model=field.get('model')),
                            fg='yellow')
            if field.get('name') not in\
               show_model_field[field.get('model')]:
                show_model_field[field.get('model')].append(field.get('name'))
                click.secho('+++ {title} {name}'.
                            format(title='field name:',
                                   name=field.get('name')),
                            fg='yellow')

            for colm in diff:
                if diff[colm]:
                    click.secho('++++field {column}'.format(column=colm),
                                fg='yellow')
                for line in diff[colm]:
                    if line.startswith('+'):
                        click.secho(line, fg='green')
                    elif line.startswith('-'):
                        click.secho(line, fg='red')
                    else:
                        click.secho(line)


def branches_to_screen(branches):
    click.echo('Repositories:\n')
    for branch in branches:
        click.secho('{path}'.format(path=branch['path']), fg='yellow')
        click.echo('{repo} {branch}'.format(branch=branch['branch'], repo=branch['name']))
        click.echo('commit: {commit}'.format(commit=branch['commit']))
        for remote, url in branch['repo_url'].iteritems():
            click.echo('{remote}: {url}'.format(url=url, remote=remote))
        click.echo('\n')
