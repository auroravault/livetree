# CLI Contract

Status legend used throughout this document:

| Symbol | Meaning |
|--------|---------|
| ✅ | Implemented — available in current release (0.1.2) |
| 🚧 | Planned — intended, design agreed, not yet coded |
| 💡 | Suggested — proposed additions, not yet decided |

---

## Synopsis

```
lt [PATH] [OPTIONS]
```

`PATH` defaults to `.` (current directory).

---

## Arguments

| Argument | Default | Status | Notes |
|----------|---------|--------|-------|
| `PATH` | `.` | ✅ | Directory to render. Must exist and be a directory. |

---

## Options — filtering

| Option | Short | Default | Status | Description |
|--------|-------|---------|--------|-------------|
| `--pattern PATTERN` | `-p` | — | ✅ | Glob filter. Only show matching files and their ancestor directories. Supports `*.py`, `tests`, `src/*.py`. |
| `--depth N` | `-d` | unlimited | ✅ | Maximum display depth. `0` shows root only. |
| `--changed` | — | false | ✅ | Show only paths with a non-UNCHANGED status (new, modified, deleted, moved, warning) and their ancestor directories. |
| `--since DURATION` | — | — | 🚧 | Combine with `--changed`. Only include paths whose last event arrived within the given window. Format: `10s`, `5m`, `1h`. |
| `--focus KIND` | — | — | 🚧 | Filter by a specific change kind rather than all changes. `KIND`: `new`, `modified`, `deleted`, `moved`. Can be repeated. |
| `--exclude PATTERN` | — | — | 💡 | Runtime glob exclude applied on top of `.gitignore`/`.ltignore`. Does not require editing ignore files. Repeatable: `--exclude "*.log" --exclude "dist"`. |

---

## Options — display

| Option | Short | Default | Status | Description |
|--------|-------|---------|--------|-------------|
| `--symbols MODE` | — | `unicode` | ✅ | Symbol set: `unicode`, `ascii`, `git`. |
| `--git` | — | false | ✅ | Shorthand for `--symbols git`. Does **not** query `git status`; only changes the symbol style. |
| `--compact` | — | false | ✅ | Shorter metadata labels and tighter spacing. Better for narrow terminals. |
| `--dense` | — | false | ✅ | Single-symbol status only, no label or age. Maximum tree density. |
| `--no-meta` | — | false | ✅ | Hide all status metadata. Renders name and connector only. |
| `--no-color` | — | false | ✅ | Disable terminal color output. |
| `--max-name-width N` | — | `72` | ✅ | Truncate long file/directory names to N characters. |
| `--sort MODE` | — | `name` | 💡 | Sort order within each directory. `name` (default, dirs-first alpha), `mtime` (most-recently-changed first), `status` (changed files first). |
| `--color-age` | — | false | 💡 | Progressively dim status markers as they age toward the fade threshold. Makes "freshness" visually obvious without needing to read the age label. |
| `--git-status` | — | false | 💡 | Query `git status --porcelain` and annotate tree entries with real git index state (staged, unstaged, untracked, ignored). Distinct from `--git`/`--symbols git`. Requires the watched path to be inside a git repository. |

---

## Options — timing

| Option | Default | Status | Description |
|--------|---------|--------|-------------|
| `--fade SECONDS` | `8.0` | ✅ | Seconds before change markers fade to UNCHANGED. Minimum 0.1. |
| `--debounce SECONDS` | `0.08` | ✅ | Seconds to wait after the first event in a burst before processing. Prevents flicker from editor save sequences. |
| `--tombstone SECONDS` | — | 💡 | Separate timeout for how long deleted paths remain visible as tombstones before being pruned. Currently inherits `--fade`. Useful for longer fade on deletions while keeping modify markers brief. |

---

## Options — behavior

| Option | Short | Default | Status | Description |
|--------|-------|---------|--------|-------------|
| `--once` | — | false | ✅ | Render the tree once and exit. No watcher is started. Useful for scripting or snapshots. |
| `--init-ignore` | `-i` | false | ✅ | Write a default `.ltignore` to PATH and exit. Does not start watching. |

---

## Implemented — full summary

The following is everything available today (0.1.2):

```
lt [PATH]
lt . --pattern "*.py"
lt . -p "*.py"
lt . --pattern tests
lt . --depth 3
lt . -d 3
lt . --changed
lt . --changed --pattern "*.py"
lt . --fade 30
lt . --symbols ascii
lt . --symbols unicode
lt . --symbols git
lt . --git
lt . --compact
lt . --dense
lt . --no-meta
lt . --no-color
lt . --max-name-width 48
lt . --once
lt . --debounce 0.2
lt -i
lt -i .
lt -i /path/to/folder
lt --help
```

