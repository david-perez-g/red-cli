"""CLI command for viewing logged time entries."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import click

from ..app import AppContainer
from ...domain.exceptions import AuthorizationRequiredError


@click.command("hours")
@click.option("--from-date", "from_date", help="Start date for time entries (YYYY-MM-DD)")
@click.option("--to-date", "to_date", help="End date for time entries (YYYY-MM-DD)")
@click.option("-p", "--project", help="Filter by project name or identifier")
@click.option("--limit", type=int, help="Limit number of entries to show")
@click.option("--csv", is_flag=True, help="Output in CSV format")
@click.pass_obj
def logged_hours(
    app: AppContainer,
    from_date: Optional[str],
    to_date: Optional[str],
    project: Optional[str],
    limit: Optional[int],
    csv: bool,
) -> None:
    """View your logged time entries with optional filtering.

    Shows time entries logged by the current user. Use filters to narrow down results.

    Examples:
        red hours                                    # All time entries
        red hours --from-date 2025-09-01             # From specific date
        red hours --from-date 2025-09-01 --to-date 2025-09-30  # Date range
        red hours --project "MyProject"              # Project specific
        red hours --limit 10                         # Limit results
        red hours --csv                              # CSV output
    """
    try:
        time_entries = app.issues.get_time_entries(
            from_date=from_date,
            to_date=to_date,
            project=project,
            limit=limit,
        )

        if not time_entries:
            click.echo("No time entries found matching the criteria.")
            return

        if csv:
            _output_csv(time_entries)
        else:
            _output_table(time_entries)

    except AuthorizationRequiredError as exc:
        err_prefix = click.get_text_stream("stderr").write("🔐 ")
        click.echo(click.style(f"Authentication required: {exc}", fg="red", bold=True), err=True)
        click.echo(click.style("Use 'red login --server <URL>' to authenticate", fg="cyan"))
    except ValueError as exc:
        err_prefix = click.get_text_stream("stderr").write("❌ ")
        click.echo(click.style(f"Invalid input: {exc}", fg="red", bold=True), err=True)
    except Exception as exc:  # noqa: BLE001
        err_prefix = click.get_text_stream("stderr").write("❌ ")
        click.echo(click.style(f"Failed to retrieve time entries: {exc}", fg="red", bold=True), err=True)


def _output_table(time_entries: list) -> None:
    """Output time entries in a formatted table."""
    # Calculate totals
    total_hours = sum(float(entry.get("hours", 0)) for entry in time_entries)

    # Group by week for summary
    entries_by_week = {}
    for entry in time_entries:
        spent_on_str = entry.get("spent_on", "Unknown")
        if spent_on_str == "Unknown":
            week_key = "Unknown"
        else:
            try:
                spent_date = datetime.strptime(spent_on_str, "%Y-%m-%d")
                # Get ISO week number and year
                week_num = spent_date.isocalendar()[1]
                year = spent_date.isocalendar()[0]
                week_key = f"{year}-W{week_num:02d}"

                # Store the week start date for display
                week_start = spent_date - timedelta(days=spent_date.weekday())  # Monday
                week_end = week_start + timedelta(days=6)  # Sunday
                entry["_week_display"] = f"{week_key}: {week_start.strftime('%b %d')}-{week_end.strftime('%d')}"
            except ValueError:
                week_key = spent_on_str

        if week_key not in entries_by_week:
            entries_by_week[week_key] = []
        entries_by_week[week_key].append(entry)

    # Header
    click.echo(click.style("📊 Logged Hours Summary (by week)", fg="blue", bold=True))
    click.echo()

    # Summary by week
    for week_key in sorted(entries_by_week.keys(), reverse=True):
        week_entries = entries_by_week[week_key]
        week_total = sum(float(entry.get("hours", 0)) for entry in week_entries)

        # Get week display name
        week_display = week_entries[0].get("_week_display", week_key) if week_entries else week_key
        click.echo(click.style(f"📅 {week_display} - {week_total:.2f} hours", fg="cyan", bold=True))

        # Group entries by date within the week
        entries_by_date = {}
        for entry in week_entries:
            spent_on = entry.get("spent_on", "Unknown")
            if spent_on not in entries_by_date:
                entries_by_date[spent_on] = []
            entries_by_date[spent_on].append(entry)

        # Show entries grouped by date within the week
        for date in sorted(entries_by_date.keys(), reverse=True):
            date_entries = entries_by_date[date]
            date_total = sum(float(entry.get("hours", 0)) for entry in date_entries)

            click.echo(click.style(f"  📅 {date} ({date_total:.2f}h)", fg="yellow"))

            for entry in date_entries:
                issue = entry.get("issue", {})
                project = issue.get("project", {}).get("name", "Unknown")
                subject = issue.get("subject", "Unknown")
                hours = float(entry.get("hours", 0))
                comments = entry.get("comments", "").strip()

                click.echo(f"    🔹 #{issue.get('id', 'N/A')} - {subject}")
                click.echo(f"       📁 {project} | ⏱️  {hours:.2f}h" + (f" | 💬 {comments}" if comments else ""))
        click.echo()

    # Grand total
    click.echo(click.style(f"📈 Total: {total_hours:.2f} hours across {len(time_entries)} entries", fg="green", bold=True))


def _output_csv(time_entries: list) -> None:
    """Output time entries in CSV format."""
    import csv
    import sys

    writer = csv.writer(sys.stdout)
    writer.writerow([
        "date", "issue_id", "project", "subject", "hours", "comments"
    ])

    for entry in time_entries:
        issue = entry.get("issue", {})
        writer.writerow([
            entry.get("spent_on", ""),
            issue.get("id", ""),
            issue.get("project", {}).get("name", ""),
            issue.get("subject", ""),
            entry.get("hours", 0),
            entry.get("comments", ""),
        ])


def register(group: click.Group) -> None:
    group.add_command(logged_hours)