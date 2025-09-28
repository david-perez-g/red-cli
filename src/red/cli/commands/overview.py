"""Overview reporting CLI command."""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Tuple

import click
from ..app import AppContainer
from ..presenters.formatters import render_personal_overview, render_project_overview
from ..presenters.spinner import Spinner
from ...domain.exceptions import AuthorizationRequiredError

DateRange = Tuple[Optional[datetime], Optional[datetime]]

def _parse_date(value: Optional[str]) -> Optional[datetime]:
	if not value:
		return None
	return datetime.strptime(value, "%Y-%m-%d")


@click.command()
@click.option("--project", help="Project identifier or name for project overview")
@click.option("--start-date", help="Start date for overview (YYYY-MM-DD format)")
@click.option("--end-date", help="End date for overview (YYYY-MM-DD format)")
@click.pass_obj
def overview(app: AppContainer, project: Optional[str], start_date: Optional[str], end_date: Optional[str]) -> None:
	"""Display personal or project overview statistics."""
	try:
		date_range = None
		if start_date or end_date:
			try:
				start = _parse_date(start_date)
				end = _parse_date(end_date)
			except ValueError as exc:
				click.echo(click.style(f"❌ Invalid date format. Use YYYY-MM-DD: {exc}", fg="red", bold=True), err=True)
				return
			date_range = (start.date() if start else None, end.date() if end else None)

		if project:
			with Spinner("Loading project data..."):
				payload = app.overview.project_overview(project, date_range)
			render_project_overview(project, payload)
		else:
			with Spinner("Loading your data..."):
				payload = app.overview.personal_overview(date_range)
			render_personal_overview(payload)
	except AuthorizationRequiredError as exc:
		click.echo(click.style(f"🔐 Authentication required: {exc}", fg="red", bold=True), err=True)
		click.echo(click.style("Use 'red login --server <URL>' to authenticate", fg="cyan"))
	except Exception as exc:  # noqa: BLE001
		click.echo(click.style(f"❌ Error: {exc}", fg="red", bold=True), err=True)


def register(group: click.Group) -> None:
	group.add_command(overview)
