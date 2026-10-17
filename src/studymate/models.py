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

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def add(self, prompt: int, completion: int) -> None:
        self.calls += 1
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        if prompt > self.max_prompt:
            self.max_prompt = prompt

# --- Cấu trúc dữ liệu cho Agent & Tool (Tuần 6 & 7) ---

@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    read_only: bool = True

@dataclass
class ParsedReply:
    kind: str  # "final", "action", hoặc "invalid"
    name: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    text: str = ""
    error: str = ""

@dataclass
class AgentRun:
    answer: str
    trace: list[dict[str, Any]] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    observations: list[str] = field(default_factory=list)
    error: str = ""

# --- Quản lý Ghi chú Học tập & Trạng thái Tool (Side-Effect State) ---

@dataclass
class StudyNote:
    note_id: str
    topic: str
    content: str
    week: int = 0
    created_at: str = ""


