"""Issue management CLI commands."""

from __future__ import annotations

from typing import Tuple

import click

from ..app import AppContainer
from ..presenters.spinner import Spinner
from ..presenters.symbols import SYMBOLS
from ...domain.exceptions import AuthorizationRequiredError


def _render_issue_detailed(issue) -> None:
    """Render issue with full details."""
    status = issue.status
    tracker = issue.tracker
    subject = issue.subject

    if status.lower() in {"new", "open", "to do"}:
        status_color = "green"
    elif status.lower() in {"in progress", "assigned"}:
        status_color = "yellow"
    elif status.lower() in {"resolved", "closed"}:
        status_color = "red"
    else:
        status_color = "white"

    # Header
    click.echo(click.style(f"#{issue.id}", fg="cyan", bold=True), nl=False)
    click.echo(click.style(f" [{tracker}]", fg="magenta"), nl=False)
    click.echo(click.style(f" {subject}", fg="white", bold=True))
    click.echo()

    # Status and Priority
    click.echo(click.style("Status: ", fg="white"), nl=False)
    click.echo(click.style(status, fg=status_color, bold=True), nl=False)
    click.echo(click.style(" | Priority: ", fg="white"), nl=False)
    click.echo(click.style(issue.priority, fg="yellow"))
    
    # Project
    click.echo(click.style("Project: ", fg="white"), nl=False)
    click.echo(click.style(issue.project, fg="blue"))
    
    # Author and Assignee
    click.echo(click.style("Author: ", fg="white"), nl=False)
    click.echo(click.style(issue.author, fg="green"), nl=False)
    if issue.assigned_to:
        click.echo(click.style(" | Assigned to: ", fg="white"), nl=False)
        click.echo(click.style(issue.assigned_to, fg="green"))
    else:
        click.echo()
    
    # Dates
    click.echo(click.style("Created: ", fg="white"), nl=False)
    click.echo(click.style(issue.created_on.strftime("%Y-%m-%d %H:%M"), fg="cyan"), nl=False)
    click.echo(click.style(" | Updated: ", fg="white"), nl=False)
    click.echo(click.style(issue.updated_on.strftime("%Y-%m-%d %H:%M"), fg="cyan"))
    
    # Progress and Estimates
    if issue.done_ratio > 0:
        click.echo(click.style(f"Progress: {issue.done_ratio}% done", fg="magenta"))
    if issue.estimated_hours:
        click.echo(click.style(f"Estimated hours: {issue.estimated_hours}", fg="magenta"))
    
    # Description
    if issue.description:
        click.echo()
        click.echo(click.style("Description:", fg="white", bold=True))
        # Wrap description for better readability
        desc_lines = issue.description.split('\n')
        for line in desc_lines[:5]:  # Limit to first 5 lines
            click.echo(click.style(f"  {line}", fg="white"))
        if len(desc_lines) > 5:
            ellipsis = SYMBOLS.get("ellipsis")
            click.echo(click.style(f"  {ellipsis} (truncated)", fg="yellow"))
    
    click.echo()  # Empty line between issues
    click.echo(click.style("─" * 60, fg="bright_black"))  # Separator line


def _render_issue_oneline(issue) -> None:
    """Render issue in compact oneline format."""
    status = issue.status
    tracker = issue.tracker
    subject = issue.subject

    if status.lower() in {"new", "open", "to do"}:
        status_color = "green"
    elif status.lower() in {"in progress", "assigned"}:
        status_color = "yellow"
    elif status.lower() in {"resolved", "closed"}:
        status_color = "red"
    else:
        status_color = "white"

    click.echo(click.style(f"#{issue.id}", fg="cyan", bold=True), nl=False)
    click.echo(click.style(f" [{tracker}]", fg="magenta"), nl=False)
    click.echo(click.style(f" {subject}", fg="white", bold=True), nl=False)
    click.echo(click.style(f" ({status})", fg=status_color))


def _render_issue(issue, oneline: bool = False) -> None:
    """Render an issue, either detailed or oneline."""
    if oneline:
        _render_issue_oneline(issue)
    else:
        _render_issue_detailed(issue)


@click.command()
@click.argument("issue_ids", nargs=-1)
@click.option("--show-first", type=int, default=20, help="Show first N issues")
@click.option("--oneline", is_flag=True, help="Show issues in compact oneline format")
@click.pass_obj
def issues(app: AppContainer, issue_ids: Tuple[str, ...], show_first: int, oneline: bool) -> None:
    """List issues for the current user or specific IDs."""
    try:
        search_prefix = SYMBOLS.get("search")
        click.echo(click.style(f"{search_prefix} Fetching issues...", fg="blue"))
        if issue_ids:
            with Spinner("Loading issues..."):
                fetched = []
                for spec in issue_ids[:show_first]:
                    issues = app.issues.list_by_ids((spec,), limit=None)
                    fetched.extend(issues)
                    if len(fetched) >= show_first:
                        break
        else:
            with Spinner("Loading your issues..."):
                fetched = app.issues.list_for_current_user()

        click.echo()
        found_prefix = SYMBOLS.get("list")
        click.echo(click.style(f"{found_prefix} Found {len(fetched)} issues", fg="blue", bold=True))
        click.echo()

        for issue in fetched[:show_first]:
            _render_issue(issue, oneline)
        if len(fetched) > show_first:
            ellipsis = SYMBOLS.get("ellipsis")
            click.echo(click.style(f"{ellipsis} {len(fetched) - show_first} more issues", fg="yellow"))
    except AuthorizationRequiredError as exc:
        auth_prefix = SYMBOLS.get("auth", stream=click.get_text_stream("stderr"))
        click.echo(click.style(f"{auth_prefix} Authentication required: {exc}", fg="red", bold=True), err=True)
        click.echo(click.style("Use 'red login --server <URL>' to authenticate", fg="cyan"))
    except Exception as exc:  # noqa: BLE001
        error_prefix = SYMBOLS.get("error", stream=click.get_text_stream("stderr"))
        click.echo(click.style(f"{error_prefix} Error: {exc}", fg="red", bold=True), err=True)


def register(group: click.Group) -> None:
    group.add_command(issues)
