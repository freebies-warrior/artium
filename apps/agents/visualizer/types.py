from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class VisualizerInputs:
    room_path: str
    art_path: str
    out_path: str


@dataclass
class RoomQualityReport:
    verdict: Literal["OK", "NEEDS_ENHANCEMENT"]
    reasons: str


@dataclass
class CriticReport:
    verdict: Literal["PASS", "RETRY"]
    issues: str
    suggested_fix: Optional[str] = None


@dataclass
class VisualizerResult:
    out_path: str
    used_enhancement: bool
    retries_used: int
    room_quality: RoomQualityReport
    critic: CriticReport
    placement: ArtworkPlacement
    appraisal: AppraisalReport


@dataclass
class ArtworkPlacement:
    # normalized [0,1] on final composite image
    x: float
    y: float
    w: float
    h: float
    confidence: float
    notes: str = ""


@dataclass
class AppraisalReport:
    suitable: bool
    summary: str
    reasons: str
    suggestions: str
