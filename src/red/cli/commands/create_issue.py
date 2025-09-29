"""CLI command for creating new issues."""

from __future__ import annotations

from typing import Optional

import click

from ..app import AppContainer
from ..presenters.spinner import Spinner
from ..presenters.symbols import SYMBOLS
from ...domain.exceptions import AuthorizationRequiredError


@click.command("create")
@click.option("-p", "--project", required=True, help="Project identifier or numeric ID for the new issue")
@click.option("-s", "--subject", help="Short subject line for the new issue")
@click.option("-d", "--description", help="Optional detailed description (use quotes or piping for multi-line text)")
@click.option("-T", "--tracker", help="Tracker name or ID (e.g. 'Bug', 'Feature')")
@click.option("-S", "--status", help="Status name or ID for the new issue")
@click.option("--start-date", help="Start date for the issue (YYYY-MM-DD format)")
@click.option("--due-date", help="Due date for the issue (YYYY-MM-DD format)")
@click.option("-a", "--assignee", help="Assignee name, login, or ID for the issue")
@click.pass_obj
def create_issue(
    app: AppContainer,
    project: str,
    subject: Optional[str],
    description: Optional[str],
    tracker: Optional[str],
    status: Optional[str],
    start_date: Optional[str],
    due_date: Optional[str],
    assignee: Optional[str],
) -> None:
    """Create a new issue in Redmine."""
    try:
        if not subject:
            subject = click.prompt(click.style("Subject", fg="yellow"), type=str)
        if not subject.strip():
            raise click.UsageError("Subject cannot be empty")

        with Spinner("Creating issue..."):
            created_issue = app.issues.create_issue(
                project=project,
                subject=subject.strip(),
                description=description,
                tracker=tracker,
                status=status,
                start_date=start_date,
                due_date=due_date,
                assignee=assignee,
            )

        success_prefix = SYMBOLS.get("success")
        click.echo()
        click.echo(click.style(f"{success_prefix} Issue #{created_issue.id} created", fg="green", bold=True))
        click.echo(click.style(f"Subject: {created_issue.subject}", fg="cyan"))
        click.echo(click.style(f"Project: {created_issue.project}", fg="cyan"))
        if created_issue.tracker:
            click.echo(click.style(f"Tracker: {created_issue.tracker}", fg="cyan"))
        if created_issue.status:
            click.echo(click.style(f"Status: {created_issue.status}", fg="cyan"))
        if created_issue.assigned_to:
            click.echo(click.style(f"Assignee: {created_issue.assigned_to}", fg="cyan"))
        if start_date:
            click.echo(click.style(f"Start Date: {start_date}", fg="cyan"))
        if due_date:
            click.echo(click.style(f"Due Date: {due_date}", fg="cyan"))

        session = app.auth.current_session()
        if session:
            base_url = session.server_url.rstrip("/")
            issue_url = f"{base_url}/issues/{created_issue.id}"
            info_prefix = SYMBOLS.get("info")
            click.echo(click.style(f"{info_prefix} View: {issue_url}", fg="blue"))
    except AuthorizationRequiredError as exc:
        err_prefix = SYMBOLS.get("auth", stream=click.get_text_stream("stderr"))
        click.echo(click.style(f"{err_prefix} Authentication required: {exc}", fg="red", bold=True), err=True)
        click.echo(click.style("Use 'red login --server <URL>' to authenticate", fg="cyan"))
    except ValueError as exc:
        err_prefix = SYMBOLS.get("error", stream=click.get_text_stream("stderr"))
        click.echo(click.style(f"{err_prefix} {exc}", fg="red", bold=True), err=True)
        click.echo(click.style("Use --tracker/--status/--assignee with a valid name or numeric ID", fg="yellow"), err=True)
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        err_prefix = SYMBOLS.get("error", stream=click.get_text_stream("stderr"))
        click.echo(click.style(f"{err_prefix} Failed to create issue: {exc}", fg="red", bold=True), err=True)


def register(group: click.Group) -> None:
    group.add_command(create_issue)
