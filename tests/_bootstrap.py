"""Expose the application sources to the offline test suite."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

SEARCH_ROOTS = (
    SRC,
    ROOT,
    ROOT / "native" / "kde",
    ROOT / "native" / "gnome",
    ROOT / "data",
    ROOT / "docs" / "releases",
    ROOT / "docs" / "planning",
    ROOT / "docs" / "design",
    ROOT / "docs" / "platform",
    ROOT / "docs",
)


def read_source(name: str) -> str:
    """Read a project file by name across the source and documentation trees."""
    for directory in SEARCH_ROOTS:
        path = directory / name
        if path.is_file():
            return path.read_text(encoding="utf-8")
    raise FileNotFoundError(name)
