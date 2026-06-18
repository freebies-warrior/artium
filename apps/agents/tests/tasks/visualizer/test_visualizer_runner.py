from PIL import Image

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

from agents.tasks.visualizer.config import VisualizerConfig
from agents.tasks.visualizer.types import CriticReport, RoomQualityReport
import agents.tasks.visualizer.runner as runner


class _DummySettings:
    VISUALIZER_USE_LANGGRAPH = False


def _cfg() -> VisualizerConfig:
    return VisualizerConfig(
        gemini_image_model="gemini-image-test",
        gemini_text_model="gemini-text-test",
        max_retries=1,
        enhance_if_low_quality=True,
    )


def test_visualize_installation_happy_path_with_stubbed_pipeline(monkeypatch) -> None:
    out_img = Image.new("RGB", (16, 16))
    room_quality = RoomQualityReport(verdict="OK", reasons="looks good")
    critic_report = CriticReport(verdict="PASS", issues="none", suggested_fix=None)

    monkeypatch.setattr(runner, "get_settings", lambda: _DummySettings())
    monkeypatch.setattr(runner, "_save_image", lambda _img, _path: None)

    def fake_run_pipeline_sequential(_cfg, room_path: str, art_path: str):
        assert room_path == "x"
        assert art_path == "y"
        return out_img, True, 2, room_quality, critic_report

    monkeypatch.setattr(runner, "run_pipeline_sequential", fake_run_pipeline_sequential)

    result = runner.visualize_installation("x", "y", "z", cfg=_cfg())

    assert result.out_path is None
    assert result.used_enhancement is True
    assert result.retries_used == 2
    assert result.room_quality is room_quality
    assert result.critic is critic_report
    assert result.placement is None
    assert result.appraisal is None
