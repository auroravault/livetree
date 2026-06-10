from pathlib import Path

import pytest

from livetree.ignore import load_ignore
from livetree.render import render_tree
from livetree.state import TreeState


def test_render_shows_only_file_as_modified_after_directory_event(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    other = tmp_path / "other.md"
    readme.write_text("a", encoding="utf-8")
    other.write_text("b", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    readme.write_text("aa", encoding="utf-8")
    state.create_or_modify(readme)
    state.create_or_modify(tmp_path)

    lines = [line.plain for line in render_tree(state).renderables]

    modified_lines = [line for line in lines if "modified" in line]
    assert len(modified_lines) == 1
    assert "README.md" in modified_lines[0]
    assert all("other.md" not in line or "unchanged" in line for line in lines)


def test_render_pattern_shows_only_matching_files(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("", encoding="utf-8")
    (tmp_path / "README.md").write_text("", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    lines = [line.plain for line in render_tree(state, pattern="*.py").renderables]

    names = [line.split()[-1].split()[0] if line.strip() else "" for line in lines]
    flat = " ".join(lines)
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

    lines = [line.plain for line in render_tree(state, pattern="*.py").renderables]
    flat = " ".join(lines)

    assert "src/" in flat
    assert "main.py" in flat
    assert "docs/" not in flat
    assert "guide.md" not in flat


def test_render_once_renders_without_watching(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("x", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))

    group = render_tree(state)

    assert any("file.txt" in line.plain for line in group.renderables)


def test_render_compact_shows_symbol_and_age(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))
    state.create_or_modify(tmp_path / "a.txt")

    lines = [line.plain for line in render_tree(state, compact=True).renderables]
    flat = " ".join(lines)

    assert "a.txt" in flat


def test_render_dense_shows_single_symbol(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))
    state.create_or_modify(tmp_path / "a.txt")

    lines = [line.plain for line in render_tree(state, dense=True).renderables]
    flat = " ".join(lines)

    assert "a.txt" in flat
    assert "modified" not in flat


def test_render_no_meta_hides_status(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    state = TreeState.from_scan(tmp_path, load_ignore(tmp_path))
    state.create_or_modify(tmp_path / "a.txt")

    lines = [line.plain for line in render_tree(state, no_meta=True).renderables]
    flat = " ".join(lines)

    assert "a.txt" in flat
    assert "modified" not in flat
    assert "unchanged" not in flat
