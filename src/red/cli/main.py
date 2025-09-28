"""CLI entrypoint wiring using Click."""

from __future__ import annotations

import click

from .app import build_app_container
from .commands import auth as auth_commands
from .commands import issues as issues_commands
from .commands import overview as overview_command


@click.group()
@click.version_option(version="0.1.0")
@click.pass_context
def main(ctx: click.Context) -> None:
    """🚀 Redmine CLI - Efficient issue management from the command line."""
    if ctx.obj is None:
        ctx.obj = build_app_container()


def _register_commands(group: click.Group) -> None:
    auth_commands.register(group)
    issues_commands.register(group)
    overview_command.register(group)


_register_commands(main)


if __name__ == "__main__":
    main(prog_name="red")
