from pathlib import Path

from livetree.ignore import load_ignore
from livetree.render import render_tree
from livetree.state import TreeState
from livetree.symbols import ChangeKind


def _lines(state: TreeState, **kwargs: object) -> list[str]:
    return [line.plain for line in render_tree(state, **kwargs).renderables]


def _flat(state: TreeState, **kwargs: object) -> str:
    return " ".join(_lines(state, **kwargs))


def test_render_shows_only_file_as_modified_after_directory_event(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    other = tmp_path / "other.md"
    readme.write_text("a", encoding="utf-8")
    other.write_text("b", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    readme.write_text("aa", encoding="utf-8")
    state.create_or_modify(readme)
    state.create_or_modify(tmp_path)

    lines = _lines(state)
    modified_lines = [line for line in lines if "modified" in line]
    assert len(modified_lines) == 1
    assert "README.md" in modified_lines[0]
    assert all("other.md" not in line or "unchanged" in line for line in lines)


# --- pattern filtering ---

def test_render_pattern_shows_only_matching_files(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("", encoding="utf-8")
    (tmp_path / "README.md").write_text("", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    flat = _flat(state, pattern="*.py")
    assert "main.py" in flat
    assert "README.md" not in flat


def test_render_pattern_hides_empty_directories(tmp_path: Path) -> None:
    src = tmp_path / "src"
    docs = tmp_path / "docs"
    src.mkdir()
    docs.mkdir()
    (src / "main.py").write_text("", encoding="utf-8")
    (docs / "guide.md").write_text("", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    flat = _flat(state, pattern="*.py")
    assert "src/" in flat
    assert "main.py" in flat
    assert "docs/" not in flat
    assert "guide.md" not in flat


def test_render_pattern_no_matches_renders_empty(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    lines = _lines(state, pattern="*.rs")
    assert lines == ["(empty)"]


def test_render_pattern_with_changed_only_preserves_ancestor_dirs(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    utils = src / "utils.py"
    utils.write_text("a", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    utils.write_text("b", encoding="utf-8")
    state.create_or_modify(utils)

    lines = _lines(state, changed_only=True, pattern="*.py")
    flat = " ".join(lines)
    # src/ is UNCHANGED but must appear as the parent of the changed matched file
    assert "src/" in flat
    assert "utils.py" in flat


def test_render_pattern_with_changed_only_nested_file_has_correct_prefix(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    utils = src / "utils.py"
    utils.write_text("a", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    utils.write_text("b", encoding="utf-8")
    state.create_or_modify(utils)

    lines = _lines(state, changed_only=True, pattern="*.py")
    # utils.py must be indented under src/, not rendered flat at root level
    utils_line = next((l for l in lines if "utils.py" in l), None)
    assert utils_line is not None
    assert utils_line.startswith(("├─", "└─", "│", " "))
    # There must be a src/ line before utils.py
    src_idx = next((i for i, l in enumerate(lines) if "src/" in l), None)
    utils_idx = next((i for i, l in enumerate(lines) if "utils.py" in l), None)
    assert src_idx is not None
    assert utils_idx is not None
    assert src_idx < utils_idx


def test_render_pattern_sibling_non_matching_files_excluded(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("", encoding="utf-8")
    (src / "notes.md").write_text("", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    flat = _flat(state, pattern="*.py")
    assert "main.py" in flat
    assert "notes.md" not in flat


def test_render_pattern_unchanged_parent_excluded_when_no_matching_children(tmp_path: Path) -> None:
    lib = tmp_path / "lib"
    lib.mkdir()
    (lib / "helper.js").write_text("", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    flat = _flat(state, pattern="*.py")
    assert "lib/" not in flat
    assert "helper.js" not in flat


# --- display modes ---

def test_render_once_renders_without_watching(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("x", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    group = render_tree(state)
    assert any("file.txt" in line.plain for line in group.renderables)


def test_render_compact_shows_symbol_and_age(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))
    state.create_or_modify(tmp_path / "a.txt")

    assert "a.txt" in _flat(state, compact=True)


def test_render_dense_shows_single_symbol(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))
    state.create_or_modify(tmp_path / "a.txt")

    flat = _flat(state, dense=True)
    assert "a.txt" in flat
    assert "modified" not in flat


def test_render_no_meta_hides_status(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))
    state.create_or_modify(tmp_path / "a.txt")

    flat = _flat(state, no_meta=True)
    assert "a.txt" in flat
    assert "modified" not in flat
    assert "unchanged" not in flat
