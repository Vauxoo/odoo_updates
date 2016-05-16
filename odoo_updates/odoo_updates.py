# -*- coding: utf-8 -*-

import difflib
import click
from utils import PostgresConnector, copy_list_dicts


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
    for uindex, view_modified in enumerate(modified_views):
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
            else:
                diff = view.get('arch' if 'arch' in view else 'name').split('\\n')
            click.secho('+++ {title} {xml_id}'.format(title=title, xml_id=view['xml_id']),
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
