# Versioning Policy

`livetree` uses Semantic Versioning 2.0.0.

Version format:

```text
MAJOR.MINOR.PATCH
```

While below `1.0.0`, the project is considered unstable.

During `0.x`, breaking CLI/API changes may happen in minor releases, but they must be documented in `CHANGELOG.md`.

Patch releases are for bug fixes and documentation corrections only.

Minor releases are for new CLI options, rendering behavior, ignore behavior, git integration, or changed defaults.

`1.0.0` means:

- Stable CLI command shape.
- Documented defaults.
- Reliable create/modify/delete/move handling.
- `.ltignore` support.
- Basic tests for scan/state/ignore/render behavior.

After `1.0.0`:

- MAJOR: breaking CLI/config/output contract changes.
- MINOR: backwards-compatible features.
- PATCH: backwards-compatible fixes.

Pre-release examples:

```text
0.1.0-alpha.1
0.1.0-beta.1
1.0.0-rc.1
```

