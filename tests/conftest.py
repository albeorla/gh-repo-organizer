"""Pytest configuration that ensures the *src* layout is importable.

Running the test-suite directly from the repository root (without installing
the package in editable mode via ``pip install -e .``) means that the Python
import machinery cannot find the ``repo_organizer`` package because it lives
inside the *src/* directory.

This small helper adds the *src* directory to ``sys.path`` **once** at session
start so that `import repo_organizer` works in all test modules.  The code is
no-op when the package is already importable (e.g. in CI where the project is
installed).
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Insert *src* at the beginning of ``sys.path`` to give it precedence over any
# globally installed version of the package.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
