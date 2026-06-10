from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .ignore import IgnoreMatcher
from .scan import ScannedNode, scan_tree, stat_node
from .symbols import ChangeKind


Clock = Callable[[], float]


@dataclass
class TreeNode:
    path: Path
    is_dir: bool
    mtime_ns: int
    size: int
    change: ChangeKind = ChangeKind.UNCHANGED
    changed_at: float | None = None
    subtree_changed_at: float = 0.0
    previous_path: Path | None = None


class TreeState:
    def __init__(
        self,
        root: Path,
        ignore: IgnoreMatcher,
        *,
        depth: int | None = None,
        fade_seconds: float = 8.0,
        clock: Clock = time.monotonic,
    ) -> None:
        self.root = root.resolve()
        self.ignore = ignore
        self.depth = depth
        self.fade_seconds = fade_seconds
        self.clock = clock
        self.nodes: dict[Path, TreeNode] = {}

    @classmethod
    def from_scan(
        cls,
        root: Path,
        ignore: IgnoreMatcher,
        *,
        depth: int | None = None,
        fade_seconds: float = 8.0,
        clock: Clock = time.monotonic,
    ) -> "TreeState":
        state = cls(root, ignore, depth=depth, fade_seconds=fade_seconds, clock=clock)
        for path, scanned in scan_tree(state.root, ignore, depth=depth).items():
            state.nodes[path] = TreeNode(path=scanned.path, is_dir=scanned.is_dir, mtime_ns=scanned.mtime_ns, size=scanned.size)
        return state

    def create_or_modify(self, path: Path) -> None:
        path = path.resolve()
        if self.ignore.ignores(path):
            return
        node = stat_node(path)
        if node is None:
            self.delete(path)
            return
        if node.is_dir:
            previous = self.nodes.get(path)
            kind = ChangeKind.NEW if previous is None or previous.change == ChangeKind.DELETED else ChangeKind.UNCHANGED
            self._scan_subtree(path, kind)
            return
        previous = self.nodes.get(path)
        kind = ChangeKind.NEW if previous is None or previous.change in {ChangeKind.DELETED, ChangeKind.NEW} else ChangeKind.MODIFIED
        self.nodes[path] = self._from_scanned(node, kind)
        self._mark_ancestors(path, self.nodes[path].changed_at)

    def delete(self, path: Path) -> None:
        path = path.resolve()
        now = self.clock()
        targets = [node_path for node_path in self.nodes if node_path == path or _is_relative_to(node_path, path)]
        if not targets:
            self.nodes[path] = TreeNode(path=path, is_dir=False, mtime_ns=0, size=0, change=ChangeKind.DELETED, changed_at=now)
            self._mark_ancestors(path, now)
            return
        for target in targets:
            node = self.nodes[target]
            node.change = ChangeKind.DELETED
            node.changed_at = now
        self._mark_ancestors(path, now)

    def move(self, src: Path, dest: Path) -> None:
        src = src.resolve()
        dest = dest.resolve()
        if self.ignore.ignores(dest):
            self.delete(src)
            return
        moved: list[tuple[Path, Path, TreeNode]] = []
        for path, node in list(self.nodes.items()):
            if path == src or _is_relative_to(path, src):
                rel = path.relative_to(src) if path != src else Path()
                new_path = dest / rel
                moved.append((path, new_path.resolve(), node))
                del self.nodes[path]
        if not moved:
            self.create_or_modify(dest)
            node = self.nodes.get(dest)
            if node:
                node.change = ChangeKind.MOVED
                node.previous_path = src
                node.changed_at = self.clock()
                self._mark_ancestors(dest, node.changed_at)
            return
        now = self.clock()
        for old_path, new_path, node in moved:
            node.path = new_path
            node.change = ChangeKind.MOVED
            node.changed_at = now
            node.previous_path = old_path
            self.nodes[new_path] = node
        self._mark_ancestors(src, now)
        self._mark_ancestors(dest, now)
        if dest.exists() and dest.is_dir():
            self._scan_subtree(dest, ChangeKind.MOVED)

    def refresh(self) -> None:
        scanned = scan_tree(self.root, self.ignore, depth=self.depth)
        for path, scan_node in scanned.items():
            current = self.nodes.get(path)
            if current is None:
                self.nodes[path] = self._from_scanned(scan_node, ChangeKind.NEW)
                self._mark_ancestors(path, self.nodes[path].changed_at)
            elif current.is_dir:
                current.mtime_ns = scan_node.mtime_ns
                current.size = scan_node.size
            elif current.mtime_ns != scan_node.mtime_ns or current.size != scan_node.size:
                self.nodes[path] = self._from_scanned(scan_node, ChangeKind.MODIFIED)
                self._mark_ancestors(path, self.nodes[path].changed_at)
        for path in list(self.nodes):
            if path not in scanned:
                self.delete(path)

    def prune_faded(self) -> None:
        now = self.clock()
        for path in list(self.nodes):
            node = self.nodes[path]
            if node.changed_at is None:
                pass
            else:
                age = now - node.changed_at
                if age >= self.fade_seconds:
                    if node.change == ChangeKind.DELETED:
                        del self.nodes[path]
                        continue
                    node.change = ChangeKind.UNCHANGED
                    node.changed_at = None
                    node.previous_path = None
            if node.subtree_changed_at and now - node.subtree_changed_at >= self.fade_seconds:
                node.subtree_changed_at = 0.0

    def visible_nodes(self, *, changed_only: bool = False) -> list[TreeNode]:
        nodes = [node for node in self.nodes.values() if not changed_only or node.change != ChangeKind.UNCHANGED]
        return sorted(nodes, key=lambda node: node.path.as_posix().lower())

    def _scan_subtree(self, path: Path, kind: ChangeKind) -> None:
        now = self.clock() if kind != ChangeKind.UNCHANGED else None
        for scanned in scan_tree(path, self.ignore, depth=None).values():
            existing = self.nodes.get(scanned.path)
            if kind == ChangeKind.MOVED:
                change = ChangeKind.MOVED
            elif scanned.path == path:
                change = kind
            elif existing is None or existing.change == ChangeKind.DELETED:
                change = ChangeKind.NEW
            elif kind == ChangeKind.NEW:
                change = ChangeKind.NEW
            else:
                change = existing.change
            updated = self._from_scanned(scanned, change, existing=existing, now=now)
            self.nodes[scanned.path] = updated
            if (
                updated.changed_at is not None
                and (
                    existing is None
                    or updated.change != existing.change
                    or updated.changed_at != existing.changed_at
                )
            ):
                self._mark_ancestors(scanned.path, updated.changed_at)

    def _from_scanned(
        self,
        scanned: ScannedNode,
        kind: ChangeKind,
        *,
        existing: TreeNode | None = None,
        now: float | None = None,
    ) -> TreeNode:
        if now is None and kind != ChangeKind.UNCHANGED:
            now = self.clock()
        changed_at = now if kind != ChangeKind.UNCHANGED else None
        previous_path = None
        subtree_changed_at = 0.0
        if existing is not None:
            if kind == existing.change:
                changed_at = existing.changed_at
                previous_path = existing.previous_path
            subtree_changed_at = existing.subtree_changed_at
        return TreeNode(
            path=scanned.path,
            is_dir=scanned.is_dir,
            mtime_ns=scanned.mtime_ns,
            size=scanned.size,
            change=kind,
            changed_at=changed_at,
            subtree_changed_at=subtree_changed_at,
            previous_path=previous_path,
        )

    def _mark_ancestors(self, path: Path, changed_at: float | None) -> None:
        if changed_at is None:
            return
        parent_path = path.parent
        while parent_path in self.nodes:
            self.nodes[parent_path].subtree_changed_at = changed_at
            parent_path = parent_path.parent


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
