import math


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError(f"vector length mismatch: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def top_k(
    query_vec: list[float],
    chunks_with_vecs: list[tuple[str, list[float]]],
    k: int,
) -> list[str]:
    scored = [(cosine(query_vec, vec), text) for text, vec in chunks_with_vecs]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [text for _, text in scored[:k]]
