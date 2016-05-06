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


def compare_views(views_prod, views_updates):
    """
    Compare all the views from views_prod with the views_updates and returns a proper report

    :param views_prod: This would be the views from production database (a copy of course)
    :param views_updates: This is are the views from the copy with
        all changes applied (-u all, -u app_module).
    :return: a dict with the added and updated views. In the case of updated will return the diff
        between the org_database and dst_database
    """
    uchecked = list()
    pchecked = list()
    res = {
        'updated': dict(),
        'added': dict()
    }
    for uindex, view_updates in enumerate(views_updates):
        for index, view_prod in enumerate(views_prod):
            if view_prod['xml_id'] == view_updates['xml_id'] and index not in pchecked:
                if view_prod['arch'] != view_updates['arch']:
                    diff = difflib.unified_diff(
                        view_prod['arch'].split('\n'),
                        view_updates['arch'].split('\n')
                    )
                    res.get('updated').update({view_updates['xml_id']: '\n'.join(diff)})
                pchecked.append(index)
                uchecked.append(uindex)
                break
        else:
            res.get('added').update({view_updates['xml_id']: view_updates['arch']})
    return res


def get_views_diff(org_database, dst_database):
    views_prod = get_views(org_database)
    views_updates = get_views(dst_database)
    res = compare_views(views_prod, views_updates)
    return res


def diff_to_screen(views_states):
    for state, values in views_states.iteritems():
        click.secho('+ ' + state.title() + ' modules', fg='yellow')
        for module, view in values.iteritems():
            click.secho('+++ Module ' + module, fg='yellow')
            for line in view.split('\n'):
                if line.startswith('+'):
                    click.secho(line, fg='green')
                elif line.startswith('-'):
                    click.secho(line, fg='red')
