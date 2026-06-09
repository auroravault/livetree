from pathlib import Path

from livetree.ignore import load_ignore
from livetree.state import TreeState
from livetree.symbols import ChangeKind
from livetree.watch import TreeEvent, apply_events


def test_apply_events_updates_state(tmp_path: Path) -> None:
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))
    (tmp_path / "created.txt").write_text("created", encoding="utf-8")

    changed = apply_events(state, [TreeEvent("created", tmp_path / "created.txt")])

    assert changed
    assert state.nodes[(tmp_path / "created.txt").resolve()].change == ChangeKind.NEW

