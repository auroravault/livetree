from pathlib import Path

from livetree.ignore import load_ignore
from livetree.state import TreeState
from livetree.symbols import ChangeKind


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_create_modify_delete_and_fade(tmp_path: Path) -> None:
    clock = FakeClock()
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path), fade_seconds=5, clock=clock)

    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    state.create_or_modify(tmp_path / "b.txt")
    assert state.nodes[(tmp_path / "b.txt").resolve()].change == ChangeKind.NEW

    (tmp_path / "a.txt").write_text("aa", encoding="utf-8")
    state.create_or_modify(tmp_path / "a.txt")
    assert state.nodes[(tmp_path / "a.txt").resolve()].change == ChangeKind.MODIFIED

    (tmp_path / "a.txt").unlink()
    state.delete(tmp_path / "a.txt")
    assert state.nodes[(tmp_path / "a.txt").resolve()].change == ChangeKind.DELETED

    clock.now = 6
    state.prune_faded()
    assert (tmp_path / "a.txt").resolve() not in state.nodes
    assert state.nodes[(tmp_path / "b.txt").resolve()].change == ChangeKind.UNCHANGED


def test_move_updates_path_and_marks_moved(tmp_path: Path) -> None:
    (tmp_path / "old.txt").write_text("old", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))
    (tmp_path / "old.txt").rename(tmp_path / "new.txt")

    state.move(tmp_path / "old.txt", tmp_path / "new.txt")

    assert (tmp_path / "old.txt").resolve() not in state.nodes
    node = state.nodes[(tmp_path / "new.txt").resolve()]
    assert node.change == ChangeKind.MOVED
    assert node.previous_path == (tmp_path / "old.txt").resolve()


def test_refresh_detects_external_changes(tmp_path: Path) -> None:
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    (tmp_path / "created.txt").write_text("created", encoding="utf-8")
    state.refresh()

    assert state.nodes[(tmp_path / "created.txt").resolve()].change == ChangeKind.NEW


def test_new_file_stays_new_after_follow_up_modify_event(tmp_path: Path) -> None:
    target = tmp_path / "created.txt"
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    target.write_text("created", encoding="utf-8")
    state.create_or_modify(target)
    target.write_text("created again", encoding="utf-8")
    state.create_or_modify(target)

    assert state.nodes[target.resolve()].change == ChangeKind.NEW


def test_modified_file_only_affects_target_file(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("a", encoding="utf-8")
    (tmp_path / "other.md").write_text("b", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    (tmp_path / "README.md").write_text("aa", encoding="utf-8")
    state.create_or_modify(tmp_path / "README.md")

    assert state.nodes[(tmp_path / "README.md").resolve()].change == ChangeKind.MODIFIED
    assert state.nodes[(tmp_path / "other.md").resolve()].change == ChangeKind.UNCHANGED
    assert state.nodes[tmp_path.resolve()].change == ChangeKind.UNCHANGED
    assert state.nodes[tmp_path.resolve()].subtree_changed_at > 0.0


def test_nested_file_modify_does_not_mark_parent_dirs_modified(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    file_path = src / "main.py"
    file_path.write_text("print('x')", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    file_path.write_text("print('y')", encoding="utf-8")
    state.create_or_modify(file_path)

    assert state.nodes[file_path.resolve()].change == ChangeKind.MODIFIED
    assert state.nodes[src.resolve()].change == ChangeKind.UNCHANGED
    assert state.nodes[tmp_path.resolve()].change == ChangeKind.UNCHANGED
    assert state.nodes[src.resolve()].subtree_changed_at > 0.0
    assert state.nodes[tmp_path.resolve()].subtree_changed_at > 0.0


def test_directory_modified_event_does_not_mark_whole_tree_modified(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    readme = tmp_path / "README.md"
    other = tmp_path / "other.md"
    nested = src / "main.py"
    readme.write_text("a", encoding="utf-8")
    other.write_text("b", encoding="utf-8")
    nested.write_text("print('x')", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    readme.write_text("aa", encoding="utf-8")
    state.create_or_modify(readme)
    state.create_or_modify(tmp_path)

    assert state.nodes[readme.resolve()].change == ChangeKind.MODIFIED
    assert state.nodes[other.resolve()].change == ChangeKind.UNCHANGED
    assert state.nodes[nested.resolve()].change == ChangeKind.UNCHANGED
    assert state.nodes[src.resolve()].change == ChangeKind.UNCHANGED
    assert state.nodes[tmp_path.resolve()].change == ChangeKind.UNCHANGED


def test_fade_resets_only_local_status_and_subtree_activity(tmp_path: Path) -> None:
    clock = FakeClock()
    src = tmp_path / "src"
    src.mkdir()
    changed = src / "changed.py"
    sibling = src / "sibling.py"
    changed.write_text("a", encoding="utf-8")
    sibling.write_text("b", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path), fade_seconds=5, clock=clock)

    changed.write_text("aa", encoding="utf-8")
    state.create_or_modify(changed)
    assert state.nodes[changed.resolve()].change == ChangeKind.MODIFIED

    clock.now = 6
    state.prune_faded()

    assert state.nodes[changed.resolve()].change == ChangeKind.UNCHANGED
    assert state.nodes[sibling.resolve()].change == ChangeKind.UNCHANGED
    assert state.nodes[src.resolve()].change == ChangeKind.UNCHANGED
    assert state.nodes[tmp_path.resolve()].change == ChangeKind.UNCHANGED
    assert state.nodes[src.resolve()].subtree_changed_at == 0.0
    assert state.nodes[tmp_path.resolve()].subtree_changed_at == 0.0


def test_deleted_tombstone_removed_after_fade(tmp_path: Path) -> None:
    clock = FakeClock()
    target = tmp_path / "gone.txt"
    target.write_text("gone", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path), fade_seconds=5, clock=clock)

    target.unlink()
    state.delete(target)
    assert state.nodes[target.resolve()].change == ChangeKind.DELETED

    clock.now = 6
    state.prune_faded()

    assert target.resolve() not in state.nodes
    assert state.nodes[tmp_path.resolve()].change == ChangeKind.UNCHANGED
    assert state.nodes[tmp_path.resolve()].subtree_changed_at == 0.0
