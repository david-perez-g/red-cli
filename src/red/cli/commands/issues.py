"""Issue management CLI commands."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, TextIO, Tuple

import click

from ..app import AppContainer
from ..presenters.spinner import Spinner
from ..presenters.symbols import SYMBOLS, use_emoji
from ...domain.exceptions import AuthorizationRequiredError


def _render_issue_detailed(issue, logged_hours: Optional[float] = None) -> None:
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
    if logged_hours is not None:
        click.echo(click.style(f"Spent time: {logged_hours} hours", fg="cyan"))
    
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
    stream = click.get_text_stream("stdout")
    separator_char = "─" if use_emoji(stream) else "-"
    click.echo(click.style(separator_char * 60, fg="bright_black"))  # Separator line


def _render_issue_oneline(issue, logged_hours: Optional[float] = None) -> None:
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
    if logged_hours is not None:
        click.echo(click.style(f" [spent {logged_hours}h]", fg="cyan"), nl=False)
    click.echo(click.style(f" ({status})", fg=status_color))


def _render_issue(issue, oneline: bool = False, logged_hours: Optional[float] = None) -> None:
    """Render an issue, either detailed or oneline."""
    if oneline:
        _render_issue_oneline(issue, logged_hours)
    else:
        _render_issue_detailed(issue, logged_hours)


def _normalize_for_csv(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        if "name" in value and isinstance(value["name"], (str, int, float, bool)):
            return _normalize_for_csv(value["name"])
        if "value" in value and not isinstance(value["value"], (dict, list)):
            return _normalize_for_csv(value["value"])
        normalized = {key: _normalize_for_csv(inner) for key, inner in value.items()}
        return json.dumps(normalized, ensure_ascii=False)
    if isinstance(value, list):
        normalized_items = [_normalize_for_csv(item) for item in value]
        normalized_items = [item for item in normalized_items if item not in ("", None)]
        return "; ".join(str(item) for item in normalized_items)
    return json.dumps(value, ensure_ascii=False)


def _export_issues_to_csv(issues: Sequence[Any], stream: TextIO) -> int:
    records = []
    for issue in issues:
        raw = getattr(issue, "raw", None)
        if raw:
            records.append(raw)
    if not records:
        return 0

    headers = sorted({key for record in records for key in record.keys()})
    # Ensure 'id' comes first if it exists
    if "id" in headers:
        headers.remove("id")
        headers.insert(0, "id")
    
    writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    for record in records:
        row = {key: _normalize_for_csv(record.get(key)) for key in headers}
        writer.writerow(row)

    return len(records)


@click.command()
@click.argument("issue_ids", nargs=-1)
@click.option("--show-first", type=int, default=20, show_default=True, help="Number of issues to display per page")
@click.option("--limit", type=int, help="Limit the number of issues fetched from the API (defaults to --show-first for interactive display)")
@click.option("--page", type=int, default=1, show_default=True, help="Page number to fetch when using pagination")
@click.option("--oneline", is_flag=True, help="Show issues in compact oneline format")
@click.option("--no-logged-hours", is_flag=True, help="Skip fetching logged hours to improve performance")
@click.option("--csv", "as_csv", is_flag=True, help="Output the fetched issues as CSV")
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Write CSV output to the given file (use with --csv)",
)
@click.option("--project", type=str, help="Filter issues by project name or identifier")
@click.pass_obj
def issues(
    app: AppContainer,
    issue_ids: Tuple[str, ...],
    show_first: int,
    limit: Optional[int],
    page: int,
    oneline: bool,
    as_csv: bool,
    output_path: Optional[Path],
    project: Optional[str],
    no_logged_hours: bool,
) -> None:
    """List issues for the current user, specific IDs, or by project."""
    try:
        if output_path and not as_csv:
            raise click.UsageError("--output/-o can only be used together with --csv")

        if page < 1:
            raise click.UsageError("--page must be greater than or equal to 1")

        if issue_ids and project:
            raise click.UsageError("Cannot specify both issue IDs and --project option")

        if not as_csv:
            search_prefix = SYMBOLS.get("search")
            click.echo(click.style(f"{search_prefix} Fetching issues (page {page})...", fg="blue"))

        fetched: list = []

        if issue_ids:
            if as_csv:
                for spec in issue_ids[:show_first]:
                    issues = app.issues.list_by_ids((spec,), limit=None)
                    fetched.extend(issues)
                    if len(fetched) >= show_first:
                        break
            else:
                with Spinner("Loading issues..."):
                    for spec in issue_ids[:show_first]:
                        issues = app.issues.list_by_ids((spec,), limit=None)
                        fetched.extend(issues)
                        if len(fetched) >= show_first:
                            break
        elif project:
            if as_csv:
                fetch_limit = limit
                offset = (page - 1) * fetch_limit if fetch_limit else None
                fetched = app.issues.list_by_project(project, limit=fetch_limit, offset=offset)
            else:
                fetch_limit = limit or show_first
                offset = (page - 1) * fetch_limit if fetch_limit else None
                with Spinner(f"Loading issues for project '{project}' (page {page})..."):
                    fetched = app.issues.list_by_project(project, limit=fetch_limit, offset=offset)
        else:
            if as_csv:
                fetch_limit = limit
                offset = (page - 1) * fetch_limit if fetch_limit else None
                fetched = app.issues.list_for_current_user(limit=fetch_limit, offset=offset)
            else:
                fetch_limit = limit or show_first
                offset = (page - 1) * fetch_limit if fetch_limit else None
                with Spinner(f"Loading your issues (page {page})..."):
                    fetched = app.issues.list_for_current_user(limit=fetch_limit, offset=offset)

        if as_csv:
            export_source = fetched
            if output_path:
                target = output_path.expanduser().resolve()
                try:
                    with target.open("w", encoding="utf-8", newline="") as handle:
                        exported = _export_issues_to_csv(export_source, handle)
                except Exception as export_exc:  # noqa: BLE001
                    err_stream = click.get_text_stream("stderr")
                    error_prefix = SYMBOLS.get("error", stream=err_stream)
                    click.echo(
                        click.style(f"{error_prefix} Failed to write CSV: {export_exc}", fg="red", bold=True),
                        err=True,
                    )
                    return
                save_prefix = SYMBOLS.get("save")
                click.echo(click.style(f"{save_prefix} Saved {exported} issues to {target}", fg="green"))
                return

            stream = click.get_text_stream("stdout") or sys.stdout
            exported = _export_issues_to_csv(export_source, stream)
            if hasattr(stream, "flush"):
                stream.flush()
            if exported == 0:
                err_stream = click.get_text_stream("stderr")
                warn_prefix = SYMBOLS.get("warning", stream=err_stream)
                click.echo(
                    click.style(f"{warn_prefix} No issue data available to export", fg="yellow"),
                    err=True,
                )
            return

        click.echo()
        found_prefix = SYMBOLS.get("list")
        click.echo(click.style(f"{found_prefix} Found {len(fetched)} issues", fg="blue", bold=True))
        click.echo()

        displayed_issues = fetched[:show_first]
        logged_hours_map: Dict[int, float] = {}
        if displayed_issues and not no_logged_hours:
            logged_hours_map = app.issues.get_logged_hours_bulk([issue.id for issue in displayed_issues])

        for issue in displayed_issues:
            _render_issue(issue, oneline, logged_hours_map.get(issue.id))

        if len(fetched) > len(displayed_issues):
            ellipsis = SYMBOLS.get("ellipsis")
            click.echo(click.style(f"{ellipsis} {len(fetched) - len(displayed_issues)} more issues", fg="yellow"))
    except AuthorizationRequiredError as exc:
        auth_prefix = SYMBOLS.get("auth", stream=click.get_text_stream("stderr"))
        click.echo(click.style(f"{auth_prefix} Authentication required: {exc}", fg="red", bold=True), err=True)
        click.echo(click.style("Use 'red login --server <URL>' to authenticate", fg="cyan"))
    except Exception as exc:  # noqa: BLE001
        error_prefix = SYMBOLS.get("error", stream=click.get_text_stream("stderr"))
        click.echo(click.style(f"{error_prefix} Error: {exc}", fg="red", bold=True), err=True)


def register(group: click.Group) -> None:
    group.add_command(issues)
