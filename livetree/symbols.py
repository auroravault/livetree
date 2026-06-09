from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ChangeKind(str, Enum):
    UNCHANGED = "unchanged"
    NEW = "new"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"
    WARNING = "warning"


@dataclass(frozen=True)
class Symbol:
    text: str
    style: str
    label: str


SYMBOLS: dict[str, dict[ChangeKind, Symbol]] = {
    "unicode": {
        ChangeKind.UNCHANGED: Symbol("◌", "default", "unchanged"),
        ChangeKind.NEW: Symbol("✚", "green", "new"),
        ChangeKind.MODIFIED: Symbol("●", "yellow3", "modified"),
        ChangeKind.DELETED: Symbol("✖", "magenta", "deleted"),
        ChangeKind.MOVED: Symbol("➜", "dim", "moved"),
        ChangeKind.WARNING: Symbol("⚠", "red", "warning"),
    },
    "ascii": {
        ChangeKind.UNCHANGED: Symbol(" ", "default", "unchanged"),
        ChangeKind.NEW: Symbol("+", "green", "new"),
        ChangeKind.MODIFIED: Symbol("*", "yellow3", "modified"),
        ChangeKind.DELETED: Symbol("-", "magenta", "deleted"),
        ChangeKind.MOVED: Symbol(">", "dim", "moved"),
        ChangeKind.WARNING: Symbol("!", "red", "warning"),
    },
    "git": {
        ChangeKind.UNCHANGED: Symbol("  ", "default", "unchanged"),
        ChangeKind.NEW: Symbol("A ", "green", "added"),
        ChangeKind.MODIFIED: Symbol("M ", "yellow3", "modified"),
        ChangeKind.DELETED: Symbol("D ", "magenta", "deleted"),
        ChangeKind.MOVED: Symbol("R ", "dim", "renamed"),
        ChangeKind.WARNING: Symbol("!!", "red", "warning"),
    },
}


def get_symbol(mode: str, kind: ChangeKind) -> Symbol:
    try:
        return SYMBOLS[mode][kind]
    except KeyError as exc:
        modes = ", ".join(sorted(SYMBOLS))
        raise ValueError(f"unknown symbol mode {mode!r}; expected one of: {modes}") from exc

