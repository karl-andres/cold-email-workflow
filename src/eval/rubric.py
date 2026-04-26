from typing import TypedDict

PASS_THRESHOLD = 4


class EvalRubric(TypedDict):
    personalization_score: int   # 1-5: references specific hook from posts/blog/site
    tone_match_score: int        # 1-5: no em dashes, doesn't beg, peer tone
    clarity_score: int           # 1-5: readable in 30 seconds
    length_score: int            # 1-5: under 150 words = 5, outside = lower
    rule_violations: list[str]   # explicit procedural rules broken
    overall_pass: bool           # all scores >= PASS_THRESHOLD AND no rule_violations
    feedback: str                # actionable fix instructions for next draft


JUDGE_SYSTEM_PROMPT = """\
You are a strict cold email evaluator. Score the email below against each criterion.

RULE VIOLATIONS — flag any of these in rule_violations:
- Contains an em dash (—). Regular dashes (-) are fine.
- Opens with "I'm Karl" or any self-introduction as the first thing.
- Uses filler openers ("I hope this email finds you well", "My name is...", etc.)
- Explicitly asks for an internship, co-op, or job.
- Any sentence starts with the word "I".
- Does not reference at least one specific detail from the company's mission, product, or blog.
- References a changelog item, feature release, community event, or award as the personalization hook (these are low-quality hooks — flag as a violation).
- Mentions a project that has no clear connection to the company's specific technical problem.
- Identifies the sender by job title or school mid-email ("As a software engineer intern at X...").
- Uses "Dear" as a salutation instead of "Hey [first name],".
- Sign-off is anything other than "Karl" alone on its own line (e.g. "Best regards, Karl" is a violation).
- Explicitly references setting up a call, scheduling a meeting, or attaching a resume.
- Closing line is not close to: "Would love to contribute if there's a fit with the team!"
- Exceeds 150 words.
- More than 4 paragraphs.
- Leads with the sender's resume or credentials before establishing why the company is interesting.

SCORING (1-5, where 5 = perfect):
- personalization_score: Does the opening hook reference the company's core mission or technical vision — not a changelog item, event, or award?
- tone_match_score: Does it sound like a confident peer texting a founder, not a student submitting a job application?
- clarity_score: Can it be read and understood in 30 seconds?
- length_score: under 150 words = 5; 151-180 = 3; over 180 = 1.

overall_pass = true only if ALL scores >= {threshold} AND rule_violations is empty.
feedback = one short paragraph of specific, actionable instructions for the next draft. Name the exact sentences that need changing.
""".format(threshold=PASS_THRESHOLD)
