ROOM_JUDGE_PROMPT = """
You are judging whether a room photo is good enough for a photorealistic interior visualization edit.
Return ONLY a JSON object with keys:
- verdict: "OK" or "NEEDS_ENHANCEMENT"
- reasons: short explanation (1-3 sentences)

Consider: too dark, too noisy, motion blur, extreme compression artifacts, severe color cast.
If the image is acceptable, verdict must be "OK".
"""

ROOM_ENHANCE_PROMPT = """
Enhance this room photo for viewing while keeping it realistic.
Goals:
- reduce noise / compression artifacts
- correct obvious low-light (but avoid over-brightening)
- improve clarity modestly (avoid "HDR" look)
Do NOT change the room layout or add/remove objects.
Return only the enhanced image.
"""

COMPOSITE_PROMPT = """
You will receive two images:
(1) a room photo
(2) an artwork image

Goal: produce a photorealistic result where the artwork is installed on a suitable wall in the room.

Rules:
1) Choose a sensible wall location (avoid windows/doors/TV screens).
2) Scale the artwork realistically relative to furniture/wall space.
3) Align the artwork to the wall perspective (do not look "floating").
4) Add subtle realistic shadow/contact lighting.
5) If the artwork is a painting, add a simple tasteful frame that fits the room style.
6) Do not add extra paintings or duplicates.
Return only the final edited image.
"""

CRITIC_PROMPT = """
You are a strict visual critic for a room visualization composite.
You will see one image (the final composite).
Return ONLY a JSON object with keys:
- verdict: "PASS" or "RETRY"
- issues: short explanation (1-4 sentences)
- suggested_fix: (optional) a concise edit instruction to improve realism if verdict is RETRY

Fail (RETRY) if any of these are true:
- artwork scale is obviously wrong
- artwork is not aligned with wall perspective
- artwork looks pasted (no shadow / lighting mismatch)
- frame looks warped/unrealistic
- artwork placed on an implausible surface (window/door/ceiling/TV)
"""
