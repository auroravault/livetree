# Agent instructions for livetree

You are working on `livetree`, a small Python CLI that renders a live terminal directory tree.

## Goal

Build a useful MVP, not a framework.

The tool should behave like Linux `tree`, but live:

* show the initial directory tree
* detect new files
* detect modified files
* detect deleted files
* detect moved files
* visually mark recent changes
* fade markers after a short time
* stay fast enough for normal repos

## Hard constraints

* Use Python first.
* Do not rewrite in Rust.
* Do not introduce a full TUI framework unless explicitly requested.
* Keep dependencies minimal.
* Prefer clear code over clever abstractions.
* Keep files small and focused.
* Avoid async unless clearly necessary.
* Do not add network functionality.
* Do not add telemetry.
* Do not add daemon/service behavior.

## Current stack

* `rich` for rendering
* `watchdog` for filesystem events
* `typer` for CLI
* `pathspec` for `.gitignore` / `.ltignore` support

## Near-term priorities

1. Make create / modify / delete / move reliable.
2. Avoid UI flicker.
3. Add proper debounce.
4. Add changed-only mode.
5. Add `.gitignore` support.
6. Add `.ltignore` support.
7. Add optional git status annotations.
8. Add tests around scanning and state updates.

## CLI target

```bash
lt .
lt . --depth 3
lt . --changed
lt . --git
lt dist --fade 30
lt --help
lt -i
lt -i .
lt -i /path/to/folder
lt /path/to/folder --depth 3 --changed
lt /path/to/folder "*.py" --depth 3 --changed
lt --no-color
lt --symbols ascii
lt --symbols unicode
lt --symbols git
lt --since 10m
lt --focus changed
```

## Ignore behavior

Default noisy paths should be ignored.

On initial run, `lt` should be able to create a `.ltignore` file for the selected workdir when requested with `-i`.

Examples:

```bash
lt -i
lt -i .
lt -i /path/to/folder
```

Default `.ltignore` content:

```gitignore
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
```

The help output must explain:

* how `.ltignore` works
* where it is written
* how to initialize it with `lt -i`
* interaction between `.gitignore` and `.ltignore`

## UX principles

* Default output should be useful immediately.
* Recent changes should be visually obvious.
* Deleted files may remain visible briefly as tombstones, then disappear.
* The tool should exit cleanly on Ctrl+C.
* Ignore/config behavior must be visible in `lt --help`.
* Do not require users to understand internals to use the tool.

## Symbols

### ASCII symbols

```text
+  new
*  modified
-  deleted
>  moved
!  warning
```

### Unicode symbols — default
- colour symbols. Dim, not bold bright or poisionous. se #color
```text
✚  new  #green
●  modified #yellow, straw
✖  deleted #magenta
➜  moved #gray faded
⚠  warning #red
◌  unchanged #white, system text default.
```

### Git symbols

Use symbols close to `git status`:

```text
M   modified
A   added
D   deleted
R   renamed
C   copied
??  untracked
!!  ignored
```

## Example output

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
## Font and layout guidance

`livetree` must not attempt to change the user's terminal font or font size.

Font and font-size are controlled by the terminal emulator, not reliably by CLI applications.

However, the tool should support compact rendering so users can fit more tree content on screen.

## Recommended terminal setup

For dense tree views, recommend a narrow, readable monospace font at a small size.

Good options:

* JetBrains Mono
* JetBrains Mono NL
* Iosevka
* Iosevka Term
* Fira Code
* Hack
* IBM Plex Mono

Recommended size:

* normal use: 11–13 pt
* dense tree use: 9–11 pt
* very dense / large repo inspection: 8–10 pt

Avoid making font assumptions in code.

## Layout modes

Support layout density through CLI options instead of font control.

Target options:

```bash
lt .
lt . --compact
lt . --dense
lt . --no-meta
lt . --max-name-width 48
lt . --symbols ascii
```

## Display density modes

### Normal mode — default

Readable output with file names and recent status labels.

Example:

```text
repo/
├─ src/
│  ├─ main.py                       ● modified 2s ago
│  ├─ watcher.py                    ✚ new
│  └─ renderer.py                   ◌ unchanged
└─ README.md                        ◌ unchanged
```

### Compact mode

Less horizontal spacing. Shorter labels. Better for smaller terminals.

Example:

```text
repo/
├─ src/
│  ├─ main.py        ● 2s
│  ├─ watcher.py     ✚
│  └─ renderer.py    ◌
└─ README.md         ◌
```

### Dense mode

Minimal metadata. Best for fitting maximum tree content on screen.

Example:

```text
repo/
├─ src/
│  ├─ main.py ●
│  ├─ watcher.py ✚
│  └─ renderer.py ◌
└─ README.md ◌
```

## Implementation notes

* Do not set terminal font.
* Do not emit terminal-specific font escape sequences.
* Do not depend on Nerd Fonts.
* Do not use emoji as default symbols.
* Unicode symbols must be simple and broadly supported.
* ASCII mode must always be available.
* Add `--compact` and `--dense` before adding more complex layout features.
* Prefer truncating long names gracefully over wrapping lines.
* Avoid rendering lines wider than the terminal width when possible.
* Use terminal width detection where practical.
* Keep vertical density high by avoiding unnecessary blank lines.



## Implementation notes

* Keep a `TreeState` mapping absolute paths to nodes.
* Use filesystem events to update state.
* Re-scan only when needed.
* Use debounce around event bursts from editors/build tools.
* Do not block the render loop with expensive operations.
* If a directory is created, scan that subtree.
* If a directory is deleted, remove its subtree.
* If a path is moved, remove old path and add new path.
* Keep deleted nodes as temporary tombstones, then remove them after fade timeout.
* Prefer deterministic sorting: directories first, then files, alphabetically.
* Make depth handling predictable.
* Make ignore handling testable.

## Suggested structure

```text
livetree/
├─ pyproject.toml
├─ README.md
├─ AGENT.md
├─ livetree/
│  ├─ __init__.py
│  ├─ cli.py
│  ├─ scan.py
│  ├─ state.py
│  ├─ render.py
│  ├─ watch.py
│  ├─ ignore.py
│  └─ symbols.py
└─ tests/
   ├─ test_scan.py
   ├─ test_state.py
   ├─ test_ignore.py
   └─ test_symbols.py
```

## Testing

Use `pytest`.

Test:

* initial scan
* ignored folders
* `.ltignore` loading
* `.gitignore` loading
* create event state update
* modify event state update
* delete event tombstone
* move event state update
* fade behavior
* depth behavior
* symbol mode selection
* changed-only filtering

## Code style

* Python 3.10+
* Type hints
* Simple dataclasses
* No global mutable state except constants
* Prefer standard library unless a dependency is justified
* Small, focused modules
* Clear names
* No clever abstractions
* Usable MVP over theoretical architecture
