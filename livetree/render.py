from __future__ import annotations

from pathlib import Path

from rich.console import Group
from rich.text import Text

from .state import TreeNode, TreeState
from .symbols import ChangeKind, get_symbol

# Single sort-key used by both walk() and _last_paths() so they can never diverge.
_CHILD_SORT_KEY = lambda node: (not node.is_dir, node.path.name.lower())  # noqa: E731


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
    nodes, by_parent = _ordered_nodes(
        state.root, list(state.nodes.values()),
        changed_only=changed_only, pattern=pattern,
    )
    lines: list[Text] = []
    last_paths = _last_paths(by_parent)
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
        if pattern:
            msg = "(empty)"
        else:
            msg = "(no changed files)" if changed_only else "(empty)"
        lines.append(Text(msg, style="dim"))
    return Group(*lines)


def _ordered_nodes(
    root: Path,
    candidates: list[TreeNode],
    *,
    changed_only: bool,
    pattern: str | None = None,
) -> tuple[list[TreeNode], dict[Path, list[TreeNode]]]:

    # --- Pattern filter ---
    # Build matching set from ALL candidates before changed_only narrows them,
    # so ancestor directories are never stripped by changed_only.
    if pattern:
        # Direct matches: files whose path matches, OR directories whose name matches.
        direct_match_paths = {node.path for node in candidates if node.path.match(pattern)}
        if not direct_match_paths:
            return [], {}

        # Directories that matched directly → include their entire subtree.
        matched_dir_paths = {
            node.path for node in candidates
            if node.is_dir and node.path in direct_match_paths
        }

        # Final set of file paths to keep.
        matching_file_paths = {
            node.path for node in candidates
            if not node.is_dir and (
                node.path in direct_match_paths
                or any(d in node.path.parents for d in matched_dir_paths)
            )
        }

        # Ancestor directories needed to connect matched files/dirs to the root.
        anchor_paths = matching_file_paths | matched_dir_paths
        ancestor_dirs = {anc for p in anchor_paths for anc in p.parents}

        candidates = [
            node for node in candidates
            if (not node.is_dir and node.path in matching_file_paths)
            or (node.is_dir and (
                node.path in matched_dir_paths
                or node.path == root
                or node.path in ancestor_dirs
            ))
        ]

    # --- changed_only filter ---
    # Keep changed nodes AND the ancestor directories they need for tree context.
    if changed_only:
        changed_paths = {
            node.path for node in candidates
            if node.change != ChangeKind.UNCHANGED
        }
        required_ancestors = {anc for p in changed_paths for anc in p.parents}
        candidates = [
            node for node in candidates
            if node.change != ChangeKind.UNCHANGED or node.path in required_ancestors
        ]

    # --- Build pre-sorted by_parent index ---
    # Shared by the DFS walk and _last_paths so the sort key is computed once
    # and both functions are guaranteed to agree on child order.
    by_parent: dict[Path, list[TreeNode]] = {}
    for node in candidates:
        if node.path != root:
            by_parent.setdefault(node.path.parent, []).append(node)
    for children in by_parent.values():
        children.sort(key=_CHILD_SORT_KEY)

    # --- DFS ordering (iterative — no recursion-limit risk) ---
    root_node = next((node for node in candidates if node.path == root), None)
    ordered: list[TreeNode] = []
    ordered_ids: set[int] = set()

    if root_node is not None:
        ordered.append(root_node)
        ordered_ids.add(id(root_node))

    # Stack holds (parent_path, next_child_index) so we process children one at
    # a time in depth-first order without recursive calls.
    stack: list[tuple[Path, int]] = [(root, 0)]
    while stack:
        parent, idx = stack[-1]
        children = by_parent.get(parent, [])
        if idx < len(children):
            stack[-1] = (parent, idx + 1)
            child = children[idx]
            ordered.append(child)
            ordered_ids.add(id(child))
            if child.is_dir:
                stack.append((child.path, 0))
        else:
            stack.pop()

    # Nodes unreachable via walk (orphaned — parent absent from candidates).
    remaining = [node for node in candidates if id(node) not in ordered_ids]
    remaining.sort(key=lambda node: node.path.as_posix().lower())
    ordered.extend(remaining)
    return ordered, by_parent


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


def _last_paths(by_parent: dict[Path, list[TreeNode]]) -> set[Path]:
    # Each children list is already sorted by _CHILD_SORT_KEY; the last element
    # is the last sibling drawn, so it gets the └─ connector.
    last: set[Path] = set()
    for siblings in by_parent.values():
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
