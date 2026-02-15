from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional, Tuple

from openai import OpenAI


DEFAULT_BASE_URL = "https://api.manus.im"


class ManusCanonicalizer:
    """Canonicalize feature_state into a strict JSON schema using Manus.

    Manus runs asynchronously via the Responses API, so we poll until completion.
    See Manus OpenAI SDK compatibility docs: https://open.manus.im/docs/openai-compatibility
    """

    def __init__(
        self,
        api_key_header: str,
        base_url: str = DEFAULT_BASE_URL,
        agent_profile: str = "manus-1.6",
        task_mode: str = "agent",
        poll_interval_s: float = 3.0,
        timeout_s: float = 120.0,
    ) -> None:
        # Manus ignores OpenAI api_key and reads the real key from API_KEY header.
        self.client = OpenAI(
            base_url=base_url,
            api_key="**",
            default_headers={"API_KEY": api_key_header},
        )
        self.agent_profile = agent_profile
        self.task_mode = task_mode
        self.poll_interval_s = poll_interval_s
        self.timeout_s = timeout_s

    def canonicalize(
        self,
        feature_state: Dict[str, Any],
        *,
        schema_version: str,
        type_specific_instructions: str,
    ) -> Dict[str, Any]:
        prompt = (
            "You are a strict data normalizer.\n"
            "Convert the given feature_state JSON into a canonical JSON object with:\n"
            "- schema_version: string\n"
            "- type: 'painting' or 'sculpture'\n"
            "- signals: object of numeric features (floats)\n"
            "- notes: object of short strings (<=250 chars each)\n"
            "Do not include market_features. Do not include any URLs.\n\n"
            f"schema_version: {schema_version}\n"
            f"{type_specific_instructions}\n\n"
            "feature_state JSON:\n" + json.dumps(feature_state, ensure_ascii=False)
        )

        resp = self.client.responses.create(
            input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
            extra_body={"task_mode": self.task_mode, "agent_profile": self.agent_profile},
        )

        task_id = resp.id
        start = time.time()
        while True:
            cur = self.client.responses.retrieve(response_id=task_id)
            if cur.status != "running":
                break
            if time.time() - start > self.timeout_s:
                raise TimeoutError(
                    f"Manus canonicalization timed out after {self.timeout_s}s (task={task_id})"
                )
            time.sleep(self.poll_interval_s)

        # Extract the last assistant text and parse JSON
        text = _extract_assistant_text(cur)
        obj = json.loads(text)
        if not isinstance(obj, dict):
            raise ValueError("Manus returned non-dict JSON")
        return obj


def _extract_assistant_text(response_obj: Any) -> str:
    # The OpenAI client returns objects; we rely on dict-like access via model_dump if available.
    try:
        data = response_obj.model_dump()
    except Exception:
        data = response_obj  # type: ignore[assignment]

    outputs = data.get("output") or []
    # Find last assistant message with text
    last_text: Optional[str] = None
    for msg in outputs:
        if msg.get("role") != "assistant":
            continue
        for part in msg.get("content", []):
            if "text" in part:
                last_text = part["text"]
    if not last_text:
        raise ValueError("No assistant text found in Manus response output")
    return last_text.strip()
