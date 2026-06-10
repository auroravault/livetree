# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project uses Semantic Versioning.

## [0.1.4] - 2026-06-10

### Added

- Startup splash: `◌  livetree  ·  by auroranode  ·  v0.1.4` printed above the
  tree on every run. Uses the UNCHANGED symbol from the active symbol mode,
  `magenta` for the tool name, `dim` for everything else. Respects `--no-color`
  and `--symbols ascii`/`git`.
- Keymap footer rendered below the live tree:
  `  ctrl+r  clear  ·  ctrl+c  exit` — dim, non-intrusive.
  Only shown in live mode (not with `--once`).

## [0.1.3] - 2026-06-10

### Added

- `Ctrl+R` clears all change markers immediately. Files with new/modified/moved
  status reset to UNCHANGED; deleted tombstones are pruned. Intended as the
  primary way to acknowledge changes rather than waiting for auto-fade.
- `livetree/input.py`: `KeyboardListener` — daemon thread that reads single
  keystrokes in cbreak mode alongside the watchdog event loop. No-ops silently
  when stdin is not a TTY (piped input, `--once`, CI).
- Structured key-action slot in the live loop (commented placeholders for future
  `git stage`, `git commit`, `git push` bindings).

### Changed

- Default `--fade` increased from `8.0` s to `99.0` s. With `Ctrl+R` available
  for explicit acknowledgement, the auto-fade timer is now a long-lived safety
  net rather than the primary UX.

## [0.1.2] - 2026-06-10

### Fixed

- `--pattern tests` now shows the matched directory and its entire subtree instead
  of returning `(empty)`. Directory-name patterns were silently excluded from
  matching because the filter only tested files.
- Pattern with no matches now always renders `(empty)`, even when `--changed` is
  also active (was: `(no changed files)` — misleading when the real reason was the
  pattern, not the absence of changes).
- `render_tree()` is now a pure read. `prune_faded()` was moved to the CLI event
  loop so rendering can no longer mutate state as a side-effect, making the
  function idempotent.

### Changed

- `walk()` converted from recursive to iterative (index-stack DFS). Eliminates any
  risk of `RecursionError` on deep trees, including directories injected at runtime
  by `_scan_subtree()` which ignores the `--depth` cap.
- `by_parent` grouping is now computed once per render frame and shared between
  ordering and connector-drawing (was computed twice with an independent sort,
  risking silent divergence in connector characters).
- `move()` uses a two-pass key-collection approach instead of copying the entire
  `nodes` dict on every rename/move event.
- `_CHILD_SORT_KEY` extracted as a module-level constant to guarantee ordering
  consistency across all sites that determine which child gets the `└─` connector.

## [0.1.1] - 2026-06-10

### Fixed

- Pattern filter (`lt . "*.py"`) no longer leaves empty parent directories visible in the tree.
  Filtering now happens at render time; directories with no matching file descendants are hidden.
- Directory moves now record each child node's own original path in `previous_path` instead of
  the source directory path.
- Removed destructive state mutation from pattern filtering. `state.nodes` is no longer modified
  by the filter; no `state.refresh()` is needed in the live-watch loop after events arrive.
- Added validation for glob patterns passed as the second positional argument; invalid patterns
  now produce a clear `BadParameter` error before the watcher starts.
- Clarified `--git` flag help text: it selects git-like status symbols only and does not query
  git status.
- Fixed double-dot typo in README (`"rust later.."` → `"rust later."`).
- Added `github` and `github.pub` to `.gitignore` to prevent accidental commit of SSH keys.

## [0.1.0] - 2026-06-09

### Added

- Initial project scaffold.
- Basic package metadata.
- Initial README.
- Initial versioning policy.
