from typing import Any
from studymate.config import INDEX_PATH, TOP_K, W_BM25, W_VECTOR, MIN_SCORE, SEARCH_MODE
from studymate.models import SearchHit, DocumentChunk
from studymate.rag.store import LessonPlanStore, embed_texts, cosine_similarity
from studymate.rag.hybrid_search import build_bm25_index, combine_hybrid_scores

_store: LessonPlanStore | None = None
_bm25_index = None
_cached_chunks: list[DocumentChunk] = []

def get_loaded_store() -> tuple[LessonPlanStore, list[DocumentChunk], Any]:
    """Tải store và dựng chỉ mục BM25 một lần duy nhất."""
    global _store, _bm25_index, _cached_chunks
    if _store is None:
        _store = LessonPlanStore()
        _store.load(INDEX_PATH)
        _cached_chunks = list(_store.chunks.values())
        _bm25_index = build_bm25_index(_cached_chunks)
    return _store, _cached_chunks, _bm25_index

def search(
    query: str,
    mode: str = "",
    top_k: int = TOP_K,
    filters: dict[str, Any] | None = None,
) -> list[SearchHit]:
    """Tìm kiếm chunk theo hybrid, dense hoặc bm25 kèm metadata filter."""
    store, all_chunks, bm25_index = get_loaded_store()
    search_mode = mode or SEARCH_MODE
    filters = filters or {}

    # 1. Lọc theo metadata nếu có
    filtered_indices: list[int] = []
    for idx, c in enumerate(all_chunks):
        matched = True
        for k, v in filters.items():
            if v and str(c.metadata.get(k, "")).lower() != str(v).lower():
                matched = False
                break
        if matched:
            filtered_indices.append(idx)

    if not filtered_indices:
        return []

    target_chunks = [all_chunks[i] for i in filtered_indices]

    # 2. Tính điểm theo mode
    ranked_results: list[tuple[DocumentChunk, float]] = []

    if search_mode == "bm25":
        tokenized_q = query.lower().split()
        raw_bm25 = bm25_index.get_scores(tokenized_q)
        scores = [raw_bm25[i] for i in filtered_indices]
        for c, s in zip(target_chunks, scores):
            ranked_results.append((c, float(s)))

    elif search_mode == "dense":
        q_vec = embed_texts([query], task="retrieval.query")[0]
        for c in target_chunks:
            score = cosine_similarity(q_vec, c.embedding) if c.embedding else 0.0
            ranked_results.append((c, score))

    else:  # hybrid
        tokenized_q = query.lower().split()
        raw_bm25 = [bm25_index.get_scores(tokenized_q)[i] for i in filtered_indices]
        
        q_vec = embed_texts([query], task="retrieval.query")[0]
        v_scores = [
            cosine_similarity(q_vec, c.embedding) if c.embedding else 0.0
            for c in target_chunks
        ]
        
        h_scores = combine_hybrid_scores(raw_bm25, v_scores, w_bm25=W_BM25, w_vector=W_VECTOR)
        for c, s in zip(target_chunks, h_scores):
            ranked_results.append((c, float(s)))

    # 3. Sắp xếp điểm giảm dần
    ranked_results.sort(key=lambda x: x[1], reverse=True)

    # 4. Lọc theo min_score
    threshold = MIN_SCORE.get(search_mode, 0.3)
    valid_results = [(c, s) for c, s in ranked_results if s >= threshold]

    # 5. Lấy top_k
    hits: list[SearchHit] = []
    for c, score in valid_results[:top_k]:
        hits.append(SearchHit(
            chunk_id=c.chunk_id,
            doc_id=c.doc_id,
            score=round(score, 4),
            content=c.content,
            metadata=c.metadata,
        ))

    return hits
