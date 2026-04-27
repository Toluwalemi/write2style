from collections import defaultdict
from statistics import mean

from .harness import CONDITIONS, CaseResult
from .judge import SCORE_KEYS


def _safe_mean(values: list[float]) -> float | None:
    cleaned = [v for v in values if v is not None]
    return round(mean(cleaned), 2) if cleaned else None


def _fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}"


def aggregate(results: list[CaseResult]) -> dict:
    by_condition: dict[str, list[float]] = defaultdict(list)
    by_author_condition: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in results:
        if r.error or not r.scores:
            continue
        overall = r.scores.get("overall")
        if overall is None:
            continue
        by_condition[r.condition].append(overall)
        by_author_condition[(r.author, r.condition)].append(overall)
    return {
        "by_condition": {k: _safe_mean(v) for k, v in by_condition.items()},
        "by_author_condition": {k: _safe_mean(v) for k, v in by_author_condition.items()},
    }


def format_report(results: list[CaseResult], conditions: tuple[str, ...] = CONDITIONS) -> str:
    if not results:
        return "_No results._\n"

    out: list[str] = []
    out.append("# Write2Style Evaluation Report\n")
    out.append(f"Cases scored: **{len(results)}**\n")
    errors = [r for r in results if r.error]
    if errors:
        out.append(f"Errors: **{len(errors)}**\n")

    out.append("## Overall (mean of `overall` score, 1–5)\n")
    out.append("| Condition | Mean |")
    out.append("|---|---|")
    agg = aggregate(results)
    for c in conditions:
        out.append(f"| {c} | {_fmt(agg['by_condition'].get(c))} |")
    out.append("")

    authors = sorted({r.author for r in results})
    out.append("## By author × condition\n")
    header = "| Author | " + " | ".join(conditions) + " |"
    sep = "|" + "---|" * (len(conditions) + 1)
    out.append(header)
    out.append(sep)
    for a in authors:
        row = [a]
        for c in conditions:
            row.append(_fmt(agg["by_author_condition"].get((a, c))))
        out.append("| " + " | ".join(row) + " |")
    out.append("")

    out.append("## Per-case detail\n")
    for r in results:
        out.append(f"### {r.author} · case {r.case_index} · `{r.condition}`")
        out.append(f"**Prompt:** {r.prompt.strip()}\n")
        if r.error:
            out.append(f"**Error:** {r.error}\n")
            continue
        scores_line = " · ".join(
            f"{k}={r.scores.get(k) if r.scores.get(k) is not None else '—'}" for k in SCORE_KEYS
        )
        out.append(f"**Scores:** {scores_line}")
        rationale = r.scores.get("rationale", "")
        if rationale:
            out.append(f"**Rationale:** {rationale}\n")
        out.append("**Output:**")
        out.append("```")
        out.append(r.candidate.strip())
        out.append("```\n")

    return "\n".join(out) + "\n"
