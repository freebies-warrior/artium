from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

from path_bootstrap import _module_points_to_src


def test_module_points_to_src_requires_a_real_subpath(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    inside_file = SimpleNamespace(__file__=str(src_dir / "agents.py"))
    inside_path = SimpleNamespace(__path__=[str(src_dir / "agents")])
    sibling_file = SimpleNamespace(__file__=str(tmp_path / "src2" / "agents.py"))
    sibling_path = SimpleNamespace(__path__=[str(tmp_path / "src2" / "agents")])

    assert _module_points_to_src(inside_file, src_dir)
    assert _module_points_to_src(inside_path, src_dir)
    assert not _module_points_to_src(sibling_file, src_dir)
    assert not _module_points_to_src(sibling_path, src_dir)
