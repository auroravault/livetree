from __future__ import annotations

import queue
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from watchdog.events import FileSystemEvent, FileSystemEventHandler, FileSystemMovedEvent
from watchdog.observers import Observer

from .state import TreeState


@dataclass(frozen=True)
class TreeEvent:
    kind: str
    src: Path
    dest: Path | None = None


class QueueingHandler(FileSystemEventHandler):
    def __init__(self, events: "queue.Queue[TreeEvent]") -> None:
        self.events = events

    def on_created(self, event: FileSystemEvent) -> None:
        self.events.put(TreeEvent("created", Path(event.src_path)))

    def on_modified(self, event: FileSystemEvent) -> None:
        self.events.put(TreeEvent("modified", Path(event.src_path)))

    def on_deleted(self, event: FileSystemEvent) -> None:
        self.events.put(TreeEvent("deleted", Path(event.src_path)))

    def on_moved(self, event: FileSystemMovedEvent) -> None:
        self.events.put(TreeEvent("moved", Path(event.src_path), Path(event.dest_path)))


def apply_events(state: TreeState, events: Iterable[TreeEvent]) -> bool:
    changed = False
    for event in events:
        if event.kind in {"created", "modified"}:
            state.create_or_modify(event.src)
            changed = True
        elif event.kind == "deleted":
            state.delete(event.src)
            changed = True
        elif event.kind == "moved" and event.dest is not None:
            state.move(event.src, event.dest)
            changed = True
    return changed


def drain_events(events: "queue.Queue[TreeEvent]", debounce_seconds: float) -> list[TreeEvent]:
    drained: list[TreeEvent] = []
    try:
        first = events.get(timeout=0.1)
    except queue.Empty:
        return drained
    drained.append(first)
    deadline = time.monotonic() + debounce_seconds
    while time.monotonic() < deadline:
        try:
            drained.append(events.get(timeout=max(0.0, deadline - time.monotonic())))
        except queue.Empty:
            break
    while True:
        try:
            drained.append(events.get_nowait())
        except queue.Empty:
            break
    return drained


class LiveWatcher:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.events: queue.Queue[TreeEvent] = queue.Queue()
        self.observer = Observer()
        self.handler = QueueingHandler(self.events)

    def __enter__(self) -> "LiveWatcher":
        self.observer.schedule(self.handler, str(self.root), recursive=True)
        self.observer.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.observer.stop()
        self.observer.join(timeout=2)

