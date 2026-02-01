from __future__ import annotations

import os
from dataclasses import asdict
from typing import Tuple

from dotenv import load_dotenv
from PIL import Image

from .client import GeminiClient
from .config import VisualizerConfig
from .prompts import (
    APPRAISAL_PROMPT,
    COMPOSITE_PROMPT,
    CRITIC_PROMPT,
    LOCATE_ARTWORK_PROMPT,
    ROOM_ENHANCE_PROMPT,
    ROOM_JUDGE_PROMPT,
)
from .types import AppraisalReport, ArtworkPlacement, CriticReport, RoomQualityReport

load_dotenv()
# print(os.getenv("GOOGLE_API_KEY"))


def _load_image(path: str) -> Image.Image:
    img = Image.open(path)
    # Normalize mode for safety
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    return img


def room_judge(
    client: GeminiClient, cfg: VisualizerConfig, room_img: Image.Image
) -> RoomQualityReport:
    print("Asking room judge: waiting")
    data = client.generate_json(
        cfg.gemini_text_model, ROOM_JUDGE_PROMPT, image=room_img
    )
    print("Room judge responded")
    verdict = data.get("verdict", "OK")
    reasons = data.get("reasons", "")
    if verdict not in ("OK", "NEEDS_ENHANCEMENT"):
        verdict = "OK"
    return RoomQualityReport(verdict=verdict, reasons=reasons)


def room_enhance(
    client: GeminiClient, cfg: VisualizerConfig, room_img: Image.Image
) -> Image.Image:
    return client.edit_image(cfg.gemini_image_model, ROOM_ENHANCE_PROMPT, room=room_img)


def composite_install(
    client: GeminiClient,
    cfg: VisualizerConfig,
    room_img: Image.Image,
    art_img: Image.Image,
    extra_fix_instruction: str | None = None,
) -> Image.Image:
    prompt = COMPOSITE_PROMPT
    if extra_fix_instruction:
        prompt = (
            prompt.strip()
            + "\n\nExtra instruction from critic:\n"
            + extra_fix_instruction.strip()
            + "\n"
        )
    return client.edit_image(cfg.gemini_image_model, prompt, room=room_img, art=art_img)


def locate_artwork(
    client: GeminiClient,
    cfg: VisualizerConfig,
    original_room_img: Image.Image,
    composite_img: Image.Image,
) -> ArtworkPlacement:
    data = client.generate_json(
        cfg.gemini_text_model,
        LOCATE_ARTWORK_PROMPT,
        images=[original_room_img, composite_img],
    )

    def clamp(v: float) -> float:
        return max(0.0, min(1.0, float(v)))

    return ArtworkPlacement(
        x=clamp(data.get("x", 0.0)),
        y=clamp(data.get("y", 0.0)),
        w=clamp(data.get("w", 1.0)),
        h=clamp(data.get("h", 1.0)),
        confidence=clamp(data.get("confidence", 0.5)),
        notes=str(data.get("notes", "")),
    )


def critic(
    client: GeminiClient, cfg: VisualizerConfig, composite_img: Image.Image
) -> CriticReport:
    data = client.generate_json(
        cfg.gemini_text_model, CRITIC_PROMPT, image=composite_img
    )
    verdict = data.get("verdict", "PASS")
    issues = data.get("issues", "")
    suggested_fix = data.get("suggested_fix", None)
    if verdict not in ("PASS", "RETRY"):
        verdict = "PASS"
    return CriticReport(verdict=verdict, issues=issues, suggested_fix=suggested_fix)


def appraise_installation(
    client: GeminiClient,
    cfg: VisualizerConfig,
    composite_img: Image.Image,
    placement: ArtworkPlacement,
) -> AppraisalReport:
    prompt = (
        APPRAISAL_PROMPT
        + f"\n\nBounding box: x={placement.x:.4f}, y={placement.y:.4f}, w={placement.w:.4f}, h={placement.h:.4f}\n"
    )
    data = client.generate_json(cfg.gemini_text_model, prompt, image=composite_img)
    print("Run appraisal: waiting")

    return AppraisalReport(
        suitable=bool(data.get("suitable", True)),
        summary=str(data.get("summary", "")),
        reasons=str(data.get("reasons", "")),
        suggestions=str(data.get("suggestions", "")),
    )


# Initial implementation to test pipeline helper functions
def run_pipeline_sequential(
    cfg: VisualizerConfig,
    room_path: str,
    art_path: str,
) -> Tuple[Image.Image, bool, int, RoomQualityReport, CriticReport]:
    """
    Returns: (final_image, used_enhancement, retries_used, room_quality, critic_report)
    """
    client = GeminiClient()

    room_img = _load_image(room_path)
    art_img = _load_image(art_path)

    room_quality = room_judge(client, cfg, room_img)

    used_enhancement = False
    if cfg.enhance_if_low_quality and room_quality.verdict == "NEEDS_ENHANCEMENT":
        room_img = room_enhance(client, cfg, room_img)
        used_enhancement = True

    # First composite
    out_img = composite_install(client, cfg, room_img, art_img)
    crit = critic(client, cfg, out_img)

    retries_used = 0
    while crit.verdict == "RETRY" and retries_used < cfg.max_retries:
        retries_used += 1
        fix = (
            crit.suggested_fix
            or "Improve realism of scale, perspective, and shadow. Keep it photorealistic."
        )
        out_img = composite_install(
            client, cfg, room_img, art_img, extra_fix_instruction=fix
        )
        crit = critic(client, cfg, out_img)

    return out_img, used_enhancement, retries_used, room_quality, crit
