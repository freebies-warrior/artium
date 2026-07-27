from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

from agents.tasks.visualizer import prompts


PROMPT_NAMES = [
    "ROOM_JUDGE_PROMPT",
    "ROOM_ENHANCE_PROMPT",
    "COMPOSITE_PROMPT",
    "CRITIC_PROMPT",
    "LOCATE_ARTWORK_PROMPT",
    "APPRAISAL_PROMPT",
]

JSON_PROMPT_NAMES = [
    "ROOM_JUDGE_PROMPT",
    "CRITIC_PROMPT",
    "LOCATE_ARTWORK_PROMPT",
    "APPRAISAL_PROMPT",
]


def test_visualizer_prompts_are_non_empty() -> None:
    for name in PROMPT_NAMES:
        value = getattr(prompts, name)
        assert isinstance(value, str)
        assert value.strip()


def test_json_prompts_require_json_only_output() -> None:
    for name in JSON_PROMPT_NAMES:
        value = getattr(prompts, name)
        assert "return only" in value.lower()
