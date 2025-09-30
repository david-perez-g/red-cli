"""CLI command for creating new issues."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

import click

from ..app import AppContainer
from ..presenters.spinner import Spinner
from ..presenters.symbols import SYMBOLS
from ...domain.exceptions import AuthorizationRequiredError
from .issues import _export_issues_to_csv


def _create_issues_from_csv(app: AppContainer, csv_path: Path, output_path: Optional[Path] = None) -> None:
    """Create multiple issues from CSV file."""
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Validate CSV headers
            required_columns = {"project_id", "subject"}
            optional_columns = {"description", "tracker_id", "status_id", "assigned_to_id", "start_date", "due_date"}
            allowed_columns = required_columns | optional_columns
            
            if not reader.fieldnames:
                raise click.UsageError(f"CSV file {csv_path} appears to be empty or has no headers")
            
            fieldnames = set(reader.fieldnames)
            missing_required = required_columns - fieldnames
            if missing_required:
                raise click.UsageError(f"CSV is missing required columns: {', '.join(missing_required)}")
            
            invalid_columns = fieldnames - allowed_columns
            if invalid_columns:
                raise click.UsageError(f"CSV contains invalid columns: {', '.join(invalid_columns)}")
            
            # Read all rows
            rows = list(reader)
            if not rows:
                raise click.UsageError(f"CSV file {csv_path} contains no data rows")
            
            total_issues = len(rows)
            click.echo(click.style(f"📄 Found {total_issues} issues to create from {csv_path}", fg="blue"))
            click.echo()
            
            created_count = 0
            failed_count = 0
            errors = []
            created_issues = []
            
            for i, row in enumerate(rows, 1):
                try:
                    with Spinner(f"Creating issue {i}/{total_issues}..."):
                        created_issue = app.issues.create_issue(
                            project=row["project_id"],
                            subject=row["subject"],
                            description=row.get("description") or None,
                            tracker=row.get("tracker_id") or None,
                            status=row.get("status_id") or None,
                            start_date=row.get("start_date") or None,
                            due_date=row.get("due_date") or None,
                            assignee=row.get("assigned_to_id") or None,
                        )
                    
                    success_prefix = SYMBOLS.get("success")
                    click.echo(click.style(f"{success_prefix} Issue #{created_issue.id} created: {created_issue.subject}", fg="green"))
                    created_count += 1
                    created_issues.append(created_issue)
                    
                except Exception as exc:  # noqa: BLE001
                    error_prefix = SYMBOLS.get("error")
                    click.echo(click.style(f"{error_prefix} Failed to create issue {i}: {exc}", fg="red"))
                    errors.append(f"Row {i}: {exc}")
                    failed_count += 1
            
            # Export to CSV if requested
            if output_path and created_issues:
                try:
                    output_path = output_path.expanduser().resolve()
                    with output_path.open("w", encoding="utf-8", newline="") as handle:
                        exported = _export_issues_to_csv(created_issues, handle)
                    save_prefix = SYMBOLS.get("save")
                    click.echo(click.style(f"{save_prefix} Exported {exported} created issues to {output_path}", fg="green"))
                except Exception as export_exc:  # noqa: BLE001
                    err_stream = click.get_text_stream("stderr")
                    error_prefix = SYMBOLS.get("error", stream=err_stream)
                    click.echo(
                        click.style(f"{error_prefix} Failed to export created issues: {export_exc}", fg="red"),
                        err=True,
                    )
            
            # Summary
            click.echo()
            summary_prefix = SYMBOLS.get("info")
            click.echo(click.style(f"{summary_prefix} Bulk creation completed:", fg="blue", bold=True))
            click.echo(click.style(f"  ✅ Created: {created_count} issues", fg="green"))
            if failed_count > 0:
                click.echo(click.style(f"  ❌ Failed: {failed_count} issues", fg="red"))
                click.echo(click.style("  Errors:", fg="red"))
                for error in errors:
                    click.echo(click.style(f"    • {error}", fg="red"))
    
    except FileNotFoundError:
        raise click.UsageError(f"CSV file not found: {csv_path}")
    except csv.Error as exc:
        raise click.UsageError(f"Invalid CSV format: {exc}")


@click.command("create")
@click.option("-p", "--project", help="Project identifier or numeric ID for the new issue")
@click.option("-s", "--subject", help="Short subject line for the new issue")
@click.option("-d", "--description", help="Optional detailed description (use quotes or piping for multi-line text)")
@click.option("-T", "--tracker", help="Tracker name or ID (e.g. 'Bug', 'Feature')")
@click.option("-S", "--status", help="Status name or ID for the new issue")
@click.option("--start-date", help="Start date for the issue (YYYY-MM-DD format)")
@click.option("--due-date", help="Due date for the issue (YYYY-MM-DD format)")
@click.option("-a", "--assignee", default="me", help="Assignee name, login, or ID for the issue (default: me)")
@click.option(
    "--csv",
    "from_csv",
    is_flag=True,
    help="Create issues from CSV file. CSV must have columns: project_id,subject (required) and optionally: description,tracker_id,status_id,assigned_to_id,start_date,due_date",
)
@click.option(
    "-i",
    "--input",
    "input_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to CSV file for bulk creation (use with --csv)",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Write created issues to CSV file (use with --csv)",
)
@click.pass_obj
def create_issue(
    app: AppContainer,
    project: Optional[str],
    subject: Optional[str],
    description: Optional[str],
    tracker: Optional[str],
    status: Optional[str],
    start_date: Optional[str],
    due_date: Optional[str],
    assignee: Optional[str],
    from_csv: bool,
    input_path: Optional[Path],
    output_path: Optional[Path],
) -> None:
    """Create a new issue in Redmine, or create multiple issues from CSV.

    For single issue creation, use the individual options.
    
    For bulk creation from CSV, use --csv with --input. The CSV must have these columns:
    - project_id (required): Project identifier or numeric ID
    - subject (required): Issue subject
    - description (optional): Issue description  
    - tracker_id (optional): Tracker name or numeric ID
    - status_id (optional): Status name or numeric ID
    - assigned_to_id (optional): Assignee name, login, or numeric ID
    - start_date (optional): Start date in YYYY-MM-DD format
    - due_date (optional): Due date in YYYY-MM-DD format
    """
    try:
        # Validate option combinations
        if output_path and not from_csv:
            raise click.UsageError("--output/-o can only be used with --csv")
        
        if from_csv:
            if not input_path:
                raise click.UsageError("--input/-i is required when using --csv")
            # Check if any single-issue options were provided
            single_options = [project, subject, description, tracker, status, start_date, due_date]
            if any(single_options) or (assignee != "me"):
                raise click.UsageError("Cannot specify individual issue options with --csv")
            
            _create_issues_from_csv(app, input_path, output_path)
            return

        # Single issue creation
        if not project:
            raise click.UsageError("--project/-p is required for single issue creation")
        
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
