import click
from os import getenv
from .. import odoo_updates
from ..utils import send_message


@click.group()
@click.option('--original', '-o', required=True)
@click.option('--updated', '-u', required=True)
@click.option('--screen', '-s', is_flag=True, default=False)
@click.option('--queue', '-q', default=False)
@click.pass_context
def cli(ctx, original, updated, screen, queue):
    ctx.obj.update({'original': original})
    ctx.obj['updated'] = updated
    ctx.obj['screen'] = screen
    ctx.obj['queue'] = queue if queue else getenv('AWS_BRANCH_QUEUE')


@cli.command()
@click.pass_context
def views(ctx):
    views_states = odoo_updates.get_views_diff(ctx.obj['original'], ctx.obj['updated'])
    if ctx.obj['screen']:
        odoo_updates.diff_to_screen(views_states, 'views')
    else:
        message = odoo_updates.jsonify('views', views_states)
        send_message(message, ctx.obj['queue'])


@cli.command()
@click.pass_context
def menus(ctx):
    menus_states = odoo_updates.get_menus_diff(ctx.obj['original'], ctx.obj['updated'])
    if ctx.obj['screen']:
        odoo_updates.diff_to_screen(menus_states, 'menus')
    else:
        message = odoo_updates.jsonify('menus', menus_states)
        send_message(message, ctx.obj['queue'])


@cli.command()
@click.pass_context
def getall(ctx):
    states = dict()
    views_states = odoo_updates.get_views_diff(ctx.obj['original'], ctx.obj['updated'])
    menus_states = odoo_updates.get_menus_diff(ctx.obj['original'], ctx.obj['updated'])
    # One for each command views, models, menus, translations, etc
    states.update({'views': views_states})
    states.update({'menus': menus_states})
    message = odoo_updates.jsonify('getall', views_states)
    send_message(message, ctx.obj['queue'])

cli(obj={})
