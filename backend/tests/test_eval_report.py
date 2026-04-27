from eval.harness import CaseResult
from eval.report import aggregate, format_report


def _result(author, condition, overall, case_index=0, error=None):
    scores = {} if error else {
        "tone": overall,
        "vocabulary": overall,
        "structure": overall,
        "overall": overall,
        "rationale": "test",
    }
    return CaseResult(
        author=author,
        case_index=case_index,
        prompt="p",
        condition=condition,
        candidate="c" if not error else "",
        scores=scores,
        error=error,
    )


def test_aggregate_means_per_condition():
    results = [
        _result("a", "baseline", 2),
        _result("a", "baseline", 4),
        _result("a", "dna_rag", 5),
    ]
    agg = aggregate(results)
    assert agg["by_condition"]["baseline"] == 3.0
    assert agg["by_condition"]["dna_rag"] == 5.0


def test_aggregate_skips_errors_and_missing():
    results = [
        _result("a", "baseline", 4),
        _result("a", "baseline", None, error="boom"),
        CaseResult(
            author="a", case_index=1, prompt="p", condition="baseline",
            candidate="c", scores={"overall": None},
        ),
    ]
    agg = aggregate(results)
    assert agg["by_condition"]["baseline"] == 4.0


def test_aggregate_per_author_condition():
    results = [
        _result("alice", "dna_only", 3),
        _result("alice", "dna_only", 5),
        _result("bob", "dna_only", 2),
    ]
    agg = aggregate(results)
    assert agg["by_author_condition"][("alice", "dna_only")] == 4.0
    assert agg["by_author_condition"][("bob", "dna_only")] == 2.0


def test_format_report_has_overall_and_per_author_tables():
    results = [
        _result("alice", "baseline", 2),
        _result("alice", "dna_only", 3),
        _result("alice", "dna_rag", 5),
    ]
    report = format_report(results)
    assert "# Write2Style Evaluation Report" in report
    assert "## Overall" in report
    assert "## By author" in report
    assert "alice" in report
    assert "baseline" in report
    assert "dna_rag" in report


def test_format_report_handles_empty():
    assert "No results" in format_report([])


def test_format_report_includes_error_cases():
    results = [_result("alice", "baseline", None, error="rate limited")]
    report = format_report(results)
    assert "Errors: **1**" in report
    assert "rate limited" in report
