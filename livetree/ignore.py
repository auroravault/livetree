from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pathspec


DEFAULT_LTIGNORE = """\
.git
node_modules
target
dist
build
__pycache__
.venv
.pytest_cache
.ruff_cache
.mypy_cache
.DS_Store
"""


@dataclass(frozen=True)
class IgnoreMatcher:
    root: Path
    spec: pathspec.PathSpec

    def ignores(self, path: Path) -> bool:
        path = path.resolve()
        if path == self.root:
            return False
        try:
            rel = path.relative_to(self.root).as_posix()
        except ValueError:
            return False
        if path.is_dir() and not rel.endswith("/"):
            rel = f"{rel}/"
        return self.spec.match_file(rel)


def _read_patterns(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def load_ignore(root: Path) -> IgnoreMatcher:
    root = root.resolve()
    patterns: list[str] = []
    patterns.extend(DEFAULT_LTIGNORE.splitlines())
    patterns.extend(_read_patterns(root / ".gitignore"))
    patterns.extend(_read_patterns(root / ".ltignore"))
    spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
    return IgnoreMatcher(root=root, spec=spec)


def init_ltignore(root: Path, overwrite: bool = False) -> Path:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = root / ".ltignore"
    if path.exists() and not overwrite:
        return path
    path.write_text(DEFAULT_LTIGNORE, encoding="utf-8")
    return path

