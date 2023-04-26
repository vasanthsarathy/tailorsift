import os
import click
import json
import random


# Shared click options
shared_options = [
    click.option('--verbose/--no-verbose', '-v', default=False, help="If set, console output is verbose"),
]

def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options

@click.group()
@click.option('--verbose/--no-verbose', '-v', default=False, help="If set, console output is verbose")
@click.pass_context
def cli(ctx, **kwargs):
    ctx.ensure_object(dict)
    ctx.obj = kwargs
    click.clear()
    click.secho('TailorSIFT', bold=True, fg='blue')
    click.secho(f"Stitching together acronyms that sing", fg='yellow')
    print(f'-----------------')


@click.command()
@add_options(shared_options)
@click.pass_context
def sing(ctx, **kwargs):
    from tailorsift import websvc
    ctx.obj.update(kwargs)
    websvc.main()

cli.add_command(sing)

def main():
    cli(obj={})

if __name__ == "__main__":
    main()

