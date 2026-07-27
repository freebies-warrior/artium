from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from PIL import Image
import pytest

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

import agents.api.service as agent_service_module
from agents.api.commands import FeatureExtractionJobCommand, PreviewJobCommand
from agents.api.service import AgentService
from agents.core.types import JobStatus


class RecordingCallbackClient:
    def __init__(self) -> None:
        self.visualization_updates: list[dict[str, Any]] = []
        self.feature_updates: list[dict[str, Any]] = []

    def update_visualization(
        self,
        job_id: str,
        status: str,
        result_description: str | None,
        error_message: str | None,
    ) -> None:
        self.visualization_updates.append(
            {
                "job_id": job_id,
                "status": status,
                "result_description": result_description,
                "error_message": error_message,
            }
        )

    def update_item_features(self, item_id: Any, feature_json: dict[str, Any]) -> None:
        self.feature_updates.append({"item_id": item_id, "feature_json": feature_json})


def test_run_preview_job_success_sends_succeeded_callback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    callback = RecordingCallbackClient()
    service = AgentService(callback_client=callback)

    room_local = tmp_path / "room.jpg"
    art_local = tmp_path / "art.png"
    room_local.write_bytes(b"room")
    art_local.write_bytes(b"art")

    monkeypatch.setattr(
        agent_service_module,
        "download_to_temp_file",
        lambda url, *, suffix, timeout: room_local if suffix == ".jpg" else art_local,
    )
    monkeypatch.setattr(
        agent_service_module,
        "load_preview_images",
        lambda room_path, art_path: (Image.new("RGB", (4, 4)), Image.new("RGB", (3, 3))),
    )
    monkeypatch.setattr(
        service,
        "run_visualizer_preview",
        lambda **kwargs: "preview-complete",
    )

    req = PreviewJobCommand(
        room_url="https://example.com/room.jpg",
        art_url="https://example.com/art.png",
        upload_image_url="https://example.com/upload.jpg",
        job_id="job-123",
    )

    service.run_preview_job(req)

    assert callback.visualization_updates == [
        {
            "job_id": "job-123",
            "status": JobStatus.SUCCEEDED,
            "result_description": "preview-complete",
            "error_message": None,
        }
    ]
    assert not room_local.exists()
    assert not art_local.exists()


def test_run_preview_job_failure_sends_failed_callback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    callback = RecordingCallbackClient()
    service = AgentService(callback_client=callback)

    room_local = tmp_path / "room.jpg"
    art_local = tmp_path / "art.png"
    room_local.write_bytes(b"room")
    art_local.write_bytes(b"art")

    monkeypatch.setattr(
        agent_service_module,
        "download_to_temp_file",
        lambda url, *, suffix, timeout: room_local if suffix == ".jpg" else art_local,
    )
    monkeypatch.setattr(
        agent_service_module,
        "load_preview_images",
        lambda room_path, art_path: (Image.new("RGB", (4, 4)), Image.new("RGB", (3, 3))),
    )

    def raise_failure(**kwargs):
        raise RuntimeError("preview pipeline failed")

    monkeypatch.setattr(service, "run_visualizer_preview", raise_failure)

    req = PreviewJobCommand(
        room_url="https://example.com/room.jpg",
        art_url="https://example.com/art.png",
        upload_image_url="https://example.com/upload.jpg",
        job_id="job-456",
    )

    service.run_preview_job(req)

    assert callback.visualization_updates == [
        {
            "job_id": "job-456",
            "status": JobStatus.FAILED,
            "result_description": None,
            "error_message": "preview pipeline failed",
        }
    ]
    assert not room_local.exists()
    assert not art_local.exists()


def test_run_preview_job_download_failure_sends_failed_callback_and_cleans_first_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    callback = RecordingCallbackClient()
    service = AgentService(callback_client=callback)

    room_local = tmp_path / "room.jpg"
    room_local.write_bytes(b"room")

    call_count = {"count": 0}

    def download_side_effect(url, *, suffix, timeout):  # noqa: ANN001
        call_count["count"] += 1
        if call_count["count"] == 1:
            return room_local
        raise RuntimeError("download failed")

    monkeypatch.setattr(agent_service_module, "download_to_temp_file", download_side_effect)

    req = PreviewJobCommand(
        room_url="https://example.com/room.jpg",
        art_url="https://example.com/art.png",
        upload_image_url="https://example.com/upload.jpg",
        job_id="job-789",
    )

    service.run_preview_job(req)

    assert callback.visualization_updates == [
        {
            "job_id": "job-789",
            "status": JobStatus.FAILED,
            "result_description": None,
            "error_message": "download failed",
        }
    ]
    assert not room_local.exists()


