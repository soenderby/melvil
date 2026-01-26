from __future__ import annotations

import math
import random
import sqlite3
from dataclasses import dataclass
from typing import Iterable

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static
from textual.widget import Widget
from rich.text import Text

from .resolve import ResolutionError, resolve_concept_id


@dataclass(frozen=True)
class Node:
    node_id: str
    label: str
    kind: str
    degree: int
    depth: str | None


@dataclass(frozen=True)
class Graph:
    nodes: list[Node]
    edges: list[tuple[str, str]]


DEPTH_COLORS = {
    "listed": "grey50",
    "mapped": "cyan",
    "reading": "yellow",
    "read": "green",
    "deep": "magenta",
}


def run_viz(conn: sqlite3.Connection, focus: str | None = None) -> None:
    full_graph = build_graph(conn)
    focus_graph = None
    focus_id = None
    if focus:
        try:
            concept_id, resolved = resolve_concept_id(conn, focus)
        except ResolutionError as exc:
            raise ValueError(str(exc)) from exc
        focus_id = f"c{concept_id}"
        focus_graph = build_graph(conn, focus_id=focus_id)
        app = GraphApp(full_graph, focus_graph, focus_id, resolved)
    else:
        app = GraphApp(full_graph, None, None, None)
    app.run()


class GraphApp(App):
    BINDINGS = [
        ("left", "prev", "Prev node"),
        ("right", "next", "Next node"),
        ("up", "prev", "Prev node"),
        ("down", "next", "Next node"),
        ("enter", "toggle", "Toggle focus"),
    ]

    def __init__(
        self,
        full_graph: Graph,
        focus_graph: Graph | None,
        focus_id: str | None,
        focus_label: str | None,
    ) -> None:
        super().__init__()
        self.full_graph = full_graph
        self.focus_graph = focus_graph
        self.focus_id = focus_id
        self.focus_label = focus_label
        self.focus_mode = bool(focus_graph)
        self.node_ids = [node.node_id for node in self.active_graph().nodes]
        self.cursor = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(id="info")
        yield GraphWidget(self.active_graph())
        yield Footer()

    def on_mount(self) -> None:
        self._update_info()

    def active_graph(self) -> Graph:
        if self.focus_mode and self.focus_graph is not None:
            return self.focus_graph
        return self.full_graph

    def action_prev(self) -> None:
        if not self.node_ids:
            return
        self.cursor = (self.cursor - 1) % len(self.node_ids)
        self._update_focus()

    def action_next(self) -> None:
        if not self.node_ids:
            return
        self.cursor = (self.cursor + 1) % len(self.node_ids)
        self._update_focus()

    def action_toggle(self) -> None:
        if self.focus_graph is None:
            return
        self.focus_mode = not self.focus_mode
        self.node_ids = [node.node_id for node in self.active_graph().nodes]
        self.cursor = 0
        self._update_focus(reset=True)

    def _update_focus(self, reset: bool = False) -> None:
        node_id = None
        if self.node_ids:
            node_id = self.node_ids[self.cursor]
        graph_widget = self.query_one(GraphWidget)
        graph_widget.set_graph(self.active_graph())
        graph_widget.set_focus(node_id)
        if reset:
            graph_widget.relayout()
        self._update_info(node_id)

    def _update_info(self, node_id: str | None = None) -> None:
        info = self.query_one("#info", Static)
        label = None
        if node_id:
            label = next(
                (node.label for node in self.active_graph().nodes if node.node_id == node_id),
                None,
            )
        if label:
            info.update(f"Focus: {label}")
        elif self.focus_label and self.focus_mode:
            info.update(f"Focus: {self.focus_label} (neighbors)")
        else:
            info.update("Focus: none")


class GraphWidget(Widget):
    def __init__(self, graph: Graph) -> None:
        super().__init__()
        self.graph = graph
        self.focus_id: str | None = None
        self.positions: dict[str, tuple[float, float]] = {}

    def on_mount(self) -> None:
        self.relayout()

    def on_resize(self) -> None:
        self.relayout()

    def relayout(self) -> None:
        self.positions = compute_layout(self.graph.nodes, self.graph.edges)
        self.refresh()

    def set_graph(self, graph: Graph) -> None:
        self.graph = graph

    def set_focus(self, node_id: str | None) -> None:
        self.focus_id = node_id
        self.refresh()

    def render(self) -> Text:
        width = max(10, self.size.width)
        height = max(8, self.size.height)
        positions = scale_positions(self.positions, width, height)
        grid: list[list[tuple[str, str | None]]] = [
            [(" ", None) for _ in range(width)] for _ in range(height)
        ]

        for a, b in self.graph.edges:
            if a not in positions or b not in positions:
                continue
            draw_line(grid, positions[a], positions[b])

        for node in self.graph.nodes:
            pos = positions.get(node.node_id)
            if not pos:
                continue
            x, y = pos
            char = "@" if node.node_id == self.focus_id else "o"
            style = node_style(node)
            grid[y][x] = (char, style)

        text = Text()
        for row in grid:
            line = Text()
            for char, style in row:
                line.append(char, style=style)
            text.append_text(line)
            text.append("\n")
        return text


def node_style(node: Node) -> str:
    if node.kind == "book":
        return DEPTH_COLORS.get(node.depth or "listed", "grey50")
    if node.degree >= 6:
        return "red"
    if node.degree >= 3:
        return "orange3"
    if node.degree >= 1:
        return "green"
    return "grey50"


