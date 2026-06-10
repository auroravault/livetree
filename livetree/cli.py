from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live

from .ignore import init_ltignore, load_ignore
from .input import CTRL_R, KeyboardListener
from .render import render_tree
from .state import TreeState
from .watch import LiveWatcher, apply_events, drain_events


HELP = """Render a live terminal directory tree.

Ignore behavior:

livetree loads default noisy ignores, then .gitignore, then .ltignore from the selected workdir.
Use lt -i [PATH] to create a default .ltignore in that workdir.
Patterns use gitignore-style matching.
"""

app = typer.Typer(help=HELP, no_args_is_help=False)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    path: Path = typer.Argument(Path("."), help="Directory to render."),
    pattern: Optional[str] = typer.Option(None, "--pattern", "-p", help="Glob pattern to focus, e.g. '*.py'."),
    depth: Optional[int] = typer.Option(None, "--depth", "-d", min=0, help="Maximum tree depth."),
    changed: bool = typer.Option(False, "--changed", help="Show only changed paths."),
    git: bool = typer.Option(False, "--git", help="Use git-like status symbols (shorthand for --symbols git; does not query git status)."),
    fade: float = typer.Option(99.0, "--fade", min=0.1, help="Seconds before change markers fade. Use Ctrl+R to clear immediately."),
    init_ignore: bool = typer.Option(False, "--init-ignore", "-i", help="Create a default .ltignore in PATH and exit."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable terminal color."),
    symbols: str = typer.Option("unicode", "--symbols", help="Symbol mode: unicode, ascii, git."),
    compact: bool = typer.Option(False, "--compact", help="Use compact metadata."),
    dense: bool = typer.Option(False, "--dense", help="Use dense single-symbol metadata."),
    no_meta: bool = typer.Option(False, "--no-meta", help="Hide status metadata."),
    max_name_width: int = typer.Option(72, "--max-name-width", min=8, help="Truncate long names."),
    once: bool = typer.Option(False, "--once", help="Render once and exit."),
    debounce: float = typer.Option(0.08, "--debounce", min=0.0, help="Seconds to debounce event bursts."),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    root = path.resolve()
    console = Console(no_color=no_color)
    if init_ignore:
        created = init_ltignore(root)
        console.print(f"Wrote {created}")
        return
    if not root.exists() or not root.is_dir():
        raise typer.BadParameter(f"{root} is not a directory")
    if git:
        symbols = "git"
    if symbols not in {"unicode", "ascii", "git"}:
        raise typer.BadParameter("symbols must be one of: unicode, ascii, git")
    ignore = load_ignore(root)
    state = TreeState.from_scan(root, ignore, depth=depth, fade_seconds=fade)
    render_kwargs = {
        "symbols": symbols,
        "changed_only": changed,
        "pattern": pattern,
        "compact": compact,
        "dense": dense,
        "no_meta": no_meta,
        "max_name_width": max_name_width,
    }
    if once:
        state.prune_faded()
        console.print(render_tree(state, **render_kwargs))
        return
    try:
        state.prune_faded()
        with Live(render_tree(state, **render_kwargs), console=console, refresh_per_second=8, screen=False) as live:
            with LiveWatcher(root) as watcher:
                with KeyboardListener() as kb:
                    while True:
                        events = drain_events(watcher.events, debounce)
                        keys = kb.drain()

                        if events:
                            apply_events(state, events)

                        # --- User actions ---
                        for key in keys:
                            if key == CTRL_R:
                                state.clear_changes()
                            # Future git actions (keys TBD):
                            # elif key == _GIT_STAGE:
                            #     pass
                            # elif key == _GIT_COMMIT:
                            #     pass
                            # elif key == _GIT_PUSH:
                            #     pass

                        state.prune_faded()
                        live.update(render_tree(state, **render_kwargs))
    except KeyboardInterrupt:
        console.print("\nStopped.", style="dim")


if __name__ == "__main__":
    app()
