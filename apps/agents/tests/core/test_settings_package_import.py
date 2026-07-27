from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_settings_imports_outside_repo(tmp_path: Path) -> None:
    wheel_root = tmp_path / "wheel"
    package_root = wheel_root / "agents"
    shutil.copytree(Path(__file__).resolve().parents[2] / "src" / "agents", package_root)

    config_path = package_root / "providers" / "rag" / "config.yaml"
    config_path.write_text("embedding_mode: image\n", encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(wheel_root)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from agents.core.settings import AGENTS_ROOT\n"
                "from agents.providers.rag.settings import load_config\n"
                "cfg = load_config()\n"
                "print(AGENTS_ROOT)\n"
                "print(cfg.path)\n"
                "print(cfg.embedding_mode)\n"
            ),
        ],
        cwd=wheel_root,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    lines = result.stdout.splitlines()
    assert Path(lines[0]) == package_root
    assert Path(lines[1]) == config_path
    assert lines[2] == "image"
