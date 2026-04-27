from app.config import settings
from app.llm import chat_json

JUDGE_SYSTEM = """You are an impartial literary judge. You score how well a CANDIDATE passage imitates the style of a REFERENCE passage written by the actual author for the same prompt.

Score four dimensions, each 1-5:
1. tone — emotional register, attitude, formality
2. vocabulary — word choice, jargon level, register
3. structure — sentence length, rhythm, syntax patterns
4. overall — holistic stylistic match

Scale:
1 = no resemblance
2 = vague resemblance
3 = some recognisable traits
4 = strong match with minor drift
5 = could pass for the same author

Be strict. A 5 is rare. Ground every score in something specific you can point to.

Return JSON only:
{"tone": int, "vocabulary": int, "structure": int, "overall": int, "rationale": "1-2 sentences citing specific observations"}"""


JUDGE_USER = """PROMPT:
{prompt}

REFERENCE (the actual author's writing):
---
{reference}
---

CANDIDATE (to be scored):
---
{candidate}
---

Score the candidate."""


SCORE_KEYS = ("tone", "vocabulary", "structure", "overall")


def judge(prompt: str, reference: str, candidate: str, model: str | None = None) -> dict:
    user = JUDGE_USER.format(prompt=prompt, reference=reference, candidate=candidate)
    raw = chat_json(model or settings.style_model, JUDGE_SYSTEM, user, temperature=0.0)
    out: dict = {}
    for key in SCORE_KEYS:
        value = raw.get(key)
        out[key] = int(value) if isinstance(value, (int, float)) and 1 <= value <= 5 else None
    out["rationale"] = raw.get("rationale", "")
    return out
