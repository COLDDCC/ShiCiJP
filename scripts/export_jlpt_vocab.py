#!/usr/bin/env python3
"""Export via the shared content build so translations and labels cannot regress."""
import tempfile
from pathlib import Path
from build_jlpt_content import build_content
from build_jlpt_db import ROOT


def export(destination=None):
    target = Path(destination) if destination else ROOT / "public/jlpt/vocabulary/data"
    with tempfile.TemporaryDirectory() as tmp:
        build_content(Path(tmp) / "jlpt.sqlite", target)


if __name__ == "__main__":
    export()
