from __future__ import annotations

import json
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from src import db, export
from src.config import resolve_db_path
from src.resolve import ResolutionError, resolve_book_id, resolve_concept_id

console = Console()


@click.group()
@click.option("--db", "db_path", default=None, help="Path to melvil.db.")
@click.pass_context
def cli(ctx: click.Context, db_path: str | None) -> None:
    path = resolve_db_path(db_path)
    conn = db.connect(path)
    db.initialize(conn)
    ctx.obj = {"conn": conn}
    ctx.call_on_close(conn.close)


@cli.command()
@click.option("--concept", "concept_name", default=None, help="Concept to inspect.")
@click.option("--book", "book_title", default=None, help="Book to inspect.")
@click.option("--related", "related_name", default=None, help="Show related concepts.")
@click.pass_context
def map(
    ctx: click.Context,
    concept_name: str | None,
    book_title: str | None,
    related_name: str | None,
) -> None:
    conn = ctx.obj["conn"]
    active = [bool(concept_name), bool(book_title), bool(related_name)]
    if sum(active) > 1:
        raise click.ClickException("Use only one of --concept, --book, or --related.")

    try:
        if concept_name:
            _map_concept(conn, concept_name)
            return
        if book_title:
            _map_book(conn, book_title)
            return
        if related_name:
            _map_related(conn, related_name)
            return
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    _map_overview(conn)


@cli.group()
def concept() -> None:
    pass


@concept.command("mentions")
@click.option("--book", "book_title", required=True, help="Book title or alias.")
@click.pass_context
def concept_mentions(ctx: click.Context, book_title: str) -> None:
    conn = ctx.obj["conn"]
    try:
        book_id, resolved = resolve_book_id(conn, book_title)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    rows = conn.execute(
        """
        SELECT c.name, ch.number, bc.location, bc.notes
        FROM book_concepts bc
        JOIN concepts c ON c.id = bc.concept_id
        LEFT JOIN chapters ch ON ch.id = bc.chapter_id
        WHERE bc.book_id = ?
        ORDER BY c.name
        """,
        (book_id,),
    ).fetchall()

    table = Table(title=f"Concept mentions for {resolved}")
    table.add_column("Concept")
    table.add_column("Chapter")
    table.add_column("Location")
    table.add_column("Notes")
    for row in rows:
        table.add_row(
            row["name"],
            row["number"] or "",
            row["location"] or "",
            row["notes"] or "",
        )
    console.print(table)


@cli.group(name="export")
def export_cmd() -> None:
    pass


@export_cmd.command("map")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["markdown", "json", "dot"], case_sensitive=False),
    default="markdown",
)
@click.pass_context
def export_map(ctx: click.Context, fmt: str) -> None:
    conn = ctx.obj["conn"]
    fmt_lower = fmt.lower()
    if fmt_lower == "markdown":
        click.echo(export.export_map_markdown(conn))
        return
    if fmt_lower == "json":
        data = export.export_map_json(conn)
        click.echo(json.dumps(data, indent=2, sort_keys=True))
        return
    if fmt_lower == "dot":
        click.echo(export.export_map_dot(conn))
        return
    raise click.ClickException(f"Unsupported format: {fmt}")


def _map_overview(conn: Any) -> None:
    counts = conn.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM concepts) AS concept_count,
            (SELECT COUNT(*) FROM books) AS book_count,
            (SELECT COUNT(*) FROM notes) AS note_count
        """
    ).fetchone()
    header = (
        f"Concept Map ({counts['concept_count']} concepts, "
        f"{counts['book_count']} books, {counts['note_count']} notes)"
    )
    table = Table(title=header)
    table.add_column("Concept")
    table.add_column("Books", justify="right")
    table.add_column("Notes", justify="right")
    table.add_column("Links", justify="right")
    rows = conn.execute(
        """
        SELECT c.id, c.name,
            (SELECT COUNT(DISTINCT bc.book_id) FROM book_concepts bc WHERE bc.concept_id = c.id) AS book_count,
            (SELECT COUNT(*) FROM note_concepts nc WHERE nc.concept_id = c.id) AS note_count,
            (SELECT COUNT(*) FROM concept_links cl WHERE cl.from_concept_id = c.id) AS link_count
        FROM concepts c
        ORDER BY c.name
        """
    ).fetchall()
    for row in rows:
        table.add_row(
            row["name"],
            str(row["book_count"]),
            str(row["note_count"]),
            str(row["link_count"]),
        )
    console.print(table)


def _map_concept(conn: Any, concept_name: str) -> None:
    concept_id, resolved = resolve_concept_id(conn, concept_name)
    rows = conn.execute(
        """
        SELECT b.title, b.depth, ch.number, bc.location, bc.notes
        FROM book_concepts bc
        JOIN books b ON b.id = bc.book_id
        LEFT JOIN chapters ch ON ch.id = bc.chapter_id
        WHERE bc.concept_id = ?
        ORDER BY b.title
        """,
        (concept_id,),
    ).fetchall()
    table = Table(title=f'Books covering "{resolved}"')
    table.add_column("Book")
    table.add_column("Depth")
    table.add_column("Chapter")
    table.add_column("Location")
    table.add_column("Notes")
    for row in rows:
        table.add_row(
            row["title"],
            row["depth"] or "",
            row["number"] or "",
            row["location"] or "",
            row["notes"] or "",
        )
    console.print(table)


def _map_book(conn: Any, book_title: str) -> None:
    book_id, resolved = resolve_book_id(conn, book_title)
    rows = conn.execute(
        """
        SELECT c.name, ch.number, bc.location, bc.notes
        FROM book_concepts bc
        JOIN concepts c ON c.id = bc.concept_id
        LEFT JOIN chapters ch ON ch.id = bc.chapter_id
        WHERE bc.book_id = ?
        GROUP BY c.id
        ORDER BY c.name
        """,
        (book_id,),
    ).fetchall()
    table = Table(title=f'Concepts in "{resolved}"')
    table.add_column("Concept")
    table.add_column("Chapter")
    table.add_column("Location")
    table.add_column("Notes")
    for row in rows:
        table.add_row(
            row["name"],
            row["number"] or "",
            row["location"] or "",
            row["notes"] or "",
        )
    console.print(table)


def _map_related(conn: Any, related_name: str) -> None:
    concept_id, resolved = resolve_concept_id(conn, related_name)
    rows = conn.execute(
        """
        SELECT c.name, cl.link_type
        FROM concept_links cl
        JOIN concepts c ON c.id = cl.to_concept_id
        WHERE cl.from_concept_id = ?
        ORDER BY c.name
        """,
        (concept_id,),
    ).fetchall()
    table = Table(title=f'Related concepts for "{resolved}"')
    table.add_column("Concept")
    table.add_column("Type")
    for row in rows:
        table.add_row(row["name"], row["link_type"])
    console.print(table)


if __name__ == "__main__":
    cli()
