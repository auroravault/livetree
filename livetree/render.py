from __future__ import annotations

from pathlib import Path

from rich.console import Group
from rich.text import Text

from .state import TreeNode, TreeState
from .symbols import ChangeKind, get_symbol


def render_tree(
    state: TreeState,
    *,
    symbols: str = "unicode",
    changed_only: bool = False,
    pattern: str | None = None,
    compact: bool = False,
    dense: bool = False,
    no_meta: bool = False,
    max_name_width: int = 72,
) -> Group:
    state.prune_faded()
    nodes = _ordered_nodes(state.root, list(state.nodes.values()), changed_only=changed_only, pattern=pattern)
    lines: list[Text] = []
    last_paths = _last_paths(state.root, nodes)
    now = state.clock()
    for node in nodes:
        lines.append(
            _render_node(
                state.root,
                node,
                last_paths=last_paths,
                symbols=symbols,
                compact=compact,
                dense=dense,
                no_meta=no_meta,
                max_name_width=max_name_width,
                now=now,
            )
        )
    if not lines:
        lines.append(Text("(no changed files)" if changed_only else "(empty)", style="dim"))
    return Group(*lines)


def _ordered_nodes(root: Path, candidates: list[TreeNode], *, changed_only: bool, pattern: str | None = None) -> list[TreeNode]:
    nodes = [node for node in candidates if not changed_only or node.change != ChangeKind.UNCHANGED]
    if pattern:
        matching = {node.path for node in nodes if not node.is_dir and (node.path.match(pattern) or node.path.name == pattern)}
        nodes = [
            node for node in nodes
            if (not node.is_dir and node.path in matching)
            or (node.is_dir and (node.path == root or any(p for p in matching if node.path in p.parents)))
        ]
    node_by_path = {node.path: node for node in nodes}
    if root in node_by_path:
        ordered = [node_by_path[root]]
    else:
        ordered = []

    def walk(parent: Path) -> None:
        children = [
            node
            for node in nodes
            if node.path != parent and node.path.parent == parent
        ]
        children.sort(key=lambda node: (not node.is_dir, node.path.name.lower()))
        for child in children:
            ordered.append(child)
            if child.is_dir:
                walk(child.path)

    walk(root)
    remaining = [node for node in nodes if node not in ordered]
    remaining.sort(key=lambda node: node.path.as_posix().lower())
    ordered.extend(remaining)
    return ordered


def _render_node(
    root: Path,
    node: TreeNode,
    *,
    last_paths: set[Path],
    symbols: str,
    compact: bool,
    dense: bool,
    no_meta: bool,
    max_name_width: int,
    now: float,
) -> Text:
    rel = Path(".") if node.path == root else node.path.relative_to(root)
    prefix = _prefix(root, node.path, last_paths)
    name = root.name + "/" if rel == Path(".") else rel.name + ("/" if node.is_dir else "")
    name = _truncate(name, max_name_width)
    symbol = get_symbol(symbols, node.change)

    text = Text(prefix, style="dim")
    text.append(name, style="magenta" if node.is_dir else "default")

    if no_meta:
        return text
    if dense:
        text.append(" ")
        text.append(symbol.text, style=symbol.style)
        return text
    if compact:
        text.append(" ")
        text.append(symbol.text, style=symbol.style)
        if node.changed_at is not None:
            text.append(f" {_age(node, now)}", style="dim")
        return text
    pad = max(1, 36 - len(prefix) - len(name))
    text.append(" " * pad)
    text.append(symbol.text, style=symbol.style)
    text.append(f" {symbol.label}", style=symbol.style if node.change != ChangeKind.UNCHANGED else "dim")
    if node.changed_at is not None:
        text.append(f" {_age(node, now)} ago", style="dim")
    return text


def _age(node: TreeNode, now: float) -> str:
    if node.changed_at is None:
        return ""
    seconds = max(0, int(now - node.changed_at))
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    return f"{minutes // 60}h"


def _truncate(name: str, width: int) -> str:
    if width <= 1 or len(name) <= width:
        return name
    return name[: max(1, width - 3)] + "..."


def _last_paths(root: Path, nodes: list[TreeNode]) -> set[Path]:
    by_parent: dict[Path, list[TreeNode]] = {}
    for node in nodes:
        if node.path == root:
            continue
        by_parent.setdefault(node.path.parent, []).append(node)
    last: set[Path] = set()
    for siblings in by_parent.values():
        siblings.sort(key=lambda node: (not node.is_dir, node.path.name.lower()))
        if siblings:
            last.add(siblings[-1].path)
    return last


def _prefix(root: Path, path: Path, last_paths: set[Path]) -> str:
    if path == root:
        return ""
    rel_parts = path.relative_to(root).parts
    pieces: list[str] = []
    current = root
    for part in rel_parts[:-1]:
        current = current / part
        pieces.append("   " if current in last_paths else "│  ")
    pieces.append("└─ " if path in last_paths else "├─ ")
    return "".join(pieces)
