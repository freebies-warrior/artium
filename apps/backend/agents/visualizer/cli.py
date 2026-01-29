from __future__ import annotations

import argparse
import json

from .runner import visualize_installation
from .config import VisualizerConfig


def main() -> None:
    arguments = argparse.ArgumentParser(description="Install artwork into a room (Gemini-only).")
    arguments.add_argument("--room", required=True, help="Path to room image (jpg/png).")
    arguments.add_argument("--art", required=True, help="Path to artwork image (jpg/png).")
    arguments.add_argument("--out", required=True, help="Path to output image (png recommended).")

    arguments.add_argument("--max-retries", type=int, default=None, help="Override retry count.")
    arguments.add_argument("--image-model", type=str, default=None, help="Override Gemini image model.")
    arguments.add_argument("--text-model", type=str, default=None, help="Override Gemini text model.")
    arguments.add_argument("--no-enhance", action="store_true", help="Disable room enhancement step.")

    args = arguments.parse_args()

    cfg = VisualizerConfig()
    if args.max_retries is not None:
        cfg.max_retries = args.max_retries
    if args.image_model is not None:
        cfg.gemini_image_model = args.image_model
    if args.text_model is not None:
        cfg.gemini_text_model = args.text_model
    if args.no_enhance:
        cfg.enhance_if_low_quality = False

    res = visualize_installation(args.room, args.art, args.out, cfg=cfg)

    # Print a compact JSON summary
    print(json.dumps({
        "out_path": res.out_path,
        "used_enhancement": res.used_enhancement,
        "retries_used": res.retries_used,
        "room_quality": {
            "verdict": res.room_quality.verdict,
            "reasons": res.room_quality.reasons,
        },
        "critic": {
            "verdict": res.critic.verdict,
            "issues": res.critic.issues,
            "suggested_fix": res.critic.suggested_fix,
        },
    }, indent=2))


if __name__ == "__main__":
    main()
