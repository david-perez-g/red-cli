"""Presentation helpers for formatting CLI output."""

from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, Optional, Sequence

import click

from ...application.dto.overview import IssueSummary, OverviewPayload, OverviewStats, TimeEntrySummary


def _format_date_range(date_range: Optional[Sequence[Optional[date]]]) -> Optional[str]:
    if not date_range or not any(date_range):
        return None
    start, end = date_range
    if start and end:
        return f"{start} to {end}"
    if start:
        return f"from {start}"
    if end:
        return f"to {end}"
    return None


def display_stats_section(title: str, stats_dict: Dict[str, int], emoji: str = "📋") -> None:
    if not stats_dict:
        return
    click.echo(click.style(f"{emoji} {title}", fg="green", bold=True))
    for key, count in stats_dict.items():
        click.echo(click.style(f"  {key}: {count}", fg="white"))
    click.echo()


def display_issues(issues: Iterable[IssueSummary], *, max_items: int = 5, truncate: bool = True) -> None:
    issues = list(issues)[:max_items]
    if not issues:
        return
    click.echo(click.style("🔥 Recent Issues", fg="green", bold=True))
    for issue in issues:
        status_color = "green" if issue.status.lower() in {"new", "open"} else "yellow"
        subject = issue.subject
        if truncate and len(subject) > 50:
            subject = subject[:50] + "..."
        click.echo(click.style(f"#{issue.id}", fg="cyan", bold=True), nl=False)
        click.echo(click.style(f" [{issue.project}]", fg="blue"), nl=False)
        click.echo(click.style(f" [{issue.tracker}]", fg="magenta"), nl=False)
        click.echo(click.style(f" {subject}", fg="white"), nl=False)
        click.echo(click.style(f" ({issue.status})", fg=status_color))
    click.echo()


def display_time_entries(entries: Iterable[TimeEntrySummary], *, max_items: int = 5) -> None:
    entries = list(entries)[:max_items]
    if not entries:
        return
    click.echo(click.style("⏰ Recent Time Entries", fg="green", bold=True))
    for entry in entries:
        click.echo(click.style(f"#{entry.issue_id}", fg="cyan"), nl=False)
        click.echo(click.style(f" {entry.hours:.1f}h", fg="yellow"), nl=False)
        click.echo(click.style(entry.spent_on.strftime("%Y-%m-%d"), fg="white"), nl=False)
        click.echo(click.style(f" {entry.user}", fg="white"), nl=False)
        comments = entry.comments
        if len(comments) > 30:
            comments = comments[:30] + "..."
        click.echo(click.style(f" {comments}", fg="white"))
    click.echo()


def render_personal_overview(payload: OverviewPayload) -> None:
    stats = payload.stats
    click.echo(click.style("👤 Personal Overview", fg="blue", bold=True))
    period = _format_date_range(payload.date_range)
    if period:
        click.echo(click.style(f"Date Range: {period}", fg="cyan"))
    click.echo()

    click.echo(click.style("📈 Summary", fg="green", bold=True))
    click.echo(click.style(f"Total Issues: {stats.total_issues}", fg="cyan"))
    click.echo(click.style(f"Open Issues: {stats.open_issues}", fg="yellow"))
    click.echo(click.style(f"Total Hours: {stats.total_hours:.1f}", fg="cyan"))
    click.echo(click.style(f"Hours in Period: {stats.this_period_hours:.1f}", fg="cyan"))
    click.echo(click.style(f"Recent Activity: {stats.recent_issues} issues updated", fg="cyan"))
    click.echo()

    display_stats_section("Issues by Status", stats.status_counts)
    display_stats_section("Issues by Project", stats.project_counts, "🏢")

    display_issues(payload.issues, truncate=False)
    display_time_entries(payload.time_entries)


def render_project_overview(project: str, payload: OverviewPayload) -> None:
    stats = payload.stats
    click.echo(click.style(f"📊 Project Overview: {project}", fg="blue", bold=True))
    period = _format_date_range(payload.date_range)
    if period:
        click.echo(click.style(f"Date Range: {period}", fg="cyan"))
    click.echo()

    click.echo(click.style("📈 Summary", fg="green", bold=True))
    click.echo(click.style(f"Total Issues: {stats.total_issues}", fg="cyan"))
    click.echo(click.style(f"Total Hours Logged: {stats.total_hours:.1f}", fg="cyan"))
    contributors = stats.extra.get("contributors_count", 0) if hasattr(stats, "extra") else 0
    click.echo(click.style(f"Contributors: {contributors}", fg="cyan"))
    click.echo()

    display_stats_section("Issues by Status", stats.status_counts)
    display_stats_section("Issues by Tracker", stats.tracker_counts, "🏷️")

    display_issues(payload.issues)
    display_time_entries(payload.time_entries)
