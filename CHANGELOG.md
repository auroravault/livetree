# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project uses Semantic Versioning.

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
