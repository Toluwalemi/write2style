import json
from dataclasses import dataclass, field
from pathlib import Path

from app.config import settings
from app.embeddings import embed
from app.extraction import chunk_text
from app.llm import refine_style_dna, stream_draft

from .judge import judge
from .retrieval import top_k

CONDITIONS = ("baseline", "dna_only", "dna_rag")

SAMPLE_EXTENSIONS = (".md", ".txt")


@dataclass
class EvalCase:
    prompt: str
    reference: str


@dataclass
class Author:
    name: str
    train_samples: list[str]
    cases: list[EvalCase]


@dataclass
class CaseResult:
    author: str
    case_index: int
    prompt: str
    condition: str
    candidate: str
    scores: dict
    error: str | None = None


@dataclass
class AuthorContext:
    name: str
    style_dna: dict
    chunks_with_vecs: list[tuple[str, list[float]]] = field(default_factory=list)


def load_authors(data_dir: Path) -> list[Author]:
    if not data_dir.exists():
        raise FileNotFoundError(f"eval data dir not found: {data_dir}")
    authors: list[Author] = []
    for sub in sorted(data_dir.iterdir()):
        if not sub.is_dir():
            continue
        eval_path = sub / "eval.json"
        if not eval_path.exists():
            continue
        train_files = sorted(
            p for p in sub.iterdir() if p.is_file() and p.suffix in SAMPLE_EXTENSIONS
        )
        train_samples = [p.read_text(encoding="utf-8") for p in train_files]
        cases_raw = json.loads(eval_path.read_text(encoding="utf-8"))
        cases = [EvalCase(prompt=c["prompt"], reference=c["reference"]) for c in cases_raw]
        authors.append(Author(name=sub.name, train_samples=train_samples, cases=cases))
    return authors


def build_context(author: Author) -> AuthorContext:
    dna: dict | None = None
    for sample in author.train_samples:
        dna = refine_style_dna(dna, sample)
    chunks: list[str] = []
    for sample in author.train_samples:
        chunks.extend(chunk_text(sample, settings.chunk_size, settings.chunk_overlap))
    vectors = embed(chunks) if chunks else []
    return AuthorContext(
        name=author.name,
        style_dna=dna or {},
        chunks_with_vecs=list(zip(chunks, vectors, strict=True)),
    )


def _draft(style_dna: dict, few_shot: list[str], prompt: str) -> str:
    return "".join(stream_draft(style_dna, few_shot, prompt))


def run_condition(
    condition: str,
    prompt: str,
    ctx: AuthorContext,
) -> str:
    if condition == "baseline":
        return _draft({}, [], prompt)
    if condition == "dna_only":
        return _draft(ctx.style_dna, [], prompt)
    if condition == "dna_rag":
        if not ctx.chunks_with_vecs:
            return _draft(ctx.style_dna, [], prompt)
        query_vec = embed([prompt])[0]
        few_shot = top_k(query_vec, ctx.chunks_with_vecs, settings.top_k_few_shot)
        return _draft(ctx.style_dna, few_shot, prompt)
    raise ValueError(f"unknown condition: {condition}")


def run_eval(
    authors: list[Author],
    conditions: tuple[str, ...] = CONDITIONS,
) -> list[CaseResult]:
    results: list[CaseResult] = []
    for author in authors:
        ctx = build_context(author)
        for idx, case in enumerate(author.cases):
            for condition in conditions:
                try:
                    candidate = run_condition(condition, case.prompt, ctx)
                    scores = judge(case.prompt, case.reference, candidate)
                    results.append(
                        CaseResult(
                            author=author.name,
                            case_index=idx,
                            prompt=case.prompt,
                            condition=condition,
                            candidate=candidate,
                            scores=scores,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    results.append(
                        CaseResult(
                            author=author.name,
                            case_index=idx,
                            prompt=case.prompt,
                            condition=condition,
                            candidate="",
                            scores={},
                            error=str(exc),
                        )
                    )
    return results
