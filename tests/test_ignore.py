from pathlib import Path

from livetree.ignore import DEFAULT_LTIGNORE, init_ltignore, load_ignore


def test_default_ignores_noisy_paths(tmp_path: Path) -> None:
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg.js").write_text("", encoding="utf-8")

    ignore = load_ignore(tmp_path)

    assert ignore.ignores(tmp_path / "node_modules")
    assert ignore.ignores(tmp_path / "node_modules" / "pkg.js")


def test_ltignore_extends_gitignore_patterns(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("ignored-by-git.txt\n", encoding="utf-8")
    (tmp_path / ".ltignore").write_text("ignored-by-lt.txt\n", encoding="utf-8")

    ignore = load_ignore(tmp_path)

    assert ignore.ignores(tmp_path / "ignored-by-git.txt")
    assert ignore.ignores(tmp_path / "ignored-by-lt.txt")
    assert not ignore.ignores(tmp_path / "visible.txt")


def test_init_ltignore_writes_default_file(tmp_path: Path) -> None:
    path = init_ltignore(tmp_path)

    assert path == tmp_path / ".ltignore"
    assert path.read_text(encoding="utf-8") == DEFAULT_LTIGNORE

