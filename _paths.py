"""
Shared path resolution for autonovel scripts.

Scripts that live inside agents/<name>/ import this to find the repo root,
so they can access shared files (seed.txt, voice.md, engine.py, etc.)
regardless of their nesting depth.

Usage:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from _paths import REPO_ROOT as BASE_DIR
"""
from pathlib import Path


def _find_root() -> Path:
    """Walk up from this file to find the repo root (contains pyproject.toml)."""
    d = Path(__file__).resolve().parent
    while d != d.parent:
        if (d / "pyproject.toml").exists():
            return d
        d = d.parent
    raise RuntimeError("Could not find repo root (no pyproject.toml found)")


REPO_ROOT = _find_root()
