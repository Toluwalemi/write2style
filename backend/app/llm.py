import json
from collections.abc import Iterator

from openai import OpenAI

from .config import settings
from .prompts import DRAFT_SYSTEM, DRAFT_USER, STYLE_DNA_REFINE_USER, STYLE_DNA_SYSTEM

_client: OpenAI | None = None


def _openrouter() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    return _client


def refine_style_dna(current_dna: dict | None, sample_text: str) -> dict:
    truncated = sample_text[: settings.max_sample_chars_for_dna]
    user = STYLE_DNA_REFINE_USER.format(
        current_dna=json.dumps(current_dna) if current_dna else "{}",
        sample_text=truncated,
    )
    resp = _openrouter().chat.completions.create(
        model=settings.style_model,
        messages=[
            {"role": "system", "content": STYLE_DNA_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw": content}


def stream_draft(style_dna: dict, few_shot: list[str], prompt: str) -> Iterator[str]:
    few_shot_block = "\n\n---\n\n".join(few_shot) if few_shot else "(no past excerpts yet)"
    user = DRAFT_USER.format(
        style_dna=json.dumps(style_dna, indent=2) if style_dna else "(no style DNA yet)",
        few_shot=few_shot_block,
        prompt=prompt,
    )
    stream = _openrouter().chat.completions.create(
        model=settings.draft_model,
        messages=[
            {"role": "system", "content": DRAFT_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield delta
