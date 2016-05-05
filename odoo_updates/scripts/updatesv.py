import click
import odoo_updates


@click.group()
@click.option('--original', '-o', required=True)
@click.option('--updated', '-u', required=True)
@click.option('--screen', '-s', is_flag=True, default=False)
@click.pass_context
def cli(ctx, original, updated, screen):
    ctx.obj.update({'original': original})
    ctx.obj['updated'] = updated
    ctx.obj['screen'] = screen


@cli.command()
@click.pass_context
def views(ctx):
    views_states = odoo_updates.get_views_diff(ctx.obj['original'], ctx.obj['updated'])
    if ctx.obj['screen']:
        odoo_updates.diff_to_screen(views_states)
    else:
        message = odoo_updates.jsonify('views', views_states)


@cli.command()
@click.pass_context
def getall(ctx):
    states = dict()
    views_states = odoo_updates.get_views_diff('apex80_production', 'apex80_updates_2')
    states.update({'views': views_states})
    message = odoo_updates.jsonify('getall', views_states)


cli(obj={})
