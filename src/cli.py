from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from src import db, export, notes as notes_lib, toc, zotero
from src.config import resolve_db_path
from src.resolve import ResolutionError, resolve_book_id, resolve_concept_id

console = Console()


class FallbackGroup(click.Group):
    """Allow treating unknown subcommands as extra args for invoke_without_command."""

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        if not args:
            return None, None, []
        cmd_name = click.utils.make_str(args[0])
        original_cmd_name = cmd_name
        cmd = self.get_command(ctx, cmd_name)
        if cmd is None and ctx.token_normalize_func is not None:
            cmd_name = ctx.token_normalize_func(cmd_name)
            cmd = self.get_command(ctx, cmd_name)
        if cmd is None:
            return None, None, args
        return original_cmd_name, cmd, args[1:]

    def invoke(self, ctx: click.Context) -> Any:
        def _process_result(value: Any) -> Any:
            if self._result_callback is not None:
                value = ctx.invoke(self._result_callback, value, **ctx.params)
            return value

        if not ctx._protected_args:
            if self.invoke_without_command:
                with ctx:
                    rv = click.Command.invoke(self, ctx)
                    return _process_result([] if self.chain else rv)
            ctx.fail("Missing command.")

        args = [*ctx._protected_args, *ctx.args]
        ctx.args = []
        ctx._protected_args = []

        if not self.chain:
            with ctx:
                cmd_name, cmd, args = self.resolve_command(ctx, args)
                if cmd is None:
                    ctx.invoked_subcommand = None
                    ctx.args = args
                    rv = click.Command.invoke(self, ctx)
                    return _process_result(rv)
                ctx.invoked_subcommand = cmd_name
                click.Command.invoke(self, ctx)
                sub_ctx = cmd.make_context(cmd_name, args, parent=ctx)
                with sub_ctx:
                    return _process_result(sub_ctx.command.invoke(sub_ctx))

        return super().invoke(ctx)


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


def _render_book_concepts(title: str, rows: list[sqlite3.Row]) -> None:
    table = Table(title=title, expand=True)
    table.add_column("Concept")
    table.add_column("Chapter")
    table.add_column("Location")
    table.add_column("Notes")
    last_concept = None
    for row in rows:
        concept_name = row["name"]
        display = concept_name if concept_name != last_concept else ""
        table.add_row(
            display,
            row["number"] or "",
            row["location"] or "",
            row["notes"] or "",
        )
        last_concept = concept_name
    console.print(table)


