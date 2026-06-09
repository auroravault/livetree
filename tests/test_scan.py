from pathlib import Path

from livetree.ignore import load_ignore
from livetree.scan import scan_tree


def test_scan_tree_collects_directories_first_and_files(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')", encoding="utf-8")
    (tmp_path / "README.md").write_text("# readme", encoding="utf-8")

    nodes = scan_tree(tmp_path, load_ignore(tmp_path))

    assert tmp_path.resolve() in nodes
    assert (tmp_path / "src").resolve() in nodes
    assert (tmp_path / "src" / "main.py").resolve() in nodes
    assert (tmp_path / "README.md").resolve() in nodes


def test_scan_tree_respects_depth(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "nested.py").write_text("", encoding="utf-8")

    nodes = scan_tree(tmp_path, load_ignore(tmp_path), depth=1)

    assert (tmp_path / "src").resolve() in nodes
    assert (tmp_path / "src" / "nested.py").resolve() not in nodes

