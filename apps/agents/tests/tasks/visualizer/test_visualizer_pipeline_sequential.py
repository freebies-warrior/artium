from PIL import Image

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

from agents.tasks.visualizer.config import VisualizerConfig
from agents.tasks.visualizer.pipeline_sequential import critic, locate_artwork, room_judge


class DummyClient:
    def __init__(self, payload: dict):
        self.payload = payload

    def generate_json(self, *_args, **_kwargs) -> dict:
        return self.payload


def _cfg() -> VisualizerConfig:
    return VisualizerConfig(
        gemini_image_model="gemini-image-test",
        gemini_text_model="gemini-text-test",
        max_retries=1,
        enhance_if_low_quality=True,
    )


def test_room_judge_defaults_invalid_verdict_to_ok() -> None:
    report = room_judge(
        DummyClient({"verdict": "INVALID", "reasons": "bad verdict"}),
        _cfg(),
        Image.new("RGB", (8, 8)),
    )

    assert report.verdict == "OK"
    assert report.reasons == "bad verdict"


def test_critic_defaults_invalid_verdict_to_pass() -> None:
    report = critic(
        DummyClient({"verdict": "INVALID", "issues": "bad verdict", "suggested_fix": "fix"}),
        _cfg(),
        Image.new("RGB", (8, 8)),
    )

    assert report.verdict == "PASS"
    assert report.issues == "bad verdict"
    assert report.suggested_fix == "fix"


def test_locate_artwork_clamps_values_into_unit_interval() -> None:
    placement = locate_artwork(
        DummyClient(
            {
                "x": -2.0,
                "y": 0.25,
                "w": 1.5,
                "h": 99.0,
                "confidence": -0.01,
                "notes": "stubbed",
            }
        ),
        _cfg(),
        Image.new("RGB", (8, 8)),
        Image.new("RGB", (8, 8)),
    )

    assert placement.x == 0.0
    assert placement.y == 0.25
    assert placement.w == 1.0
    assert placement.h == 1.0
    assert placement.confidence == 0.0
    assert placement.notes == "stubbed"