@cli.command()
@click.argument("title")
@click.option("--author", "authors", multiple=True, help="Author name (repeatable).")
@click.option("--year", type=int)
@click.option(
    "--type",
    "book_type",
    type=click.Choice(["book", "paper", "article"], case_sensitive=False),
    default="book",
    show_default=True,
)
@click.option("--from-zotero", is_flag=True, help="Import from Zotero.")
@click.option(
    "--zotero-db",
    "zotero_db",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to zotero.sqlite (optional).",
)
@click.pass_context
def add(
    ctx: click.Context,
    title: str,
    authors: tuple[str, ...],
    year: int | None,
    book_type: str,
    from_zotero: bool,
    zotero_db: Path | None,
) -> None:
    if from_zotero:
        try:
            book = zotero.create_book_from_zotero(
                ctx.obj["conn"],
                title=title,
                zotero_db_path=zotero_db,
            )
        except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
            raise click.ClickException(str(exc)) from exc
        console.print(f"Added: {book['title']}")
        return

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

    console.print(resolved)
    table = Table(title=resolved, expand=True)
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
        SELECT c.name, ch.number, bc.location, bc.notes, bc.id AS mention_id
        FROM book_concepts bc
        JOIN concepts c ON c.id = bc.concept_id
        LEFT JOIN chapters ch ON ch.id = bc.chapter_id
        WHERE bc.book_id = ?
        ORDER BY
            c.name,
            (ch.position IS NULL AND ch.page_start IS NULL),
            COALESCE(ch.position, ch.page_start),
            bc.location,
            mention_id
        """,
        (book_id,),
    ).fetchall()
    if rows:
        _render_book_concepts("Concepts", rows)


@cli.command(name="books")
@click.option("--depth", default=None, help="Filter by depth.")
@click.option("--concept", "concept_name", default=None, help="Filter by concept.")
@click.pass_context
def list_books(ctx: click.Context, depth: str | None, concept_name: str | None) -> None:
    if depth and concept_name:
        raise click.ClickException("Use only one of --depth or --concept.")
    if depth and depth not in DEPTH_LEVELS:
        raise click.ClickException(
            f"Depth must be one of: {', '.join(sorted(DEPTH_LEVELS))}."
        )

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
    table.add_column("Title", style="bold", no_wrap=True)
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
    if depth not in DEPTH_LEVELS:
        raise click.ClickException(
            f"Depth must be one of: {', '.join(sorted(DEPTH_LEVELS))}."
        )
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

    try:
        conn.execute(
            "INSERT INTO aliases (alias, book_id) VALUES (?, ?)",
            (alias, book_id),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise click.ClickException(f'Alias "{alias}" is already in use.') from exc
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


@cli.command()
@click.option("--focus", "focus_name", default=None, help="Focus on a concept.")
@click.option("--book", "book_title", default=None, help="Focus on a book.")
@click.option(
    "--related",
    "include_related",
    is_flag=True,
    help="Include related concepts when using --book.",
)
@click.pass_context
def viz(
    ctx: click.Context,
    focus_name: str | None,
    book_title: str | None,
    include_related: bool,
) -> None:
    conn = ctx.obj["conn"]
    if focus_name and book_title:
        raise click.ClickException("Use only one of --focus or --book.")
    if include_related and not book_title:
        raise click.ClickException("--related requires --book.")
    try:
        from src import viz as viz_module
    except ImportError as exc:
        raise click.ClickException(
            "Textual is required for visualization. Install it with `pip install textual`."
        ) from exc

    try:
        viz_module.run_viz(
            conn,
            focus=focus_name,
            book=book_title,
            include_related=include_related,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


DEPTH_LEVELS = {"listed", "mapped", "reading", "read", "deep"}
NOTE_TYPES = {"standard", "relation"}
LINK_TYPES = {"related", "prerequisite", "contradicts", "specializes", "generalizes"}


@cli.group(
    invoke_without_command=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    cls=FallbackGroup,
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
        SELECT c.name, ch.number, bc.location, bc.notes, bc.id AS mention_id
        FROM book_concepts bc
        JOIN concepts c ON c.id = bc.concept_id
        LEFT JOIN chapters ch ON ch.id = bc.chapter_id
        WHERE bc.book_id = ?
        ORDER BY
            c.name,
            (ch.position IS NULL AND ch.page_start IS NULL),
            COALESCE(ch.position, ch.page_start),
            bc.location,
            mention_id
        """,
        (book_id,),
    ).fetchall()

    _render_book_concepts(f"Concept mentions for {resolved}", rows)


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
        ORDER BY
            b.title,
            (ch.position IS NULL AND ch.page_start IS NULL),
            COALESCE(ch.position, ch.page_start),
            bc.location
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