def build_graph(conn: sqlite3.Connection, focus_id: str | None = None) -> Graph:
    nodes: dict[str, Node] = {}
    edges: set[tuple[str, str]] = set()

    concept_rows = conn.execute("SELECT id, name FROM concepts").fetchall()
    book_rows = conn.execute("SELECT id, title, depth FROM books").fetchall()

    for row in concept_rows:
        node_id = f"c{row['id']}"
        nodes[node_id] = Node(node_id=node_id, label=row["name"], kind="concept", degree=0, depth=None)

    for row in book_rows:
        node_id = f"b{row['id']}"
        nodes[node_id] = Node(node_id=node_id, label=row["title"], kind="book", degree=0, depth=row["depth"])

    link_rows = conn.execute(
        "SELECT from_concept_id, to_concept_id FROM concept_links"
    ).fetchall()
    for row in link_rows:
        a = f"c{row['from_concept_id']}"
        b = f"c{row['to_concept_id']}"
        edges.add(tuple(sorted((a, b))))

    book_concepts = conn.execute(
        "SELECT book_id, concept_id FROM book_concepts"
    ).fetchall()
    for row in book_concepts:
        a = f"b{row['book_id']}"
        b = f"c{row['concept_id']}"
        edges.add(tuple(sorted((a, b))))

    filtered_edges = list(edges)
    if focus_id:
        filtered_edges = [edge for edge in edges if focus_id in edge]

    connected = {node_id for edge in filtered_edges for node_id in edge}
    if focus_id:
        connected.add(focus_id)
    if connected:
        nodes = {node_id: node for node_id, node in nodes.items() if node_id in connected}

    degree_counts: dict[str, int] = {node_id: 0 for node_id in nodes}
    for a, b in filtered_edges:
        if a in degree_counts:
            degree_counts[a] += 1
        if b in degree_counts:
            degree_counts[b] += 1

    nodes = {
        node_id: Node(
            node_id=node.node_id,
            label=node.label,
            kind=node.kind,
            degree=degree_counts.get(node_id, 0),
            depth=node.depth,
        )
        for node_id, node in nodes.items()
    }

    return Graph(nodes=list(nodes.values()), edges=filtered_edges)


def compute_layout(nodes: Iterable[Node], edges: Iterable[tuple[str, str]]) -> dict[str, tuple[float, float]]:
    nodes = list(nodes)
    if not nodes:
        return {}

    rnd = random.Random(42)
    positions = {node.node_id: (rnd.random(), rnd.random()) for node in nodes}
    velocities = {node.node_id: (0.0, 0.0) for node in nodes}
    node_ids = [node.node_id for node in nodes]
    edge_list = list(edges)

    repulsion = 0.02
    spring = 0.08
    damping = 0.85

    for _ in range(200):
        forces = {node_id: (0.0, 0.0) for node_id in node_ids}

        for i, a in enumerate(node_ids):
            ax, ay = positions[a]
            for b in node_ids[i + 1 :]:
                bx, by = positions[b]
                dx = ax - bx
                dy = ay - by
                dist = math.sqrt(dx * dx + dy * dy) + 0.01
                force = repulsion / (dist * dist)
                fx = force * (dx / dist)
                fy = force * (dy / dist)
                forces[a] = (forces[a][0] + fx, forces[a][1] + fy)
                forces[b] = (forces[b][0] - fx, forces[b][1] - fy)

        for a, b in edge_list:
            if a not in positions or b not in positions:
                continue
            ax, ay = positions[a]
            bx, by = positions[b]
            dx = bx - ax
            dy = by - ay
            dist = math.sqrt(dx * dx + dy * dy) + 0.01
            target = 0.25
            force = spring * (dist - target)
            fx = force * (dx / dist)
            fy = force * (dy / dist)
            forces[a] = (forces[a][0] + fx, forces[a][1] + fy)
            forces[b] = (forces[b][0] - fx, forces[b][1] - fy)

        for node_id in node_ids:
            vx, vy = velocities[node_id]
            fx, fy = forces[node_id]
            vx = (vx + fx) * damping
            vy = (vy + fy) * damping
            x, y = positions[node_id]
            x = min(1.0, max(0.0, x + vx))
            y = min(1.0, max(0.0, y + vy))
            positions[node_id] = (x, y)
            velocities[node_id] = (vx, vy)

    return positions


def scale_positions(
    positions: dict[str, tuple[float, float]], width: int, height: int
) -> dict[str, tuple[int, int]]:
    scaled: dict[str, tuple[int, int]] = {}
    for node_id, (x, y) in positions.items():
        sx = max(0, min(width - 1, int(x * (width - 1))))
        sy = max(0, min(height - 1, int(y * (height - 1))))
        scaled[node_id] = (sx, sy)
    return scaled


def draw_line(
    grid: list[list[tuple[str, str | None]]],
    start: tuple[int, int],
    end: tuple[int, int],
) -> None:
    x0, y0 = start
    x1, y1 = end
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy

    while True:
        if 0 <= y0 < len(grid) and 0 <= x0 < len(grid[0]):
            if grid[y0][x0][0] == " ":
                grid[y0][x0] = (".", "grey50")
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
