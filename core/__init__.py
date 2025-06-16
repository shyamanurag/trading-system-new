"""Top-level core package.

This package exposes the modules located in `src/core` so that they can be
imported simply as `import core.models` etc. It ensures the `src` directory is
on `sys.path` when the package is imported so that unit-tests and application
code do not have to manipulate `PYTHONPATH` manually.
"""

import importlib
import pkgutil
import sys
from pathlib import Path

# Add the project `src` directory to sys.path so that `src.core` becomes
# importable regardless of the working directory or environment.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Lazily re-export the submodules inside ``src.core`` so callers can just do
# ``import core.models`` instead of ``from src.core import models``.
# We only eagerly import ``src.core`` itself so that attribute access works.
importlib.import_module("src.core")

# Anything that tries ``import core.models`` will trigger regular import
# machinery which now resolves to ``src.core.models`` thanks to the updated
# `sys.path`.