def test_run_preview_job_decode_failure_sends_failed_callback_and_cleans_downloads(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    callback = RecordingCallbackClient()
    service = AgentService(callback_client=callback)

    room_local = tmp_path / "room.jpg"
    art_local = tmp_path / "art.png"
    room_local.write_bytes(b"room")
    art_local.write_bytes(b"art")

    monkeypatch.setattr(
        agent_service_module,
        "download_to_temp_file",
        lambda url, *, suffix, timeout: room_local if suffix == ".jpg" else art_local,
    )

    def raise_decode_error(room_path, art_path):  # noqa: ANN001
        raise RuntimeError("decode failed")

    monkeypatch.setattr(agent_service_module, "load_preview_images", raise_decode_error)

    req = PreviewJobCommand(
        room_url="https://example.com/room.jpg",
        art_url="https://example.com/art.png",
        upload_image_url="https://example.com/upload.jpg",
        job_id="job-790",
    )

    service.run_preview_job(req)

    assert callback.visualization_updates == [
        {
            "job_id": "job-790",
            "status": JobStatus.FAILED,
            "result_description": None,
            "error_message": "decode failed",
        }
    ]
    assert not room_local.exists()
    assert not art_local.exists()


def test_run_feature_extraction_job_success_sends_combined_features(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    callback = RecordingCallbackClient()
    service = AgentService(callback_client=callback)

    initial_state = {"images": ["bytes"]}
    metadata = {"seller": "abc"}
    image_bytes = b"img-bytes"

    monkeypatch.setattr(
        agent_service_module,
        "build_initial_feature_state",
        lambda *, image_urls, item_id, metadata: (initial_state, metadata, image_bytes),
    )
    monkeypatch.setattr(
        service,
        "extract_features",
        lambda state: {
            "artwork_type": "painting",
            "vision_features": {"color": "red"},
            "image_bytes": b"result-bytes",
            "errors": [],
        },
    )
    monkeypatch.setattr(
        service,
        "valuate_artwork",
        lambda state: {"price_range": {"mid": 1200}},
    )

    item_id = uuid4()
    req = FeatureExtractionJobCommand(
        item_id=item_id,
        image_keys=("img1",),
        image_get_urls=("https://example.com/images/1.jpg",),
        metadata={"source": "unit-test"},
    )

    service.run_feature_extraction_job(req)

    assert len(callback.feature_updates) == 1
    update = callback.feature_updates[0]
    assert update["item_id"] == item_id
    assert update["feature_json"]["artwork_type"] == "painting"
    assert update["feature_json"]["valuation"] == {"price_range": {"mid": 1200}}
    assert "image_bytes" not in update["feature_json"]


def test_run_feature_extraction_job_failure_skips_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    callback = RecordingCallbackClient()
    service = AgentService(callback_client=callback)

    def raise_failure(*, image_urls, item_id, metadata):
        raise RuntimeError("feature extraction failed before graph invoke")

    monkeypatch.setattr(agent_service_module, "build_initial_feature_state", raise_failure)

    item_id = uuid4()
    req = FeatureExtractionJobCommand(
        item_id=item_id,
        image_keys=("img1",),
        image_get_urls=("https://example.com/images/1.jpg",),
        metadata={"source": "unit-test"},
    )

    service.run_feature_extraction_job(req)

    assert callback.feature_updates == []


@pytest.mark.parametrize("artwork_type_alias", ["NOT AN ARTWORK", "not-artwork"])
def test_run_feature_extraction_job_skips_valuation_for_not_artwork_aliases(
    monkeypatch: pytest.MonkeyPatch,
    artwork_type_alias: str,
) -> None:
    callback = RecordingCallbackClient()
    service = AgentService(callback_client=callback)
    called = {"valuate": False}

    monkeypatch.setattr(
        agent_service_module,
        "build_initial_feature_state",
        lambda *, image_urls, item_id, metadata: ({"images": ["bytes"]}, {"seller": "abc"}, b"img"),
    )
    monkeypatch.setattr(
        service,
        "extract_features",
        lambda state: {
            "artwork_type": artwork_type_alias,
            "vision_features": {"style": "abstract"},
            "image_bytes": b"result-bytes",
            "errors": [],
        },
    )

    def _fail_if_called(state):
        called["valuate"] = True
        raise AssertionError("valuate_artwork should not be called for not-artwork aliases")

    monkeypatch.setattr(service, "valuate_artwork", _fail_if_called)

    item_id = uuid4()
    req = FeatureExtractionJobCommand(
        item_id=item_id,
        image_keys=("img1",),
        image_get_urls=("https://example.com/images/1.jpg",),
        metadata={"source": "unit-test"},
    )

    service.run_feature_extraction_job(req)

    assert called["valuate"] is False
    assert len(callback.feature_updates) == 1
    feature_json = callback.feature_updates[0]["feature_json"]
    assert feature_json["artwork_type"] == artwork_type_alias
    assert feature_json["valuation"] is None
    assert "image_bytes" not in feature_json
