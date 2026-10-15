from rank_bm25 import BM25Okapi
from typing import Any

def normalise_scores(scores: list[float]) -> list[float]:
    """Chuẩn hoá danh sách điểm về [0, 1] bằng min-max scaling."""
    if not scores:
        return []
    min_s = min(scores)
    max_s = max(scores)
    if max_s == min_s:
        return [1.0] * len(scores)
    return [(s - min_s) / (max_s - min_s) for s in scores]

def build_bm25_index(chunks: list[Any]) -> BM25Okapi:
    """Tạo chỉ mục BM25 từ danh sách chunk (tokenize bằng lowercase split)."""
    tokenized = [chunk.content.lower().split() for chunk in chunks]
    return BM25Okapi(tokenized)

def combine_hybrid_scores(
    bm25_scores: list[float],
    vector_scores: list[float],
    w_bm25: float = 0.3,
    w_vector: float = 0.7
) -> list[float]:
    """Kết hợp điểm BM25 đã chuẩn hoá và cosine similarity theo trọng số."""
    bm25_norm = normalise_scores(bm25_scores)
    return [
        w_bm25 * b + w_vector * v
        for b, v in zip(bm25_norm, vector_scores)
    ]
