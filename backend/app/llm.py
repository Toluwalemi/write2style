import json
import logging
import time
from collections.abc import Iterator

from openai import OpenAI

from .config import settings
from .logging_config import timed
from .prompts import DRAFT_SYSTEM, DRAFT_USER, STYLE_DNA_REFINE_USER, STYLE_DNA_SYSTEM

log = logging.getLogger("app.llm")

_client: OpenAI | None = None


def _openrouter() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    return _client


def chat_json(model: str, system: str, user: str, temperature: float = 0.0) -> dict:
    with timed(log, "chat_json", model=model):
        resp = _openrouter().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
    content = resp.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        log.warning("chat_json_invalid", extra={"model": model, "content_chars": len(content)})
        return {"raw": content}


def refine_style_dna(current_dna: dict | None, sample_text: str) -> dict:
    truncated = sample_text[: settings.max_sample_chars_for_dna]
    user = STYLE_DNA_REFINE_USER.format(
        current_dna=json.dumps(current_dna) if current_dna else "{}",
        sample_text=truncated,
    )
    with timed(
        log,
        "style_dna_refine",
        model=settings.style_model,
        sample_chars=len(truncated),
        had_prior_dna=bool(current_dna),
    ):
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
        log.warning("style_dna_invalid_json", extra={"content_chars": len(content)})
        return {"raw": content}


def stream_draft(style_dna: dict, few_shot: list[str], prompt: str) -> Iterator[str]:
    few_shot_block = "\n\n---\n\n".join(few_shot) if few_shot else "(no past excerpts yet)"
    user = DRAFT_USER.format(
        style_dna=json.dumps(style_dna, indent=2) if style_dna else "(no style DNA yet)",
        few_shot=few_shot_block,
        prompt=prompt,
    )
    log.info(
        "draft_start",
        extra={
            "model": settings.draft_model,
            "few_shot_count": len(few_shot),
            "prompt_chars": len(prompt),
            "has_style_dna": bool(style_dna),
        },
    )
    start = time.perf_counter()
    first_token_logged = False
    output_chars = 0
    try:
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
                if not first_token_logged:
                    ttfb_ms = round((time.perf_counter() - start) * 1000, 2)
                    log.info(
                        "draft_first_token",
                        extra={"model": settings.draft_model, "ttfb_ms": ttfb_ms},
                    )
                    first_token_logged = True
                output_chars += len(delta)
                yield delta
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log.exception(
            "draft_failed",
            extra={"model": settings.draft_model, "duration_ms": duration_ms},
        )
        raise
    else:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log.info(
            "draft_complete",
            extra={
                "model": settings.draft_model,
                "duration_ms": duration_ms,
                "output_chars": output_chars,
            },
        )
