# StudyMate — Trợ lý học tập trên lesson plan môn học

> **Môn học:** AI Programming with Python — HCMUTE  
> **Đề tài:** Trợ lý học tập trên lesson plan & tài liệu môn học  
> **Dữ liệu bài giảng:** Giáo trình & Kế hoạch bài dạy 6 tuần của môn học AI Programming with Python (`w1` đến `w6`).

---

## 1. Cấu trúc thư mục hiện tại (Khung sườn khởi tạo)

```text
AIPwP/
├── data/                                  # Dữ liệu bài giảng 6 tuần môn học
│   ├── w1_lecture_notes.md                # Bài giảng Tuần 1: Python Data Structures for AI
│   ├── w2_lecture_notes.md                # Bài giảng Tuần 2: LLM API Access & Integration
│   ├── w3_lecture_notes.md                # Bài giảng Tuần 3: RAG Foundations: Documents & Embeddings
│   ├── w4_lecture_notes.md                # Bài giảng Tuần 4: Building the RAG Pipeline
│   ├── w5_lecture_notes.md                # Bài giảng Tuần 5: RAG Evaluation & Groundedness
│   └── w6_lecture_notes.md                # Bài giảng Tuần 6: Agent Loop, ReAct & Agent Memory
│
├── src/studymate/                         # Khung mã nguồn dự án
│   └── __init__.py                        # Khởi tạo package studymate
│
├── .env.example                           # Mẫu cấu hình API key
├── .gitignore                             # Cấu hình loại trừ file rác, cache, môi trường ảo
├── pyproject.toml                         # Khai báo cài đặt gói và dependencies
└── README.md                              # Tài liệu giới thiệu dự án & cấu trúc
```

---

## 2. Hướng dẫn cài đặt & Thiết lập ban đầu

### Cài đặt môi trường
Tạo và kích hoạt môi trường ảo Python (>= 3.11):
```bash
python -m venv .venv
# Kích hoạt môi trường (Windows PowerShell):
.venv\Scripts\Activate.ps1

# Cài đặt package ở chế độ editable
pip install -e .
```

### Cấu hình API Key
Tạo file `.env` từ file mẫu `.env.example`:
```ini
GROQ_API_KEY=your_groq_api_key_here
JINA_API_KEY=your_jina_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
```

---

## 3. Kế hoạch phát triển các module tiếp theo

- **Module RAG (`src/studymate/rag/`):** Tải và xử lý bài giảng, chia chunk theo ngữ cảnh, xây dựng vector store (Jina embeddings) và tìm kiếm kết hợp Hybrid Search (BM25 + Dense).
- **Module LLM (`src/studymate/llm.py`):** Tích hợp Groq API với cơ chế retry, xử lý lỗi và thống kê token usage.
- **Tools (`tools/`):** Script tạo chỉ mục offline cho cơ sở tri thức bài giảng.
- **Tests (`tests/`):** Bộ kiểm thử đọc dữ liệu bài giảng và kiểm thử truy vấn tìm kiếm RAG.
