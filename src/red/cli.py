# src/red/cli.py
"""Main CLI entry point for red."""

import click
from typing import Optional, Dict, Any

from .auth import login, logout as auth_logout, get_current_session, AuthError, RedmineAuthenticator
from .api import get_api_client
from .utils import parse_ids, validate_server_url, Spinner
from .config import config


def format_date_range_description(date_range):
    """Format date range for display."""
    if not date_range or not (date_range[0] or date_range[1]):
        return None
    
    if date_range[0] and date_range[1]:
        return f"{date_range[0]} to {date_range[1]}"
    elif date_range[0]:
        return f"from {date_range[0]}"
    elif date_range[1]:
        return f"to {date_range[1]}"
    return None


def display_stats_section(title, stats_dict, emoji="📋"):
    """Display a statistics section with counts."""
    if stats_dict:
        click.echo(click.style(f"{emoji} {title}", fg='green', bold=True))
        for key, count in stats_dict.items():
            click.echo(click.style(f"  {key}: {count}", fg='white'))
        click.echo()


def display_issues_list(issues, max_issues=5, truncate_subject=True):
    """Display a list of issues."""
    if issues:
        click.echo(click.style("🔥 Recent Issues", fg='green', bold=True))
        for issue in issues[:max_issues]:
            status_color = 'green' if issue.status.lower() in ['new', 'open'] else 'yellow'
            subject = issue.subject[:50] + "..." if truncate_subject and len(issue.subject) > 50 else issue.subject
            click.echo(click.style(f"#{issue.id}", fg='cyan', bold=True), nl=False)
            click.echo(click.style(f" [{issue.project}]", fg='blue'), nl=False)
            click.echo(click.style(f" [{issue.tracker}]", fg='magenta'), nl=False)
            click.echo(click.style(f" {subject}", fg='white'), nl=False)
            click.echo(click.style(f" ({issue.status})", fg=status_color))
        click.echo()


def display_time_entries_list(time_entries, max_entries=5):
    """Display a list of time entries."""
    if time_entries:
        click.echo(click.style("⏰ Recent Time Entries", fg='green', bold=True))
        for entry in time_entries[:max_entries]:
            click.echo(click.style(f"#{entry.issue_id}", fg='cyan'), nl=False)
            click.echo(click.style(f" {entry.hours:.1f}h", fg='yellow'), nl=False)
            click.echo(click.style(f" {entry.spent_on.strftime('%Y-%m-%d')}", fg='white'), nl=False)
            if hasattr(entry, 'user'):
                click.echo(click.style(f" {entry.user}", fg='white'), nl=False)
            comments = entry.comments[:30] + "..." if len(entry.comments) > 30 else entry.comments
            click.echo(click.style(f" {comments}", fg='white'))


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


@main.command()
@click.option('--project', help='Project identifier or name for project overview')
@click.option('--start-date', help='Start date for overview (YYYY-MM-DD format)')
@click.option('--end-date', help='End date for overview (YYYY-MM-DD format)')
def overview(project, start_date, end_date):
    """Show overview of issues and time tracking."""
    try:
        from .overview import get_personal_overview, get_project_overview

        # Parse and validate dates if provided
        date_range = None
        if start_date or end_date:
            from datetime import datetime
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
                end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
                date_range = (start, end)
            except ValueError as e:
                click.echo(click.style(f"❌ Invalid date format. Use YYYY-MM-DD: {e}", fg='red', bold=True), err=True)
                return

        if project:
            # Project overview
            click.echo(click.style(f"📊 Project Overview: {project}", fg='blue', bold=True))
            if date_range:
                click.echo(click.style(f"Date Range: {start_date or 'Start'} to {end_date or 'End'}", fg='cyan'))
            click.echo()

            with Spinner("Loading project data..."):
                overview_data = get_project_overview(project, date_range)

            display_project_overview(overview_data)
        else:
            # Personal overview
            click.echo(click.style("👤 Personal Overview", fg='blue', bold=True))
            if date_range:
                click.echo(click.style(f"Date Range: {start_date or 'Start'} to {end_date or 'End'}", fg='cyan'))
            click.echo()

            with Spinner("Loading your data..."):
                overview_data = get_personal_overview(date_range)

            display_personal_overview(overview_data)

    except AuthError as e:
        click.echo(click.style(f"🔐 Authentication required: {e}", fg='red', bold=True), err=True)
        click.echo(click.style("Use 'red login --server <URL>' to authenticate", fg='cyan'))
    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg='red', bold=True), err=True)


def display_personal_overview(data: Dict[str, Any]) -> None:
    """Display personal overview."""
    stats = data['stats']
    issues = data['issues'][:5]  # Show top 5 issues
    time_entries = data['time_entries'][:5]  # Show recent 5 time entries
    date_range = data.get('date_range')

    # Summary stats
    click.echo(click.style("📈 Summary", fg='green', bold=True))
    click.echo(click.style(f"Total Issues: {stats['total_issues']}", fg='cyan'))
    click.echo(click.style(f"Open Issues: {stats['open_issues']}", fg='yellow'))
    
    # Show appropriate time period in summary
    period_desc = format_date_range_description(date_range)
    if period_desc:
        click.echo(click.style(f"Total Hours ({period_desc}): {stats['total_hours']:.1f}", fg='cyan'))
        click.echo(click.style(f"Hours in Period: {stats['this_week_hours']:.1f}", fg='cyan'))
    else:
        click.echo(click.style(f"Total Hours (30 days): {stats['total_hours']:.1f}", fg='cyan'))
        click.echo(click.style(f"Hours This Week: {stats['this_week_hours']:.1f}", fg='cyan'))
    
    click.echo(click.style(f"Recent Activity: {stats['recent_issues_count']} issues updated", fg='cyan'))
    click.echo()

    # Issues by status and project
    display_stats_section("Issues by Status", stats['status_counts'])
    display_stats_section("Issues by Project", stats.get('project_counts'), "🏢")

    # Recent issues and time entries
    display_issues_list(issues, truncate_subject=False)
    display_time_entries_list(time_entries)


def display_project_overview(data: Dict[str, Any]) -> None:
    """Display project overview."""
    stats = data['stats']
    issues = data['issues'][:5]  # Show top 5 issues
    time_entries = data['time_entries'][:5]  # Show recent 5 time entries

    # Summary stats
    click.echo(click.style("📈 Summary", fg='green', bold=True))
    click.echo(click.style(f"Total Issues: {stats['total_issues']}", fg='cyan'))
    click.echo(click.style(f"Total Hours Logged: {stats['total_hours']:.1f}", fg='cyan'))
    click.echo(click.style(f"Contributors: {stats['contributors_count']}", fg='cyan'))
    click.echo()

    # Issues by status and tracker
    display_stats_section("Issues by Status", stats['status_counts'])
    display_stats_section("Issues by Tracker", stats['tracker_counts'], "🏷️")

    # Recent issues and time entries
    display_issues_list(issues, truncate_subject=True)
    display_time_entries_list(time_entries)


if __name__ == "__main__":
    # make it runnable as `python -m red.cli` for local dev
    main(prog_name="red")
