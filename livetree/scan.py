from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .ignore import IgnoreMatcher


@dataclass(frozen=True)
class ScannedNode:
    path: Path
    is_dir: bool
    mtime_ns: int
    size: int


def stat_node(path: Path) -> ScannedNode | None:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    return ScannedNode(
        path=path.resolve(),
        is_dir=path.is_dir(),
        mtime_ns=stat.st_mtime_ns,
        size=stat.st_size,
    )


def scan_tree(root: Path, ignore: IgnoreMatcher, depth: int | None = None) -> dict[Path, ScannedNode]:
    root = root.resolve()
    nodes: dict[Path, ScannedNode] = {}

    def visit(path: Path, current_depth: int) -> None:
        if ignore.ignores(path):
            return
        node = stat_node(path)
        if node is None:
            return
        nodes[node.path] = node
        if not node.is_dir:
            return
        if depth is not None and current_depth >= depth:
            return
        try:
            children = sorted(path.iterdir(), key=lambda child: (not child.is_dir(), child.name.lower()))
        except (OSError, PermissionError):
            return
        for child in children:
            visit(child, current_depth + 1)

    visit(root, 0)
    return nodes

