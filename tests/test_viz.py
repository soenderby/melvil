from __future__ import annotations

import sys
import types


class _DummyWidget:
    def __init__(self, *args, **kwargs):
        pass


class _DummyApp:
    def __init__(self, *args, **kwargs):
        pass


class _DummyStatic:
    def __init__(self, *args, **kwargs):
        pass


textual_module = types.ModuleType("textual")
textual_app = types.ModuleType("textual.app")
textual_widgets = types.ModuleType("textual.widgets")
textual_widget = types.ModuleType("textual.widget")

textual_app.App = _DummyApp
textual_app.ComposeResult = object
textual_widgets.Footer = object
textual_widgets.Header = object
textual_widgets.Static = _DummyStatic
textual_widget.Widget = _DummyWidget

sys.modules.setdefault("textual", textual_module)
sys.modules.setdefault("textual.app", textual_app)
sys.modules.setdefault("textual.widgets", textual_widgets)
sys.modules.setdefault("textual.widget", textual_widget)

from src.viz import Node, build_graph, compute_layout, draw_line, scale_positions


def _seed_graph_data(conn):
    book_id = conn.execute(
        "INSERT INTO books (title, depth) VALUES (?, ?)",
        ("Book One", "mapped"),
    ).lastrowid
    concept_alpha = conn.execute(
        "INSERT INTO concepts (name) VALUES (?)", ("Alpha",)
    ).lastrowid
    concept_beta = conn.execute(
        "INSERT INTO concepts (name) VALUES (?)", ("Beta",)
    ).lastrowid
    conn.execute(
        "INSERT INTO concept_links (from_concept_id, to_concept_id, link_type) VALUES (?, ?, ?)",
        (concept_alpha, concept_beta, "related"),
    )
    conn.execute(
        "INSERT INTO book_concepts (book_id, concept_id) VALUES (?, ?)",
        (book_id, concept_alpha),
    )
    conn.commit()
    return int(book_id), int(concept_alpha), int(concept_beta)


def test_build_graph_focus_and_degrees(db_conn):
    book_id, concept_alpha, concept_beta = _seed_graph_data(db_conn)

    graph = build_graph(db_conn)
    node_ids = {node.node_id for node in graph.nodes}
    assert node_ids == {f"b{book_id}", f"c{concept_alpha}", f"c{concept_beta}"}

    degrees = {node.node_id: node.degree for node in graph.nodes}
    assert degrees[f"c{concept_alpha}"] == 2
    assert degrees[f"c{concept_beta}"] == 1
    assert degrees[f"b{book_id}"] == 1

    focus_graph = build_graph(db_conn, focus_id=f"c{concept_beta}")
    focus_ids = {node.node_id for node in focus_graph.nodes}
    assert focus_ids == {f"c{concept_alpha}", f"c{concept_beta}"}
    assert all(f"c{concept_beta}" in edge for edge in focus_graph.edges)


def test_compute_layout_deterministic():
    nodes = [
        Node(node_id="a", label="A", kind="concept", degree=1, depth=None),
        Node(node_id="b", label="B", kind="concept", degree=1, depth=None),
    ]
    edges = [("a", "b")]

    first = compute_layout(nodes, edges)
    second = compute_layout(nodes, edges)

    assert first == second


def test_scale_positions_bounds():
    positions = {"a": (-0.2, 1.4), "b": (0.5, 0.5)}
    scaled = scale_positions(positions, width=10, height=5)

    assert scaled["a"] == (0, 4)
    assert scaled["b"] == (4, 2)


def test_draw_line_marks_grid():
    grid = [[(" ", None) for _ in range(5)] for _ in range(5)]

    draw_line(grid, (0, 0), (4, 4))

    assert grid[0][0][0] == "."
    assert grid[4][4][0] == "."
    assert any(cell[0] == "." for row in grid for cell in row)
