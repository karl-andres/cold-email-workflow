from src.eval.rubric import JUDGE_SYSTEM_PROMPT, PASS_THRESHOLD, EvalRubric


def test_pass_threshold_is_4():
    assert PASS_THRESHOLD == 4


def test_judge_prompt_contains_key_rules():
    assert "em dash" in JUDGE_SYSTEM_PROMPT.lower() or "em dashes" in JUDGE_SYSTEM_PROMPT.lower()
    assert "180" in JUDGE_SYSTEM_PROMPT
    assert "internship" in JUDGE_SYSTEM_PROMPT.lower()


def test_eval_rubric_typeddict_keys():
    rubric: EvalRubric = {
        "personalization_score": 5,
        "tone_match_score": 4,
        "clarity_score": 4,
        "cta_strength_score": 4,
        "length_score": 5,
        "rule_violations": [],
        "overall_pass": True,
        "feedback": "Looks good.",
    }
    assert rubric["overall_pass"] is True
    assert isinstance(rubric["rule_violations"], list)
