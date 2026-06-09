from pathlib import Path

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
