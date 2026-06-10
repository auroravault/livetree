# livetree

`livetree` (`lt`) is a live terminal tree renderer for watching file changes in repos and folders.

Like `tree`, but live.

## Status

Early MVP. APIs, output format, and CLI options may change before `1.0.0`.

Current MVP scope:

- Render an initial directory tree.
- Watch for create, modify, delete, and move filesystem events.
- Mark recent changes and fade markers after a short time.
- Keep noisy default paths out of the tree.
- Provide compact, dense, ASCII, Unicode, and git-like symbol displays.
- open source.  
- python first, rust later.
## Install for development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
lt .
```

## Usage

```bash
lt .
lt . --depth 3
lt . --changed
lt . --pattern "*.py"
lt . -p "*.py"
lt . --pattern tests
lt . --git
lt dist --fade 30
lt --symbols ascii
lt --symbols unicode
lt --no-color
lt --compact
lt --dense
lt --once
```

## Example

```text
repo/
├─ src/
│  ├─ main.py                       ● modified 2s ago
│  ├─ watcher.py                    ✚ new
│  ├─ renderer.py                   ◌ unchanged
│  └─ cli.py                        ⚠ deleted?
├─ tests/
│  └─ test_render.py                ● modified 14s ago
├─ README.md                        ◌ unchanged
└─ target/                          hidden
```

## Ignore Behavior

`livetree` ignores noisy folders by default:

- `.git`
- `node_modules`
- `target`
- `dist`
- `build`
- `__pycache__`
- `.venv`
- `.pytest_cache`
- `.ruff_cache`
- `.mypy_cache`
- `.DS_Store`

`livetree` loads default ignores, then `.gitignore`, then `.ltignore` from the selected workdir. Patterns use gitignore-style matching.

Create a default `.ltignore` file:

```bash
lt -i
lt -i .
lt -i /path/to/folder
```

## Symbols

Default Unicode symbols:

```text
✚  new
●  modified
✖  deleted
➜  moved
⚠  warning
◌  unchanged
```

ASCII symbols:

```text
+  new
*  modified
-  deleted
>  moved
!  warning
```

Git symbols:

```text
M   modified
A   added
D   deleted
R   renamed
C   copied
??  untracked
!!  ignored
```

## Dev Environment

Developed and tested on:

| | |
|---|---|
| OS | Debian GNU/Linux 13 (trixie) — kernel 6.12 |
| Python | 3.13.5 |
| rich | 15.0.0 |
| watchdog | 6.0.0 |
| typer | 0.26.7 |
| pathspec | 1.1.1 |

To set up the dev environment and make `lt` available globally on this machine:

```bash
./scripts/startlt.sh
```

This creates `.venv`, installs the package in editable mode, and symlinks `lt` into
`~/.local/bin`. The symlink persists across reboots — re-run only after a fresh
clone or if `.venv` is deleted.

To run the test suite:

```bash
source .venv/bin/activate
pytest
```

## Planned Options

```bash
lt .
lt . --depth 3
lt . --changed
lt . --pattern "*.py"
lt . -p "*.py"
lt . --pattern tests
lt . --git
lt dist --fade 30
lt --help
lt -i
lt -i .
lt -i /path/to/folder
lt /path/to/folder --depth 3 --changed
lt /path/to/folder -p "*.py" --depth 3 --changed
lt --no-color
lt --symbols ascii
lt --symbols unicode
lt --symbols git
lt --since 10m
lt --focus changed
lt . --compact
lt . --dense
lt . --no-meta
lt . --max-name-width 48
```

## Versioning

This project uses Semantic Versioning.

See [VERSIONING.md](VERSIONING.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Origin

`livetree` was built while developing [AuroraVault](https://auroranode.com/vault), a CLI-first tool for signed file receipts, evidence trails, and developer-friendly proof workflows.
It is part of the broader [AuroraNode](https://auroranode.com) secosystem.

## License

Use the repository license.
