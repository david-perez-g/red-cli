"""Authentication-related CLI commands."""

from __future__ import annotations

from typing import Optional

import click

from ..app import AppContainer
from ..presenters.spinner import Spinner
from ..presenters.symbols import SYMBOLS
from ...domain.exceptions import AuthError


@click.command()
@click.option("--server", required=True, help="Redmine server URL")
@click.option("--user", "auth_user", help="Username for authentication")
@click.option("--method", type=click.Choice(["token", "password"]), help="Authentication method")
@click.pass_obj
def login(app: AppContainer, server: str, auth_user: Optional[str], method: Optional[str]) -> None:
    """Authenticate against a Redmine server."""
    try:
        if not auth_user:
            auth_user = click.prompt(click.style("Username", fg="yellow"))

        if not method:
            use_token = click.confirm(
                click.style("Do you want to use an API token instead of password? (Defaults to no)", fg="yellow")
            )
            method = "token" if use_token else "password"

        password: Optional[str] = None
        token: Optional[str] = None

        if method == "token":
            token = click.prompt(click.style("Enter your API token", fg="yellow"), hide_input=True)
        else:
            password = click.prompt(click.style("Enter your password", fg="yellow"), hide_input=True)

        click.echo()
        with Spinner("Authenticating..."):
            session = app.auth.login(server, username=auth_user, password=password, token=token)

        success_prefix = SYMBOLS.get("success")
        click.echo(click.style(f"{success_prefix} Successfully logged in!", fg="green", bold=True))
        click.echo(click.style(f"User: {session.user_name} (ID: {session.user_id})", fg="cyan"))
        click.echo(click.style(f"Server: {session.server_url}", fg="cyan"))
    except AuthError as exc:
        err_stream = click.get_text_stream("stderr")
        auth_error_prefix = SYMBOLS.get("error", stream=err_stream)
        click.echo(click.style(f"{auth_error_prefix} Authentication failed: {exc}", fg="red", bold=True), err=True)
    except Exception as exc:  # noqa: BLE001 - show generic failure to user
        err_stream = click.get_text_stream("stderr")
        error_prefix = SYMBOLS.get("error", stream=err_stream)
        click.echo(click.style(f"{error_prefix} Login failed: {exc}", fg="red", bold=True), err=True)


@click.command()
@click.pass_obj
def logout(app: AppContainer) -> None:
    """Clear the stored authentication session."""
    try:
        app.auth.logout()
        goodbye_prefix = SYMBOLS.get("goodbye")
        click.echo(click.style(f"{goodbye_prefix} Successfully logged out", fg="green"))
    except Exception as exc:  # noqa: BLE001
        err_stream = click.get_text_stream("stderr")
        error_prefix = SYMBOLS.get("error", stream=err_stream)
        click.echo(click.style(f"{error_prefix} Logout failed: {exc}", fg="red", bold=True), err=True)


@click.command()
@click.pass_obj
def whoami(app: AppContainer) -> None:
    """Display the current authenticated user."""
    session = app.auth.current_session()
    if not session:
        unknown_prefix = SYMBOLS.get("unknown")
        click.echo(click.style(f"{unknown_prefix} Not logged in", fg="yellow"))
        click.echo(click.style("Use 'red login --server <URL>' to authenticate", fg="cyan"))
        return

    person_prefix = SYMBOLS.get("person")
    click.echo(click.style(f"{person_prefix} Current Session", fg="blue", bold=True))
    click.echo(click.style(f"User: {session.user_name}", fg="cyan"))
    click.echo(click.style(f"ID: {session.user_id}", fg="cyan"))
    click.echo(click.style(f"Server: {session.server_url}", fg="cyan"))


def register(group: click.Group) -> None:
    group.add_command(login)
    group.add_command(logout)
    group.add_command(whoami)
