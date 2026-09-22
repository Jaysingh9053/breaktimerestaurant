from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


APP_FOLDER_NAME = "BreaktimeRestaurant"
PROJECT_ROOT = Path(__file__).resolve().parent
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_path(*parts: str) -> Path:
    return BUNDLE_ROOT.joinpath(*parts)


def data_dir() -> Path:
    if not is_frozen():
        target = PROJECT_ROOT
    else:
        base_dir = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        target = base_dir / APP_FOLDER_NAME
    target.mkdir(parents=True, exist_ok=True)
    return target


def database_path(filename: str = "breaktime_restaurant.db") -> Path:
    target = data_dir() / filename
    if is_frozen() and not target.exists():
        bundled_copy = resource_path(filename)
        if bundled_copy.exists():
            shutil.copy2(bundled_copy, target)
    return target
