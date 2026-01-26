from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from src import db, export, toc
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


def _format_authors(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(data, list):
        return ", ".join(str(item) for item in data)
    return str(data)


@cli.command()
@click.argument("title")
@click.option("--author", "authors", multiple=True, help="Author name (repeatable).")
@click.option("--year", type=int)
@click.option("--type", "book_type", default="book", show_default=True)
@click.option("--from-zotero", is_flag=True, help="Import from Zotero.")
@click.pass_context
def add(
    ctx: click.Context,
    title: str,
    authors: tuple[str, ...],
    year: int | None,
    book_type: str,
    from_zotero: bool,
) -> None:
    if from_zotero:
        raise click.ClickException("Zotero import not implemented yet.")

    conn = ctx.obj["conn"]
    authors_json = json.dumps(list(authors)) if authors else None
    try:
        conn.execute(
            """
            INSERT INTO books (title, authors, year, type)
            VALUES (?, ?, ?, ?)
            """,
            (title, authors_json, year, book_type),
        )
        conn.commit()
    except Exception as exc:  # pragma: no cover - sqlite constraint errors
        raise click.ClickException(str(exc)) from exc

    console.print(f"Added: {title}")


@cli.command()
@click.argument("title")
@click.pass_context
def show(ctx: click.Context, title: str) -> None:
    conn = ctx.obj["conn"]
    try:
        book_id, resolved = resolve_book_id(conn, title)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        raise click.ClickException(f'Book "{title}" not found.')

    table = Table(title=resolved)
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Author", _format_authors(book["authors"]))
    table.add_row("Year", str(book["year"]) if book["year"] else "")
    table.add_row("Depth", book["depth"] or "")
    if book["about"]:
        table.add_row("About", book["about"])
    console.print(table)

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
    if rows:
        concept_table = Table(title="Concepts")
        concept_table.add_column("Concept")
        concept_table.add_column("Chapter")
        concept_table.add_column("Location")
        concept_table.add_column("Notes")
        for row in rows:
            concept_table.add_row(
                row["name"],
                row["number"] or "",
                row["location"] or "",
                row["notes"] or "",
            )
        console.print(concept_table)


@cli.command(name="books")
@click.option("--depth", default=None, help="Filter by depth.")
@click.option("--concept", "concept_name", default=None, help="Filter by concept.")
@click.pass_context
def list_books(ctx: click.Context, depth: str | None, concept_name: str | None) -> None:
    if depth and concept_name:
        raise click.ClickException("Use only one of --depth or --concept.")

    conn = ctx.obj["conn"]
    params: list[object] = []
    query = "SELECT * FROM books"

    if depth:
        query += " WHERE depth = ?"
        params.append(depth)
    elif concept_name:
        try:
            concept_id, _ = resolve_concept_id(conn, concept_name)
        except ResolutionError as exc:
            raise click.ClickException(str(exc)) from exc
        query = (
            "SELECT b.* FROM books b JOIN book_concepts bc ON bc.book_id = b.id "
            "WHERE bc.concept_id = ? GROUP BY b.id"
        )
        params.append(concept_id)

    query += " ORDER BY title"
    rows = conn.execute(query, params).fetchall()

    table = Table(title="Books")
    table.add_column("Title", style="bold")
    table.add_column("Author")
    table.add_column("Year")
    table.add_column("Depth")
    for row in rows:
        table.add_row(
            row["title"],
            _format_authors(row["authors"]),
            str(row["year"]) if row["year"] else "",
            row["depth"] or "",
        )
    console.print(table)


@cli.command()
@click.argument("title")
@click.argument("depth")
@click.pass_context
def depth(ctx: click.Context, title: str, depth: str) -> None:
    conn = ctx.obj["conn"]
    try:
        book_id, resolved = resolve_book_id(conn, title)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    conn.execute("UPDATE books SET depth = ? WHERE id = ?", (depth, book_id))
    conn.commit()
    console.print(f"Updated depth: {resolved} -> {depth}")


@cli.command()
@click.argument("title")
@click.argument("about")
@click.pass_context
def about(ctx: click.Context, title: str, about: str) -> None:
    conn = ctx.obj["conn"]
    try:
        book_id, resolved = resolve_book_id(conn, title)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    conn.execute("UPDATE books SET about = ? WHERE id = ?", (about, book_id))
    conn.commit()
    console.print(f"Updated about: {resolved}")


@cli.command()
@click.argument("alias")
@click.argument("title")
@click.pass_context
def alias(ctx: click.Context, alias: str, title: str) -> None:
    conn = ctx.obj["conn"]
    try:
        book_id, resolved = resolve_book_id(conn, title)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    conn.execute(
        "INSERT INTO aliases (alias, book_id) VALUES (?, ?)",
        (alias, book_id),
    )
    conn.commit()
    console.print(f"Alias added: {alias} -> {resolved}")


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


LINK_TYPES = {"related", "prerequisite", "contradicts", "specializes", "generalizes"}


@cli.group(
    invoke_without_command=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
@click.option("--definition", default=None, help="Optional concept definition.")
@click.pass_context
def concept(ctx: click.Context, definition: str | None) -> None:
    if ctx.invoked_subcommand is not None:
        return
    if not ctx.args:
        raise click.ClickException("Provide a concept name.")
    name = " ".join(ctx.args).strip()
    if not name:
        raise click.ClickException("Provide a concept name.")

    conn = ctx.obj["conn"]
    row = conn.execute(
        "SELECT id FROM concepts WHERE name = ? COLLATE NOCASE",
        (name,),
    ).fetchone()
    if row:
        if definition:
            conn.execute(
                "UPDATE concepts SET definition = ? WHERE id = ?",
                (definition, row["id"]),
            )
            conn.commit()
            console.print(f'Updated concept: "{name}"')
        else:
            console.print(f'Concept already exists: "{name}"')
        return

    conn.execute(
        "INSERT INTO concepts (name, definition) VALUES (?, ?)",
        (name, definition),
    )
    conn.commit()
    console.print(f'Created concept: "{name}"')


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


@concept.command("show")
@click.argument("name")
@click.pass_context
def concept_show(ctx: click.Context, name: str) -> None:
    conn = ctx.obj["conn"]
    try:
        concept_id, resolved = resolve_concept_id(conn, name)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    concept_row = conn.execute(
        "SELECT * FROM concepts WHERE id = ?",
        (concept_id,),
    ).fetchone()
    if not concept_row:
        raise click.ClickException(f'Concept "{name}" not found.')

    aliases = []
    if concept_row["aliases"]:
        try:
            aliases = json.loads(concept_row["aliases"])
        except json.JSONDecodeError:
            aliases = []

    header = Table(title=resolved)
    header.add_column("Field", style="bold")
    header.add_column("Value")
    if concept_row["definition"]:
        header.add_row("Definition", concept_row["definition"])
    if aliases:
        header.add_row("Aliases", ", ".join(aliases))
    note_count = conn.execute(
        "SELECT COUNT(*) AS count FROM note_concepts WHERE concept_id = ?",
        (concept_id,),
    ).fetchone()
    header.add_row("Notes", str(note_count["count"] if note_count else 0))
    console.print(header)

    related = conn.execute(
        """
        SELECT c.name, cl.link_type, cl.notes
        FROM concept_links cl
        JOIN concepts c ON c.id = cl.to_concept_id
        WHERE cl.from_concept_id = ?
        ORDER BY c.name
        """,
        (concept_id,),
    ).fetchall()
    if related:
        rel_table = Table(title="Related concepts")
        rel_table.add_column("Concept")
        rel_table.add_column("Type")
        rel_table.add_column("Notes")
        for row in related:
            rel_table.add_row(row["name"], row["link_type"], row["notes"] or "")
        console.print(rel_table)

    incoming = conn.execute(
        """
        SELECT c.name, cl.link_type, cl.notes
        FROM concept_links cl
        JOIN concepts c ON c.id = cl.from_concept_id
        WHERE cl.to_concept_id = ?
        ORDER BY c.name
        """,
        (concept_id,),
    ).fetchall()
    if incoming:
        inc_table = Table(title="Incoming concepts")
        inc_table.add_column("Concept")
        inc_table.add_column("Type")
        inc_table.add_column("Notes")
        for row in incoming:
            inc_table.add_row(row["name"], row["link_type"], row["notes"] or "")
        console.print(inc_table)

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
    if rows:
        book_table = Table(title="Books")
        book_table.add_column("Book")
        book_table.add_column("Depth")
        book_table.add_column("Chapter")
        book_table.add_column("Location")
        book_table.add_column("Notes")
        for row in rows:
            book_table.add_row(
                row["title"],
                row["depth"] or "",
                row["number"] or "",
                row["location"] or "",
                row["notes"] or "",
            )
        console.print(book_table)


@concept.command("alias")
@click.argument("name")
@click.argument("aliases", nargs=-1)
@click.pass_context
def concept_alias(ctx: click.Context, name: str, aliases: tuple[str, ...]) -> None:
    if not aliases:
        raise click.ClickException("Provide at least one alias.")
    conn = ctx.obj["conn"]
    try:
        concept_id, resolved = resolve_concept_id(conn, name)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    row = conn.execute(
        "SELECT aliases FROM concepts WHERE id = ?",
        (concept_id,),
    ).fetchone()
    existing = []
    if row and row["aliases"]:
        try:
            existing = json.loads(row["aliases"])
        except json.JSONDecodeError:
            existing = []

    existing_lower = {alias.lower() for alias in existing}
    for alias in aliases:
        if alias.lower() not in existing_lower:
            existing.append(alias)
            existing_lower.add(alias.lower())

    conn.execute(
        "UPDATE concepts SET aliases = ? WHERE id = ?",
        (json.dumps(existing), concept_id),
    )
    conn.commit()
    console.print(f"Aliases updated for {resolved}")


@concept.command("link")
@click.argument("name")
@click.option("--book", "book_title", required=True, help="Book title or alias.")
@click.option("--chapter", "chapter_number", default=None, help="Chapter number.")
@click.option("--location", default=None, help="Location within the book.")
@click.option("--note", "notes", default=None, help="Notes about this link.")
@click.pass_context
def concept_link(
    ctx: click.Context,
    name: str,
    book_title: str,
    chapter_number: str | None,
    location: str | None,
    notes: str | None,
) -> None:
    conn = ctx.obj["conn"]
    try:
        concept_id, resolved = resolve_concept_id(conn, name)
        book_id, book_resolved = resolve_book_id(conn, book_title)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    chapter_id = None
    if chapter_number:
        row = conn.execute(
            """
            SELECT id FROM chapters
            WHERE book_id = ? AND number = ?
            """,
            (book_id, chapter_number),
        ).fetchone()
        if not row:
            raise click.ClickException(
                f'Chapter "{chapter_number}" not found for "{book_resolved}".'
            )
        chapter_id = row["id"]

    conn.execute(
        """
        INSERT INTO book_concepts (book_id, concept_id, chapter_id, location, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (book_id, concept_id, chapter_id, location, notes),
    )
    conn.commit()
    console.print(f'Linked "{resolved}" to "{book_resolved}"')


@concept.command("relate")
@click.argument("from_name")
@click.argument("to_name")
@click.option(
    "--type",
    "link_type",
    default="related",
    show_default=True,
    help="Link type.",
)
@click.option("--note", "notes", default=None, help="Relationship note.")
@click.pass_context
def concept_relate(
    ctx: click.Context,
    from_name: str,
    to_name: str,
    link_type: str,
    notes: str | None,
) -> None:
    if link_type not in LINK_TYPES:
        raise click.ClickException(
            f"Link type must be one of: {', '.join(sorted(LINK_TYPES))}."
        )
    conn = ctx.obj["conn"]
    try:
        from_id, from_resolved = resolve_concept_id(conn, from_name)
        to_id, to_resolved = resolve_concept_id(conn, to_name)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    if from_id == to_id:
        raise click.ClickException("Cannot relate a concept to itself.")

    conn.execute(
        """
        INSERT OR IGNORE INTO concept_links (from_concept_id, to_concept_id, link_type, notes)
        VALUES (?, ?, ?, ?)
        """,
        (from_id, to_id, link_type, notes),
    )
    conn.commit()
    console.print(f'Related "{from_resolved}" -> "{to_resolved}" ({link_type})')


@cli.command(name="concepts")
@click.option("--book", "book_title", default=None, help="Filter by book.")
@click.option("--orphan", "orphan", is_flag=True, help="Show unlinked concepts.")
@click.pass_context
def list_concepts(ctx: click.Context, book_title: str | None, orphan: bool) -> None:
    if book_title and orphan:
        raise click.ClickException("Use only one of --book or --orphan.")

    conn = ctx.obj["conn"]
    params: list[object] = []
    if book_title:
        try:
            book_id, resolved = resolve_book_id(conn, book_title)
        except ResolutionError as exc:
            raise click.ClickException(str(exc)) from exc
        query = (
            "SELECT c.name, COUNT(bc.id) AS mentions FROM concepts c "
            "JOIN book_concepts bc ON bc.concept_id = c.id "
            "WHERE bc.book_id = ? GROUP BY c.id ORDER BY c.name"
        )
        params.append(book_id)
        title = f'Concepts in "{resolved}"'
    elif orphan:
        query = """
            SELECT c.name, 0 AS mentions
            FROM concepts c
            WHERE NOT EXISTS (SELECT 1 FROM book_concepts bc WHERE bc.concept_id = c.id)
              AND NOT EXISTS (
                SELECT 1 FROM concept_links cl
                WHERE cl.from_concept_id = c.id OR cl.to_concept_id = c.id
              )
            ORDER BY c.name
        """
        title = "Orphan concepts"
    else:
        query = """
            SELECT c.name, COUNT(bc.id) AS mentions
            FROM concepts c
            LEFT JOIN book_concepts bc ON bc.concept_id = c.id
            GROUP BY c.id
            ORDER BY c.name
        """
        title = "Concepts"

    rows = conn.execute(query, params).fetchall()
    table = Table(title=title)
    table.add_column("Concept", style="bold")
    table.add_column("Mentions", justify="right")
    for row in rows:
        table.add_row(row["name"], str(row["mentions"]))
    console.print(table)


@cli.group(name="toc", invoke_without_command=True)
@click.argument("book_title", required=False)
@click.pass_context
def toc_cmd(ctx: click.Context, book_title: str | None) -> None:
    if ctx.invoked_subcommand or not book_title:
        return
    ctx.invoke(toc_show, book_title=book_title)


@toc_cmd.command("add")
@click.argument("book_title")
@click.option("--number", "number", default=None, help="Chapter number.")
@click.option("--title", "title", required=True, help="Chapter title.")
@click.option("--pages", "pages", default=None, help="Page range, e.g. 321-374.")
@click.pass_context
def toc_add(
    ctx: click.Context,
    book_title: str,
    number: str | None,
    title: str,
    pages: str | None,
) -> None:
    conn = ctx.obj["conn"]
    try:
        book_id, resolved = resolve_book_id(conn, book_title)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        page_start, page_end = toc.parse_pages(pages)
        chapter = toc.ChapterInput(
            number=number,
            title=title,
            parent_id=None,
            position=None,
            page_start=page_start,
            page_end=page_end,
        )
        toc.add_chapter(conn, book_id, chapter)
        conn.commit()
    except toc.TocError as exc:
        raise click.ClickException(str(exc)) from exc

    console.print(f'Added chapter "{title}" to {resolved}.')


@toc_cmd.command("import")
@click.argument("book_title")
@click.option("--from-pdf", "pdf_path", required=True, type=click.Path(path_type=Path))
@click.pass_context
def toc_import(ctx: click.Context, book_title: str, pdf_path: Path) -> None:
    conn = ctx.obj["conn"]
    try:
        book_id, resolved = resolve_book_id(conn, book_title)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        inserted = toc.import_from_pdf(conn, book_id, pdf_path)
        conn.commit()
    except toc.TocError as exc:
        raise click.ClickException(str(exc)) from exc

    console.print(f"Imported {inserted} chapters into {resolved}.")


@toc_cmd.command("summarize")
@click.argument("book_title")
@click.option("--chapter", "chapter_ref", required=True, help="Chapter number or id.")
@click.argument("summary")
@click.pass_context
def toc_summarize(
    ctx: click.Context, book_title: str, chapter_ref: str, summary: str
) -> None:
    conn = ctx.obj["conn"]
    try:
        book_id, resolved = resolve_book_id(conn, book_title)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        chapter_id = toc.resolve_chapter_id(conn, book_id, chapter_ref)
        toc.update_summary(conn, chapter_id, summary)
        conn.commit()
    except toc.TocError as exc:
        raise click.ClickException(str(exc)) from exc

    console.print(f'Updated chapter {chapter_ref} summary for {resolved}.')


@toc_cmd.command("show")
@click.argument("book_title")
@click.pass_context
def toc_show(ctx: click.Context, book_title: str) -> None:
    conn = ctx.obj["conn"]
    try:
        book_id, resolved = resolve_book_id(conn, book_title)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    rows = conn.execute(
        """
        SELECT number, title, page_start, page_end, summary
        FROM chapters
        WHERE book_id = ?
        ORDER BY position, id
        """,
        (book_id,),
    ).fetchall()

    table = Table(title=f"TOC for {resolved}")
    table.add_column("Number")
    table.add_column("Title")
    table.add_column("Pages")
    table.add_column("Summary")
    for row in rows:
        if row["page_start"] and row["page_end"]:
            pages = f"{row['page_start']}-{row['page_end']}"
        elif row["page_start"]:
            pages = str(row["page_start"])
        else:
            pages = ""
        table.add_row(
            row["number"] or "",
            row["title"],
            pages,
            row["summary"] or "",
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
