from __future__ import annotations

from typing import Any, Dict, List, Sequence


def _get_by_path(d: Dict[str, Any], path: str) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


class NumericFeatureEmbedder:
    def __init__(self, feature_map: Dict[str, List[str]]) -> None:
        self.feature_map = feature_map

    def dimension_for_type(self, artwork_type: str) -> int:
        keys = self.feature_map.get(artwork_type, [])
        return len(keys)

    def build_vector(self, artwork_type: str, vision_features: Dict[str, Any]) -> List[float]:
        keys = self.feature_map.get(artwork_type)
        if not keys:
            raise ValueError(f"No feature_map configured for artwork_type={artwork_type}")
        vec: List[float] = []
        for k in keys:
            v = _get_by_path(vision_features, k)
            try:
                vec.append(float(v) if v is not None else 0.0)
            except Exception:
                vec.append(0.0)
        return vec
