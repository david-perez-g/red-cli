# src/red/cli.py
import re
import sys
from typing import Iterator

import click

__all__ = ["main"]

RANGE_RE = re.compile(r"^(\d+)\.\.(\d+)$")

def expand_range_token(token: str) -> Iterator[int]:
    token = token.strip()
    if not token:
        return
    m = RANGE_RE.match(token)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        step = 1 if a <= b else -1
        # range end inclusive
        for i in range(a, b + step, step):
            yield i
    else:
        yield int(token)

def parse_ids(specs: list[str]) -> Iterator[int]:
    """
    Accept forms:
      - "1..10"
      - "1,3,5..8"
      - multiple args: "1..5" "7,9"
      - individual numbers: "1" "2" "3"
    Returns an iterator (doesn't build the entire list).
    """
    for spec in specs:
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            for n in expand_range_token(part):
                yield n

@click.group()
def main():
    """red CLI"""
    pass

@main.command("get-issues")
@click.argument("ids", nargs=-1, required=True)
@click.option("--show-first", type=int, default=20, help="Show first N examples")
def get_issues(ids, show_first):
    """
    Example usage:
      red get-issues 1..10
      red get-issues 1,3,5..8
      red get-issues 1 3 5..8
    """
    it = parse_ids(list(ids))
    # Example: stream processing (doesn't collect everything)
    count = 0
    shown = 0
    for n in it:
        count += 1
        if shown < show_first:
            click.echo(f"[{count}] fetching issue {n} ...")
            shown += 1
        # Replace the following with your real per-item work:
        # process_issue(n)
    click.echo(f"Total requested items: {count}", err=False)

if __name__ == "__main__":
    # make it runnable as `python -m red.cli` for local dev
    main(prog_name="red")