@cli.group(
    invoke_without_command=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    cls=FallbackGroup,
)
@click.option("--book", "book_title", default=None, help="Book title or alias.")
@click.option("--chapter", "chapter_ref", default=None, help="Chapter number or id.")
@click.option("--concept", "concepts", multiple=True, help="Link to a concept.")
@click.option(
    "--type",
    "note_type",
    type=click.Choice(sorted(NOTE_TYPES), case_sensitive=False),
    default="standard",
    show_default=True,
)
@click.option("--location", "source_location", default=None, help="Source location.")
@click.option("--title", "note_title", default=None, help="Optional note title.")
@click.pass_context
def note(
    ctx: click.Context,
    book_title: str | None,
    chapter_ref: str | None,
    concepts: tuple[str, ...],
    note_type: str,
    source_location: str | None,
    note_title: str | None,
) -> None:
    if ctx.invoked_subcommand is not None:
        return

    text = " ".join(ctx.args).strip() if ctx.args else None
    if not text:
        text = click.edit("")
        if text is None:
            return
        text = text.strip()

    if not text:
        raise click.ClickException("Note text is required.")

    wikilink_names = notes_lib.parse_wikilinks(text)

    conn = ctx.obj["conn"]
    explicit_ids: list[int] = []
    for concept_name in concepts:
        try:
            explicit_ids.append(notes_lib.resolve_or_create_concept_id(conn, concept_name))
        except ResolutionError as exc:
            raise click.ClickException(str(exc)) from exc

    wikilink_ids = set()
    for concept_name in wikilink_names:
        try:
            wikilink_ids.add(notes_lib.resolve_or_create_concept_id(conn, concept_name))
        except ResolutionError as exc:
            raise click.ClickException(str(exc)) from exc

    if note_type == "standard" and len(set(explicit_ids) | wikilink_ids) > 1:
        raise click.ClickException(
            "Standard notes can link to at most one concept. Use --type relation."
        )

    book_id = None
    chapter_id = None
    if book_title:
        try:
            book_id, _ = resolve_book_id(conn, book_title)
        except ResolutionError as exc:
            raise click.ClickException(str(exc)) from exc
    if chapter_ref:
        if not book_id:
            raise click.ClickException("--chapter requires --book.")
        try:
            chapter_id = toc.resolve_chapter_id(conn, book_id, chapter_ref)
        except toc.TocError as exc:
            raise click.ClickException(str(exc)) from exc

    cursor = conn.execute(
        """
        INSERT INTO notes (
            title, body, book_id, chapter_id, note_type, source_location, is_quote
        ) VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
        (
            note_title,
            text,
            book_id,
            chapter_id,
            note_type,
            source_location,
        ),
    )
    note_id = int(cursor.lastrowid)

    notes_lib.insert_note_concepts(
        conn,
        note_id=note_id,
        concept_ids=explicit_ids,
        source="explicit",
    )

    notes_lib.sync_wikilink_concepts(
        conn,
        note_id=note_id,
        wikilink_names=wikilink_names,
        explicit_ids=set(explicit_ids),
    )
    conn.commit()
    console.print(f"Added note #{note_id}.")


@note.command("edit")
@click.argument("note_id", type=int)
@click.pass_context
def note_edit(ctx: click.Context, note_id: int) -> None:
    conn = ctx.obj["conn"]
    row = conn.execute(
        "SELECT body, note_type FROM notes WHERE id = ?",
        (note_id,),
    ).fetchone()
    if not row:
        raise click.ClickException(f"Note {note_id} not found.")

    updated = click.edit(row["body"])
    if updated is None:
        return
    updated = updated.strip()
    if not updated:
        raise click.ClickException("Note body cannot be empty.")

    wikilink_names = notes_lib.parse_wikilinks(updated)
    explicit_ids = {
        row["concept_id"]
        for row in conn.execute(
            """
            SELECT concept_id
            FROM note_concepts
            WHERE note_id = ? AND source = 'explicit'
            """,
            (note_id,),
        ).fetchall()
    }

    wikilink_ids = set()
    for concept_name in wikilink_names:
        try:
            wikilink_ids.add(notes_lib.resolve_or_create_concept_id(conn, concept_name))
        except ResolutionError as exc:
            raise click.ClickException(str(exc)) from exc

    if row["note_type"] == "standard" and len(explicit_ids | wikilink_ids) > 1:
        raise click.ClickException(
            "Standard notes can link to at most one concept. Use --type relation."
        )

    conn.execute(
        "UPDATE notes SET body = ? WHERE id = ?",
        (updated, note_id),
    )

    notes_lib.sync_wikilink_concepts(
        conn,
        note_id=note_id,
        wikilink_names=wikilink_names,
        explicit_ids=set(explicit_ids),
    )
    conn.commit()
    console.print(f"Updated note #{note_id}.")


@note.command("link")
@click.argument("from_note", type=int)
@click.argument("to_note", type=int)
@click.pass_context
def note_link(ctx: click.Context, from_note: int, to_note: int) -> None:
    conn = ctx.obj["conn"]
    if from_note == to_note:
        raise click.ClickException("Cannot link a note to itself.")
    conn.execute(
        """
        INSERT OR IGNORE INTO note_links (from_note_id, to_note_id)
        VALUES (?, ?)
        """,
        (from_note, to_note),
    )
    conn.commit()
    console.print(f"Linked note #{from_note} -> #{to_note}.")


@cli.command()
@click.argument("text", required=False)
@click.option("--book", "book_title", default=None, help="Book title or alias.")
@click.option("--location", "source_location", required=True, help="Source location.")
@click.option("--concept", "concepts", multiple=True, help="Link to a concept.")
@click.pass_context
def quote(
    ctx: click.Context,
    text: str | None,
    book_title: str | None,
    source_location: str,
    concepts: tuple[str, ...],
) -> None:
    body = text or click.edit("")
    if body is None:
        return
    body = body.strip()
    if not body:
        raise click.ClickException("Quote text is required.")

    conn = ctx.obj["conn"]
    wikilink_names = notes_lib.parse_wikilinks(body)

    explicit_ids: list[int] = []
    for concept_name in concepts:
        try:
            explicit_ids.append(notes_lib.resolve_or_create_concept_id(conn, concept_name))
        except ResolutionError as exc:
            raise click.ClickException(str(exc)) from exc

    wikilink_ids = set()
    for concept_name in wikilink_names:
        try:
            wikilink_ids.add(notes_lib.resolve_or_create_concept_id(conn, concept_name))
        except ResolutionError as exc:
            raise click.ClickException(str(exc)) from exc

    if len(set(explicit_ids) | wikilink_ids) > 1:
        raise click.ClickException(
            "Standard notes can link to at most one concept. Use --type relation."
        )

    book_id = None
    if book_title:
        try:
            book_id, _ = resolve_book_id(conn, book_title)
        except ResolutionError as exc:
            raise click.ClickException(str(exc)) from exc

    cursor = conn.execute(
        """
        INSERT INTO notes (
            title, body, book_id, chapter_id, note_type, source_location, is_quote
        ) VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
        (None, body, book_id, None, "standard", source_location),
    )
    note_id = int(cursor.lastrowid)

    notes_lib.insert_note_concepts(
        conn,
        note_id=note_id,
        concept_ids=explicit_ids,
        source="explicit",
    )
    notes_lib.sync_wikilink_concepts(
        conn,
        note_id=note_id,
        wikilink_names=wikilink_names,
        explicit_ids=set(explicit_ids),
    )
    conn.commit()
    console.print(f"Added quote #{note_id}.")


