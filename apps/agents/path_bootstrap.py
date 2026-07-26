from __future__ import annotations

import sys
from pathlib import Path


def _module_points_to_src(module: object, src_dir: Path) -> bool:
    module_file = getattr(module, "__file__", None)
    if isinstance(module_file, str):
        try:
            if Path(module_file).resolve().is_relative_to(src_dir):
                return True
        except OSError:
            pass

    module_paths = getattr(module, "__path__", None)
    if module_paths is not None:
        for path in module_paths:
            try:
                if Path(path).resolve().is_relative_to(src_dir):
                    return True
            except OSError:
                continue

    return False


def ensure_src_on_path() -> None:
    src_dir = Path(__file__).resolve().parent / "src"
    src_path = str(src_dir)

    if src_dir.is_dir() and src_path not in sys.path:
        sys.path.insert(0, src_path)

    agents_module = sys.modules.get("agents")
    if agents_module is not None and not _module_points_to_src(agents_module, src_dir):
        for module_name in list(sys.modules):
            if module_name == "agents" or module_name.startswith("agents."):
                module = sys.modules.get(module_name)
                module_spec = getattr(module, "__spec__", None)
                if getattr(module_spec, "_initializing", False):
                    continue
                del sys.modules[module_name]
