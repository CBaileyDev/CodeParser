from __future__ import annotations

from pathlib import Path

try:  # pragma: no cover - import guard
    from detect_secrets.core.scan import scan_file
except ImportError:  # pragma: no cover
    scan_file = None  # type: ignore


def scan_path_for_secrets(path: Path) -> int:
    """Return a count of potential secrets in the given file.

    If detect-secrets is not installed or scanning fails, this returns 0.
    The intent is to provide a coarse signal without ever failing the
    main CodeParser run.
    """

    if scan_file is None:
        return 0

    try:
        count = 0
        for _secret in scan_file(str(path)):
            count += 1
        return count
    except Exception:
        # Best-effort only; never fail the main process.
        return 0
