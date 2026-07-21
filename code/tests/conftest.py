"""Make ``import fuxi`` work no matter where pytest is invoked from.

The package lives in ``<repo>/code/fuxi`` and ``verify_all.py`` sits next to it
in ``<repo>/code``. This file puts ``<repo>/code`` on ``sys.path`` so the suite
runs identically from the repository root, from ``code/`` or from ``code/tests``.
"""

from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
