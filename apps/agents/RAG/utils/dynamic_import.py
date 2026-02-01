from __future__ import annotations

import importlib
from typing import Any, Callable


def import_from_path(path: str) -> Callable[..., Any]:
    """Import a callable from 'module.sub:func_name'."""
    if not path or ":" not in path:
        raise ValueError("import_path must look like 'module.submodule:function_name'")
    mod_name, attr = path.split(":", 1)
    mod = importlib.import_module(mod_name)
    fn = getattr(mod, attr, None)
    if fn is None or not callable(fn):
        raise ValueError(f"Object at {path} is not a callable")
    return fn
