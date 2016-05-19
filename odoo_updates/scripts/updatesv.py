# -*- coding: utf-8 -*-

import click
from .. import odoo_updates
from .. import utils


@click.group()
@click.option('--original', '-o', required=True)
@click.option('--updated', '-u', required=True)
@click.option('--screen', '-s', is_flag=True, default=False)
@click.option('--queue', '-q', envvar='AWS_BRANCH_QUEUE', default=False)
@click.option('--customer', '-c', envvar='CUSTOMER', required=True)
@click.pass_context
def cli(ctx, original, updated, screen, queue, customer):
    ctx.obj.update({'original': original})
    ctx.obj['updated'] = updated
    ctx.obj['screen'] = screen
    ctx.obj['queue'] = queue
    ctx.obj['customer'] = customer


@cli.command()
@click.pass_context
def views(ctx):
    views_states = odoo_updates.get_views_diff(ctx.obj['original'], ctx.obj['updated'])
    if ctx.obj['screen']:
        odoo_updates.diff_to_screen(views_states, 'views')
    else:
        message = utils.jsonify(views_states, 'views', ctx.obj['customer'])
        utils.send_message(message, ctx.obj['queue'])


@cli.command()
@click.pass_context
def menus(ctx):
    menus_states = odoo_updates.get_menus_diff(ctx.obj['original'], ctx.obj['updated'])
    if ctx.obj['screen']:
        odoo_updates.diff_to_screen(menus_states, 'menus')
    else:
        message = utils.jsonify(menus_states, 'menus', ctx.obj['customer'])
        utils.send_message(message, ctx.obj['queue'])


@cli.command()
@click.pass_context
def branches(ctx):
    branches_info = odoo_updates.get_branches()
    if ctx.obj['screen']:
        odoo_updates.branches_to_screen(branches_info)
    else:
        message = utils.jsonify(branches_info, 'branches', ctx.obj['customer'])
        utils.send_message(message, ctx.obj['queue'])


@cli.command()
@click.pass_context
def translations(ctx):
    translation_states = odoo_updates.get_translations_diff(ctx.obj['original'],
                                                            ctx.obj['updated'])
    if ctx.obj['screen']:
        odoo_updates.diff_to_screen(translation_states, 'Translations')
    else:
        message = utils.jsonify(translation_states, 'translations', ctx.obj['customer'])
        utils.send_message(message, ctx.obj['queue'])


@cli.command()
@click.pass_context
def fields(ctx):
    fields_states = odoo_updates.get_fields_diff(ctx.obj['original'],
                                                 ctx.obj['updated'])
    if ctx.obj['screen']:
        odoo_updates.diff_to_screen(fields_states, 'Fields')
    else:
        message = utils.jsonify(fields_states, 'fields', ctx.obj['customer'])
        utils.send_message(message, ctx.obj['queue'])


@cli.command()
@click.pass_context
def getall(ctx):
    states = dict()
    views_states = odoo_updates.get_views_diff(ctx.obj['original'], ctx.obj['updated'])
    menus_states = odoo_updates.get_menus_diff(ctx.obj['original'], ctx.obj['updated'])
    translation_states = odoo_updates.get_translations_diff(ctx.obj['original'],
                                                            ctx.obj['updated'])
    branches_info = odoo_updates.get_branches()
    fields_states = odoo_updates.get_fields_diff(ctx.obj['original'], ctx.obj['updated'])
    # One for each command views, models, menus, translations, etc
    states.update({'views': views_states})
    states.update({'menus': menus_states})
    states.update({'branches': branches_info})
    states.update({'translations': translation_states})
    states.update({'fields': fields_states})
    message = utils.jsonify(states, 'getall', ctx.obj['customer'])
    utils.send_message(message, ctx.obj['queue'])

cli(obj={})
