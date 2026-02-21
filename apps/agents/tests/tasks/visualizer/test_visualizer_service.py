from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from PIL import Image
import pytest

from agents.tasks.visualizer.config import VisualizerConfig
import agents.tasks.visualizer.service as visualizer_service


def _cfg() -> VisualizerConfig:
    return VisualizerConfig(
        gemini_image_model="gemini-image-test",
        gemini_text_model="gemini-text-test",
        max_retries=1,
        enhance_if_low_quality=True,
    )


def test_load_preview_images_returns_two_images(tmp_path: Path) -> None:
    room_path = tmp_path / "room.jpg"
    art_path = tmp_path / "art.jpg"
    Image.new("RGB", (12, 12), "white").save(room_path)
    Image.new("RGB", (10, 10), "black").save(art_path)

    room_img, art_img = visualizer_service.load_preview_images(str(room_path), str(art_path))

    assert room_img.size == (12, 12)
    assert art_img.size == (10, 10)


def test_run_preview_with_graph_happy_path_returns_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    room_img = Image.new("RGB", (8, 8))
    art_img = Image.new("RGB", (8, 8))
    out_img = Image.new("RGB", (16, 16))
    saved: dict[str, object] = {}

    class DummyGraph:
        def __init__(self):
            self.last_state = None

        def invoke(self, state):
            self.last_state = state
            return {"out_img": out_img, "appraisal": SimpleNamespace(summary="looks good")}

    graph = DummyGraph()
    dummy_client = object()

    monkeypatch.setattr(
        visualizer_service, "is_valid_artwork_and_room", lambda *_: (True, True, True)
    )
    monkeypatch.setattr(
        visualizer_service,
        "_save_image",
        lambda image, out_path: saved.update({"image": image, "path": out_path}),
    )

    summary = visualizer_service.run_preview_with_graph(
        cfg=_cfg(),
        room_img=room_img,
        art_img=art_img,
        upload_image_url="https://example.com/upload.jpg",
        visualizer_client=dummy_client,  # type: ignore[arg-type]
        visualizer_graph=graph,
    )

    assert summary == "looks good"
    assert graph.last_state["client"] is dummy_client
    assert graph.last_state["room_img"] is room_img
    assert graph.last_state["art_img"] is art_img
    assert saved["image"] is out_img
    assert saved["path"] == "https://example.com/upload.jpg"


@pytest.mark.parametrize(
    ("validation_result", "expected_message"),
    [
        (
            (False, False, False),
            "First image is not recognized as an artwork and second image is not recognized as a room.",
        ),
        ((False, False, True), "First image is not recognized as an artwork."),
        ((False, True, False), "Second image is not recognized as a room."),
    ],
)
def test_run_preview_with_graph_invalid_inputs_keep_exact_error_messages(
    monkeypatch: pytest.MonkeyPatch,
    validation_result: tuple[bool, bool | None, bool | None],
    expected_message: str,
) -> None:
    monkeypatch.setattr(
        visualizer_service,
        "is_valid_artwork_and_room",
        lambda *_: validation_result,
    )
    monkeypatch.setattr(
        visualizer_service,
        "_save_image",
        lambda *_: (_ for _ in ()).throw(AssertionError("_save_image should not be called")),
    )

    with pytest.raises(ValueError) as exc:
        visualizer_service.run_preview_with_graph(
            cfg=_cfg(),
            room_img=Image.new("RGB", (8, 8)),
            art_img=Image.new("RGB", (8, 8)),
            upload_image_url="https://example.com/upload.jpg",
            visualizer_client=object(),  # type: ignore[arg-type]
            visualizer_graph=SimpleNamespace(
                invoke=lambda *_: (_ for _ in ()).throw(
                    AssertionError("invoke should not be called")
                )
            ),
        )

    assert str(exc.value) == expected_message
