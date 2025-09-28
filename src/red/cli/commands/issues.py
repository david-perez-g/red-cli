"""Issue management CLI commands."""

from __future__ import annotations

from typing import Iterable, Tuple

import click

from ..app import AppContainer
from ..presenters.spinner import Spinner
from ...domain.exceptions import AuthorizationRequiredError


def _render_issue(issue) -> None:
    status = issue.status
    tracker = issue.tracker
    subject = issue.subject

    if status.lower() in {"new", "open"}:
        status_color = "green"
    elif status.lower() in {"in progress", "assigned"}:
        status_color = "yellow"
    elif status.lower() in {"resolved", "closed"}:
        status_color = "red"
    else:
        status_color = "white"

    click.echo(click.style(f"#{issue.id}", fg="cyan", bold=True), nl=False)
    click.echo(click.style(f" [{tracker}]", fg="magenta"), nl=False)
    click.echo(click.style(f" {subject}", fg="white", bold=True))
    click.echo(click.style("  Status: ", fg="white"), nl=False)
    click.echo(click.style(status, fg=status_color, bold=True))
    click.echo()


@click.command()
@click.argument("issue_ids", nargs=-1)
@click.option("--show-first", type=int, default=20, help="Show first N issues")
@click.pass_obj
def issues(app: AppContainer, issue_ids: Tuple[str, ...], show_first: int) -> None:
    """List issues for the current user or specific IDs."""
    try:
        click.echo(click.style("🔍 Fetching issues...", fg="blue"))
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
        click.echo(click.style(f"📋 Found {len(fetched)} issues", fg="blue", bold=True))
        click.echo()

        for issue in fetched[:show_first]:
            _render_issue(issue)
        if len(fetched) > show_first:
            click.echo(click.style(f"... and {len(fetched) - show_first} more issues", fg="yellow"))
    except AuthorizationRequiredError as exc:
        click.echo(click.style(f"🔐 Authentication required: {exc}", fg="red", bold=True), err=True)
        click.echo(click.style("Use 'red login --server <URL>' to authenticate", fg="cyan"))
    except Exception as exc:  # noqa: BLE001
        click.echo(click.style(f"❌ Error: {exc}", fg="red", bold=True), err=True)


def register(group: click.Group) -> None:
    group.add_command(issues)