@cli.group(name="notes", invoke_without_command=True)
@click.option("--concept", "concept_name", default=None, help="Filter by concept.")
@click.option("--book", "book_title", default=None, help="Filter by book.")
@click.option("--draft", "draft_only", is_flag=True, help="Show unlinked notes.")
@click.option(
    "--type",
    "note_type",
    type=click.Choice(sorted(NOTE_TYPES), case_sensitive=False),
    default=None,
    help="Filter by note type.",
)
@click.pass_context
def notes_cmd(
    ctx: click.Context,
    concept_name: str | None,
    book_title: str | None,
    draft_only: bool,
    note_type: str | None,
) -> None:
    if ctx.invoked_subcommand is not None:
        return

    conn = ctx.obj["conn"]
    params: list[object] = []
    joins: list[str] = []
    where: list[str] = []

    if concept_name:
        try:
            concept_id, _ = resolve_concept_id(conn, concept_name)
        except ResolutionError as exc:
            raise click.ClickException(str(exc)) from exc
        joins.append("JOIN note_concepts nc ON nc.note_id = n.id")
        where.append("nc.concept_id = ?")
        params.append(concept_id)

    if book_title:
        try:
            book_id, _ = resolve_book_id(conn, book_title)
        except ResolutionError as exc:
            raise click.ClickException(str(exc)) from exc
        where.append("n.book_id = ?")
        params.append(book_id)

    if draft_only:
        where.append(
            "NOT EXISTS (SELECT 1 FROM note_concepts nc2 WHERE nc2.note_id = n.id)"
        )

    if note_type:
        where.append("n.note_type = ?")
        params.append(note_type)

    query = (
        "SELECT n.id, n.title, n.body, n.note_type, n.source_location, b.title AS book_title "
        "FROM notes n "
        "LEFT JOIN books b ON b.id = n.book_id "
    )
    if joins:
        query += " " + " ".join(joins)
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " GROUP BY n.id ORDER BY n.id DESC"

    rows = conn.execute(query, params).fetchall()
    table = Table(title="Notes")
    table.add_column("ID", justify="right")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Book")
    for row in rows:
        title = row["title"] or row["body"].strip().replace("\n", " ")
        if len(title) > 80:
            title = title[:77].rstrip() + "..."
        table.add_row(
            str(row["id"]),
            title,
            row["note_type"] or "",
            row["book_title"] or "",
        )
    console.print(table)


