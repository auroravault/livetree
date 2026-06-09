import pytest

from livetree.symbols import ChangeKind, get_symbol


def test_symbol_modes() -> None:
    assert get_symbol("ascii", ChangeKind.NEW).text == "+"
    assert get_symbol("git", ChangeKind.MODIFIED).text == "M "
    assert get_symbol("unicode", ChangeKind.DELETED).text == "✖"


def test_unknown_symbol_mode_raises() -> None:
    with pytest.raises(ValueError):
        get_symbol("bad", ChangeKind.NEW)

