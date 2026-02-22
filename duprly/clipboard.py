from __future__ import annotations

import platform
import subprocess
from typing import Tuple


def copy_text(text: str) -> Tuple[bool, str, str]:
    """
    Try to copy text to clipboard.
    Returns (ok, mechanism, reason).
    """
    system = platform.system().lower()
    candidates: list[list[str]] = []

    if system == "darwin":
        candidates = [["pbcopy"]]
    elif system == "windows":
        candidates = [["clip"]]
    else:
        candidates = [["wl-copy"], ["xclip", "-selection", "clipboard"]]

    last_reason = ""
    for cmd in candidates:
        try:
            subprocess.run(
                cmd,
                input=text,
                text=True,
                check=True,
                capture_output=True,
            )
            return True, cmd[0], ""
        except FileNotFoundError:
            last_reason = f"{cmd[0]} not found"
        except subprocess.CalledProcessError as err:
            stderr = (err.stderr or "").strip()
            if stderr:
                last_reason = stderr
            else:
                last_reason = f"{cmd[0]} failed with exit code {err.returncode}"
        except Exception as err:  # pragma: no cover - defensive
            last_reason = str(err)

    if not last_reason:
        last_reason = "No clipboard command available"
    return False, "none", last_reason