@notes_cmd.command("search")
@click.argument("query")
@click.pass_context
def notes_search(ctx: click.Context, query: str) -> None:
    conn = ctx.obj["conn"]
    try:
        rows = conn.execute(
            """
            SELECT n.id, n.title, n.body, n.note_type, b.title AS book_title
            FROM notes_fts f
            JOIN notes n ON n.id = f.rowid
            LEFT JOIN books b ON b.id = n.book_id
            WHERE notes_fts MATCH ?
            ORDER BY bm25(notes_fts)
            """,
            (query,),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        raise click.ClickException(
            "Invalid FTS query. Use terms, quotes for phrases, and operators like "
            'AND/OR/NOT. Example: "consensus" OR linear*.'
        ) from exc

    table = Table(title=f'Search results for "{query}"')
    table.add_column("ID", justify="right")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Book")
    for row in rows:
        title = row["title"] or row["body"].strip().replace("\n", " ")
        if len(title) > 80:
            title = title[:77].rstrip() + "..."
        table.add_row(
            str(row["id"]),
            title,
            row["note_type"] or "",
            row["book_title"] or "",
        )
    console.print(table)


@cli.group(name="toc", invoke_without_command=True, cls=FallbackGroup)
@click.pass_context
def toc_cmd(ctx: click.Context) -> None:
    if ctx.invoked_subcommand or not ctx.args:
        return
    book_title = " ".join(ctx.args).strip()
    if not book_title:
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
        ORDER BY
            (position IS NULL AND page_start IS NULL),
            COALESCE(position, page_start),
            id
        """,
        (book_id,),
    ).fetchall()

    table = Table(title=f"TOC for {resolved}", expand=True)
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
    type=click.Choice(["markdown", "json", "dot", "obsidian"], case_sensitive=False),
    default="markdown",
)
@click.option(
    "--output",
    "output_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for obsidian export.",
)
@click.pass_context
def export_map(ctx: click.Context, fmt: str, output_dir: Path | None) -> None:
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
    if fmt_lower == "obsidian":
        target = output_dir or export.obsidian_default_dir()
        try:
            output_path = export.export_map_obsidian(conn, target)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        console.print(f"Obsidian vault written to {output_path}.")
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
        ORDER BY
            b.title,
            (ch.position IS NULL AND ch.page_start IS NULL),
            COALESCE(ch.position, ch.page_start),
            bc.location
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
        SELECT c.name, ch.number, bc.location, bc.notes, bc.id AS mention_id
        FROM book_concepts bc
        JOIN concepts c ON c.id = bc.concept_id
        LEFT JOIN chapters ch ON ch.id = bc.chapter_id
        WHERE bc.book_id = ?
        ORDER BY
            c.name,
            (ch.position IS NULL AND ch.page_start IS NULL),
            COALESCE(ch.position, ch.page_start),
            bc.location,
            mention_id
        """,
        (book_id,),
    ).fetchall()
    _render_book_concepts(f'Concepts in "{resolved}"', rows)


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