All options above are combinable unless otherwise noted. `--git` is a shorthand for `--symbols git` and cannot conflict with it — if both are given, `--git` wins.

---

## Planned — not yet implemented

These are committed to the roadmap (in `agents.md` or prior design):

### `--since DURATION`

```
lt . --changed --since 5m
lt . --changed --since 30s
lt . --since 1h
```

Shows only paths whose last filesystem event arrived within the given duration window. Duration format: `Ns` (seconds), `Nm` (minutes), `Nh` (hours). Without `--changed`, also implies changed-only filtering (no point showing unchanged files if filtering by recency).

Implementation notes:
- Store event timestamp on each `TreeNode`
- Filter at render time alongside `changed_only`
- No new state machinery needed; just an additional predicate in `_ordered_nodes()`

### `--focus KIND`

```
lt . --focus new
lt . --focus modified
lt . --focus deleted
lt . --focus moved
lt . --focus new --focus modified
```

Subset of `--changed`: show only paths with a specific `ChangeKind`. Multiple `--focus` flags are OR'd. Allows a developer to watch only deletions or only new files during a refactor.

### Real git status integration

The `--git` / `--symbols git` flag currently changes symbol style only. The planned feature is a separate `--git-status` mode that runs `git status --porcelain -z` on startup and on file events, and annotates each tree entry with the actual git index state.

This is a **distinct implementation** from the existing `--git` flag. The two flags serve different purposes:

| Flag | What it does |
|------|-------------|
| `--git` / `--symbols git` | Changes symbol characters to look like `git status` output |
| `--git-status` (planned/💡) | Queries git and shows real index state |

---

## Suggested additions (💡)

These are my proposals — not committed, open for decision.

### `--exclude PATTERN`

Runtime exclude on top of the ignore chain, without touching ignore files:

```
lt . --exclude "*.log"
lt . --exclude "dist" --exclude "*.tmp"
```

Useful for one-off sessions where you don't want to pollute `.ltignore`. Gitignore-style pattern syntax (same as `.ltignore`). Applied after the ignore chain, before rendering.

### `--sort MODE`

```
lt . --sort name       # default — dirs first, then files, alphabetical
lt . --sort mtime      # most recently changed first within each directory
lt . --sort status     # changed files bubble to the top within each dir
```

`mtime` and `status` are useful when scanning large trees — the most active files stay near the top rather than wherever alphabetical order puts them.

### `--tombstone SECONDS`

```
lt . --fade 5 --tombstone 30
```

Separates the fade timeout (how long modify/new markers stay bright) from the tombstone timeout (how long deleted paths stay visible). Currently both are controlled by `--fade`, which means you can't have short modify markers and long deletion visibility at the same time.

### `--color-age`

```
lt . --color-age
```

Progressively dims the status marker color as the age approaches `--fade`. Makes freshness visible at a glance without reading the age label. Works well with `--compact` where space for the age string is limited.

### `--git-status`

See the planned section above. Flagged here as a proposal because the design (polling interval, conflict with watchdog events, handling of `.gitignore` overlap) needs a decision before implementation.

---

## Ignore chain

Evaluated in order; later entries override earlier ones:

1. Built-in defaults (`.git`, `node_modules`, `__pycache__`, `.venv`, etc.)
2. `.gitignore` in the watched directory
3. `.ltignore` in the watched directory
4. `--exclude` patterns (💡 — not yet implemented)

Use `lt -i [PATH]` to write the default built-in ignore list to a `.ltignore` file for editing.

---

## Symbol modes

### Unicode (default)

| Symbol | Meaning | Color |
|--------|---------|-------|
| `✚` | new | green (dim) |
| `●` | modified | yellow/straw (dim) |
| `✖` | deleted | magenta (dim) |
| `➜` | moved | gray (dim) |
| `⚠` | warning | red (dim) |
| `◌` | unchanged | default text |

### ASCII (`--symbols ascii`)

| Symbol | Meaning |
|--------|---------|
| `+` | new |
| `*` | modified |
| `-` | deleted |
| `>` | moved |
| `!` | warning |

### Git (`--symbols git` or `--git`)

| Symbol | Meaning |
|--------|---------|
| `A` | new (added) |
| `M` | modified |
| `D` | deleted |
| `R` | moved (renamed) |
| `??` | untracked / warning |

---

## Exit codes

| Code | Condition |
|------|-----------|
| `0` | Clean exit (Ctrl+C, `--once` completed, `--init-ignore` wrote file) |
| `1` | Bad argument (path not a directory, unknown symbol mode) |
| `2` | Typer/CLI parse error |

---

## Signals

| Signal | Behavior |
|--------|---------|
| `SIGINT` (Ctrl+C) | Stops watcher and Live display, prints `Stopped.`, exits 0 |
| `SIGTERM` | Not explicitly handled — Python default (exit, no cleanup message) 🚧 |
