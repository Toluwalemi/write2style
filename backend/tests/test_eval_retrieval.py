import math

import pytest

from eval.retrieval import cosine, top_k


class TestCosine:
    def test_identical_vectors(self):
        assert cosine([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        assert cosine([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self):
        assert cosine([0.0, 0.0], [1.0, 2.0]) == 0.0
        assert cosine([1.0, 2.0], [0.0, 0.0]) == 0.0

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            cosine([1.0, 2.0], [1.0, 2.0, 3.0])

    def test_known_value(self):
        a = [1.0, 1.0]
        b = [1.0, 0.0]
        expected = 1.0 / math.sqrt(2)
        assert cosine(a, b) == pytest.approx(expected)


class TestTopK:
    def test_orders_by_similarity(self):
        query = [1.0, 0.0]
        chunks = [
            ("far", [0.0, 1.0]),
            ("near", [1.0, 0.1]),
            ("middle", [1.0, 1.0]),
        ]
        result = top_k(query, chunks, k=3)
        assert result == ["near", "middle", "far"]

    def test_respects_k(self):
        query = [1.0, 0.0]
        chunks = [(f"c{i}", [1.0, float(i)]) for i in range(10)]
        result = top_k(query, chunks, k=3)
        assert len(result) == 3

    def test_empty_chunks(self):
        assert top_k([1.0, 0.0], [], k=5) == []
