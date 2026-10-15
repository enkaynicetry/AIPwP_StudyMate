import json
import numpy as np
import requests
from pathlib import Path
from typing import Any
from studymate.config import JINA_API_KEY
from studymate.models import Document, DocumentChunk

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Tính độ tương đồng cosine giữa hai vector."""
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def embed_texts(texts: list[str], task: str = "retrieval.passage", batch_size: int = 16) -> list[list[float]]:
    """Gọi Jina API tạo embedding theo batch."""
    if not JINA_API_KEY:
        raise ValueError("Thiếu JINA_API_KEY trong file .env")

    url = "https://api.jina.ai/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JINA_API_KEY}",
    }

    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        payload = {
            "model": "jina-embeddings-v3",
            "task": task,
            "normalized": True,
            "input": [{"text": t} for t in batch],
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        for item in data:
            all_embeddings.append(item["embedding"])

    return all_embeddings

class LessonPlanStore:
    """Lớp lưu trữ tài liệu và chunk, hỗ trợ lưu và đọc index.json."""
    def __init__(self) -> None:
        self.docs: dict[str, Document] = {}
        self.chunks: dict[str, DocumentChunk] = {}

    def add_doc(self, doc: Document) -> None:
        self.docs[doc.doc_id] = doc

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        for c in chunks:
            self.chunks[c.chunk_id] = c

    def save(self, path: Path) -> None:
        """Lưu docs và chunks kèm embedding vào file JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "docs": [
                {
                    "doc_id": d.doc_id,
                    "title": d.title,
                    "content": d.content,
                    "source": d.source,
                    "metadata": d.metadata,
                    "created_at": d.created_at,
                }
                for d in self.docs.values()
            ],
            "chunks": [
                {
                    "chunk_id": c.chunk_id,
                    "content": c.content,
                    "doc_id": c.doc_id,
                    "title": c.title,
                    "source": c.source,
                    "chunk_index": c.chunk_index,
                    "metadata": c.metadata,
                    "embedding": c.embedding,
                }
                for c in self.chunks.values()
            ]
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: Path) -> None:
        """Đọc docs và chunks kèm embedding từ file JSON."""
        if not path.exists():
            raise FileNotFoundError(f"Chỉ mục chưa tồn tại tại {path}. Hãy chạy tools/build_index.py trước.")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.docs = {}
        for d in data.get("docs", []):
            self.docs[d["doc_id"]] = Document(
                content=d["content"],
                doc_id=d["doc_id"],
                title=d["title"],
                source=d["source"],
                metadata=d.get("metadata", {}),
                created_at=d.get("created_at", ""),
            )

        self.chunks = {}
        for c in data.get("chunks", []):
            self.chunks[c["chunk_id"]] = DocumentChunk(
                chunk_id=c["chunk_id"],
                content=c["content"],
                doc_id=c["doc_id"],
                title=c["title"],
                source=c["source"],
                chunk_index=c.get("chunk_index", 0),
                metadata=c.get("metadata", {}),
                embedding=c.get("embedding"),
            )
