# -*- coding: utf-8 -*-

import difflib
import json
import click
from utils import PostgresConnector


def jsonify(command, message):
    """

    :param command:
    :param message:
    :return:
    """
    res = dict()
    res.update({
        'command': command,
        'params': message
    })
    return json.dumps(res, indent=4, sort_keys=True)


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


def diff_to_screen(views_states):
    for state, values in views_states.iteritems():
        click.secho('+ ' + state.title() + ' modules', fg='yellow')
        for view in values:
            if state == 'updated':
                diff = difflib.unified_diff(
                    view['original'].split('\n'),
                    view['modified'].split('\n')
                )
            else:
                diff = view['arch'].split('\\n')
            click.secho('+++ Module ' + view['xml_id'], fg='yellow')
            for line in diff:
                if line.startswith('+'):
                    click.secho(line, fg='green')
                elif line.startswith('-'):
                    click.secho(line, fg='red')
                else:
                    click.secho(line)
