# StudyMate — Trợ lý học tập trên lesson plan môn học

> **Môn học:** AI Programming with Python — HCMUTE  
> **Đề tài:** Trợ lý học tập trên lesson plan & tài liệu môn học  
> **Dữ liệu bài giảng:** Giáo trình & Kế hoạch bài dạy 6 tuần của môn học AI Programming with Python (`w1` đến `w6`).

---

## 1. Cấu trúc thư mục dự án

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
├── src/studymate/                         # Mã nguồn gói studymate
│   ├── __init__.py                        # Khởi tạo package studymate
│   ├── config.py                          # Quản lý cấu hình hệ thống & nạp biến môi trường
│   ├── models.py                          # Định nghĩa cấu trúc dữ liệu OOP (@dataclass)
│   └── rag/                               # Phân hệ RAG (Retrieval-Augmented Generation)
│       ├── __init__.py
│       └── corpus.py                      # Tách YAML front-matter & chia chunk tài liệu markdown
│
├── tests/                                 # Thư mục kiểm thử (Unit tests)
│   └── test_corpus.py                     # Kiểm thử đọc front-matter và nạp toàn bộ bài giảng
│
├── .env.example                           # Mẫu cấu hình API key
├── .gitignore                             # Cấu hình loại trừ file cache, môi trường ảo
├── pyproject.toml                         # Khai báo cấu hình gói và dependencies
└── README.md                              # Tài liệu hướng dẫn & cấu trúc dự án
```

---

## 2. Hướng dẫn cài đặt & Thiết lập ban đầu

### Bước 1: Cài đặt môi trường ảo
Khởi tạo và kích hoạt môi trường ảo Python (>= 3.11):
```bash
python -m venv .venv

# Kích hoạt trên Windows PowerShell:
.venv\Scripts\Activate.ps1

# Cài đặt các gói phụ thuộc ở chế độ editable:
pip install -e .
```

### Bước 2: Cấu hình biến môi trường
Sao chép `.env.example` thành `.env` và điền các khóa API:
```ini
GROQ_API_KEY=your_groq_api_key_here
JINA_API_KEY=your_jina_api_key_here
LLM_MODEL=openai/gpt-oss-20b
```


## 3. Kế hoạch phát triển các module tiếp theo

- **Module Vector Store & Search (`src/studymate/rag/`):** Tích hợp Jina AI embedding (`store.py`), thuật toán tìm kiếm kết hợp Hybrid Search BM25 + Dense vector (`hybrid_search.py`, `search.py`).
- **Module LLM (`src/studymate/llm.py`):** Kết nối Groq API gọi LLM xử lý câu hỏi sinh viên, quản lý retry và thống kê token usage.
- **Tools (`tools/`):** Script `build_index.py` tạo chỉ mục vector offline lưu tại `data/index.json`.
- **Giao diện dòng lệnh (CLI):** Cung cấp giao diện tương tác trực tiếp cho sinh viên hỏi đáp.
