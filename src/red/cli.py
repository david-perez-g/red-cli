# src/red/cli.py
"""Main CLI entry point for red."""

import click
from typing import Optional

from .auth import login, logout as auth_logout, get_current_session, AuthError, RedmineAuthenticator
from .api import get_api_client
from .utils import parse_ids, validate_server_url, Spinner
from .config import config


@click.group()
@click.version_option(version="0.1.0")
def main():
    """🚀 Redmine CLI - Efficient issue management from the command line.

    A powerful command-line interface for Redmine issue tracking.
    """
    pass


@main.command()
@click.option('--server', required=True, help='Redmine server URL')
@click.option('--user', 'auth_user', help='Username for authentication')
@click.option('--method', type=click.Choice(['token', 'password']), help='Authentication method')
def login(server, auth_user, method):
    """Login to Redmine server."""
    try:
        server_url = validate_server_url(server)

        click.echo(click.style("🔐 Redmine Login", fg='blue', bold=True))
        click.echo(click.style(f"Server: {server_url}", fg='cyan'))
        click.echo()

        # Determine authentication method
        if not auth_user:
            auth_user = click.prompt(click.style("Username", fg='yellow'))

        if not method:
            if click.confirm(click.style("Do you want to use an API token instead of password? (Defaults to no)", fg='yellow')):
                method = 'token'
            else:
                method = 'password'

        auth_token = None
        password = None

        if method == 'token':
            auth_token = click.prompt(click.style("Enter your API token", fg='yellow'), hide_input=True)
        else:
            password = click.prompt(click.style("Enter your password", fg='yellow'), hide_input=True)

        click.echo()

        # Show loading indicator
        with Spinner("Authenticating..."):
            # Call authentication directly to avoid function conflicts
            from .auth import RedmineAuthenticator
            authenticator = RedmineAuthenticator(server_url)

            if auth_token:
                session = authenticator.authenticate_with_token(auth_token)
            else:
                session = authenticator.authenticate_with_credentials(auth_user, password)

            # Save the session
            config.save_session(session)

        click.echo(click.style("✅ Successfully logged in!", fg='green', bold=True))
        click.echo(click.style(f"User: {session.user_name} (ID: {session.user_id})", fg='cyan'))
        click.echo(click.style(f"Server: {session.server_url}", fg='cyan'))

    except AuthError as e:
        click.echo(click.style(f"❌ Authentication failed: {e}", fg='red', bold=True), err=True)
    except Exception as e:
        click.echo(click.style(f"❌ Login failed: {e}", fg='red', bold=True), err=True)


@main.command()
def logout():
    """Logout and clear session data."""
    try:
        auth_logout()
        click.echo(click.style("👋 Successfully logged out", fg='green'))
    except Exception as e:
        click.echo(click.style(f"❌ Logout failed: {e}", fg='red', bold=True), err=True)


@main.command()
def whoami():
    """Show current login information."""
    try:
        session = get_current_session()
        if not session:
            click.echo(click.style("❓ Not logged in", fg='yellow'))
            click.echo(click.style("Use 'red login --server <URL>' to authenticate", fg='cyan'))
            return

        click.echo(click.style("👤 Current Session", fg='blue', bold=True))
        click.echo(click.style(f"User: {session.user_name}", fg='cyan'))
        click.echo(click.style(f"ID: {session.user_id}", fg='cyan'))
        click.echo(click.style(f"Server: {session.server_url}", fg='cyan'))

    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg='red', bold=True), err=True)


@main.command()
@click.argument('issue_ids', nargs=-1)
@click.option('--show-first', type=int, default=20, help='Show first N issues')
def issues(issue_ids, show_first):
    """
    List issues.

    ISSUE_IDS: Issue IDs to fetch (e.g., 1..10, 1,3,5..8)
    """
    try:
        api = get_api_client()

        click.echo(click.style("🔍 Fetching issues...", fg='blue'))

        if issue_ids:
            # Fetch specific issues
            ids = list(parse_ids(issue_ids))
            issues_data = []

            with click.progressbar(ids[:show_first], label=click.style("Loading issues", fg='green')) as bar:
                for issue_id in bar:
                    try:
                        issue = api.get_issue(issue_id)
                        issues_data.append(issue)
                    except Exception as e:
                        click.echo(click.style(f"⚠️  Error fetching issue {issue_id}: {e}", fg='yellow'), err=True)
        else:
            # Fetch issues assigned to current user
            with click.progressbar(length=1, label=click.style("Loading your issues", fg='green')) as bar:
                issues_data = api.get_issues()
                bar.update(1)

        click.echo()
        click.echo(click.style(f"📋 Found {len(issues_data)} issues", fg='blue', bold=True))
        click.echo()

        # Display issues with fancy formatting
        for i, issue in enumerate(issues_data[:show_first]):
            status = issue['status']['name']
            tracker = issue['tracker']['name']

            # Color code status
            if status.lower() in ['new', 'open']:
                status_color = 'green'
            elif status.lower() in ['in progress', 'assigned']:
                status_color = 'yellow'
            elif status.lower() in ['resolved', 'closed']:
                status_color = 'red'
            else:
                status_color = 'white'

            click.echo(click.style(f"#{issue['id']}", fg='cyan', bold=True), nl=False)
            click.echo(click.style(f" [{tracker}]", fg='magenta'), nl=False)
            click.echo(click.style(f" {issue['subject']}", fg='white', bold=True))
            click.echo(click.style(f"  Status: ", fg='white'), nl=False)
            click.echo(click.style(f"{status}", fg=status_color, bold=True))
            click.echo()

        if len(issues_data) > show_first:
            click.echo(click.style(f"... and {len(issues_data) - show_first} more issues", fg='yellow'))

    except AuthError as e:
        click.echo(click.style(f"🔐 Authentication required: {e}", fg='red', bold=True), err=True)
        click.echo(click.style("Use 'red login --server <URL>' to authenticate", fg='cyan'))
    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg='red', bold=True), err=True)


if __name__ == "__main__":
    # make it runnable as `python -m red.cli` for local dev
    main(prog_name="red")
