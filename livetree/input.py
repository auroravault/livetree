from __future__ import annotations

import queue
import sys
import threading
from types import TracebackType

try:
    import termios
    import tty
    _TTY_AVAILABLE = True
except ImportError:
    _TTY_AVAILABLE = False  # non-Unix fallback: keyboard input silently disabled


CTRL_R = "\x12"

# Placeholder key constants for future git actions.
# Assignments TBD when git integration is implemented.
# _GIT_STAGE  = ???
# _GIT_COMMIT = ???
# _GIT_PUSH   = ???


class KeyboardListener:
    """Non-blocking single-keystroke reader.

    Uses cbreak mode so individual keys are delivered without waiting for Enter.
    Runs a daemon thread; the main loop calls drain() each iteration.
    No-ops silently when stdin is not a TTY (piped input, CI, --once).
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[str] = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._fd: int | None = None
        self._old_settings: list | None = None

    def __enter__(self) -> "KeyboardListener":
        if _TTY_AVAILABLE and sys.stdin.isatty():
            self._fd = sys.stdin.fileno()
            self._old_settings = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
            self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._fd is not None and self._old_settings is not None:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_settings)

    def _run(self) -> None:
        try:
            while True:
                ch = sys.stdin.read(1)
                if not ch:
                    break
                self._queue.put(ch)
        except Exception:
            pass

    def drain(self) -> list[str]:
        keys: list[str] = []
        while True:
            try:
                keys.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return keys
