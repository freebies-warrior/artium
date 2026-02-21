from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from PIL import Image
import pytest

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
    cleaned: dict[str, Path] = {}

    room_local = tmp_path / "room.jpg"
    art_local = tmp_path / "art.png"
    room_local.write_bytes(b"room")
    art_local.write_bytes(b"art")

    monkeypatch.setattr(agent_service_module.tempfile, "mkdtemp", lambda: str(tmp_path / "job_tmp"))
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
    monkeypatch.setattr(
        agent_service_module,
        "cleanup_directory",
        lambda path: cleaned.update({"path": path}),
    )

    req = PreviewJobCommand(
        room_url="https://example.com/room.jpg",
        art_url="https://example.com/art.png",
        upload_image_url="https://example.com/upload.jpg",
        upload_image_key=None,
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
    assert cleaned["path"] == Path(tmp_path / "job_tmp")


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

    monkeypatch.setattr(agent_service_module.tempfile, "mkdtemp", lambda: str(tmp_path / "job_tmp"))
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
    monkeypatch.setattr(agent_service_module, "cleanup_directory", lambda path: None)

    req = PreviewJobCommand(
        room_url="https://example.com/room.jpg",
        art_url="https://example.com/art.png",
        upload_image_url="https://example.com/upload.jpg",
        upload_image_key=None,
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
        callback_url=None,
        metadata={"source": "unit-test"},
    )

    service.run_feature_extraction_job(req)

    assert len(callback.feature_updates) == 1
    update = callback.feature_updates[0]
    assert update["item_id"] == item_id
    assert update["feature_json"]["artwork_type"] == "painting"
    assert update["feature_json"]["valuation"] == {"price_range": {"mid": 1200}}
    assert "image_bytes" not in update["feature_json"]


def test_run_feature_extraction_job_failure_sends_safe_empty_payload(
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
        callback_url=None,
        metadata={"source": "unit-test"},
    )

    service.run_feature_extraction_job(req)

    assert callback.feature_updates == [{"item_id": item_id, "feature_json": {}}]
