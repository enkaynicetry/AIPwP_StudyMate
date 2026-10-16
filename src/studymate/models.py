from dataclasses import dataclass, field
from typing import Any

# --- Cấu trúc dữ liệu cho RAG & Document ---

@dataclass
class Document:
    content: str
    doc_id: str
    title: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

@dataclass
class DocumentChunk:
    chunk_id: str
    content: str
    doc_id: str
    title: str
    source: str
    chunk_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None

@dataclass
class SearchHit:
    chunk_id: str
    doc_id: str
    score: float
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

# --- Quản lý Token & Usage ---

@dataclass
class Usage:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    max_prompt: int = 0

    def add(self, prompt: int, completion: int) -> None:
        self.calls += 1
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        if prompt > self.max_prompt:
            self.max_prompt = prompt


# --- Quản lý Ghi chú Học tập & Trạng thái Tool (Side-Effect State) ---

@dataclass
class StudyNote:
    note_id: str
    topic: str
    content: str
    week: int = 0
    created_at: str = ""
