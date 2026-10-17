# StudyMate — Trợ lý học tập trên Lesson Plan môn học

> **Trường Đại học Sư phạm Kỹ thuật TP.HCM (HCMUTE)**  
> **Khoa Công nghệ Thông tin — Bộ môn Trí tuệ Nhân tạo**  
> **Môn học:** AI Programming with Python (AIPwP)  
> **Đề tài (Topic T3):** Trợ lý học tập trên giáo trình và kế hoạch bài dạy môn học  
> **Nhóm sinh viên thực hiện:** Khuê & Hiển  
> **Cơ sở dữ liệu tri thức:** 6 bài giảng môn học từ Tuần 1 đến Tuần 6 (`AIPwP-W01` đến `AIPwP-W06`).

---

## 1. Lệnh chạy ứng dụng

Theo yêu cầu của đề tài, toàn bộ các tác vụ chính của dự án được cấu hình sẵn trong `Makefile` để thực thi nhanh chóng:

| Tác vụ | Lệnh make | Chức năng chi tiết |
| :--- | :--- | :--- |
| **Chạy Demo 3 tầng (Cold Start)** | `make setup && make demo` | Tự động tạo chỉ mục offline và chạy kịch bản Demo 3 tầng năng lực theo rubric (không cần nhập tay câu hỏi). |
| **Đánh giá Benchmark (Lab 5)** | `make eval` | Tự động chạy 14 câu hỏi kiểm thử song ngữ, đo lường độ trung thực (Faithfulness) và xuất log JSONL + CSV. |
| **So sánh cấu hình RAG (Bonus)** | `make compare` | So sánh đối đầu giữa 2 cấu hình tìm kiếm: Dense-only (Jina) vs Hybrid (BM25 + Dense). |
| **Kiểm chứng Interop (Bonus)** | `make interop` | Chạy Client Python thứ hai độc lập để chứng minh tính tương tác của MCP Server. |
| **Trò chuyện trực tiếp (CLI)** | `make chat` | Khởi động giao diện dòng lệnh tương tác hỏi đáp liên tục với StudyMate. |
| **Kiểm thử hệ thống (Unit Test)** | `make test` | Chạy toàn bộ 4 file kiểm thử trong thư mục `tests/`. |

---

## 2. Hướng dẫn cài đặt & Thiết lập môi trường

### Bước 1: Khởi tạo và kích hoạt môi trường ảo Python (>= 3.11)
```bash
python -m venv .venv

# Kích hoạt trên Windows PowerShell:
.venv\Scripts\Activate.ps1

# Kích hoạt trên Linux / macOS:
source .venv/bin/activate
```

### Bước 2: Cài đặt các thư viện phụ thuộc ở chế độ editable
```bash
pip install -e .
```

### Bước 3: Cấu hình biến môi trường
Tạo file `.env` từ file mẫu `.env.example` và điền các khóa API:
```ini
GROQ_API_KEY=your_groq_api_key_here
JINA_API_KEY=your_jina_api_key_here
LLM_MODEL=qwen/qwen-2.5-32b
```

---

## 3. Cấu trúc cây thư mục dự án

```text
AIPwP/
├── data/                                  # Cơ sở tri thức bài giảng & cơ sở dữ liệu
│   ├── w1_lecture_notes.md ... w6...      # 6 bài giảng Markdown kèm YAML front-matter
│   ├── index.json                         # Chỉ mục vector & BM25 tạo trước offline
│   └── study_notes.json                   # Cơ sở dữ liệu ghi chú ôn tập của sinh viên
│
├── src/studymate/                         # Mã nguồn gói studymate
│   ├── __init__.py                        # Khởi tạo package
│   ├── config.py                          # Cấu hình hệ thống & nạp biến môi trường
│   ├── models.py                          # Định nghĩa dữ liệu hướng đối tượng qua @dataclass
│   ├── llm.py                             # Giao tiếp Groq API, quản lý retry và token usage
│   ├── mcp_server.py                      # MCP Stdio Server (5 tools, stdout sạch)
│   ├── agent.py                           # Vòng lặp ReAct Agent & Guard Verify
│   ├── agent_support.py                   # System prompt ReAct và hàm parse_reply
│   ├── cli.py                             # Giao diện dòng lệnh & kịch bản demo 3 tầng
│   ├── main.py                            # Điểm nhập chính của chương trình
│   │
│   ├── rag/                               # Phân hệ Hybrid RAG
│   │   ├── corpus.py                      # Bóc tách front-matter & chia chunk Markdown
│   │   ├── store.py                       # Vector Store kết nối Jina AI Embeddings
│   │   ├── search.py                      # Tìm kiếm bài giảng có lọc metadata
│   │   └── hybrid_search.py               # Thuật toán kết hợp BM25 + Dense vectors
│   │
│   └── eval/                              # Phân hệ Đánh giá Benchmark (Lab 5)
│       ├── __init__.py
│       ├── judge.py                       # LLM-as-a-Judge đánh giá Atomic Claims
│       └── run_eval.py                    # Runner chạy đánh giá & so sánh cấu hình
│
├── tests/                                 # Bộ kiểm thử Unit test & Benchmark Testset
│   ├── test_corpus.py                     # Kiểm thử nạp bài giảng
│   ├── test_search.py                     # Kiểm thử Hybrid Search & Metadata Filter
│   ├── test_mcp.py                        # Kiểm thử MCP Server qua giao thức Stdio
│   ├── test_agent.py                      # Kiểm thử ReAct loop & parse cú pháp
│   └── testset.jsonl                      # 14 câu hỏi benchmark song ngữ chuẩn rubric
│
├── tools/                                 # Script tiền xử lý dữ liệu
│   └── build_index.py                     # Tạo chỉ mục vector & BM25 offline
│
├── scripts/                               # Kịch bản phụ trợ
│   └── mcp_client_interop.py              # Client thứ hai kiểm chứng MCP Interoperability
│
├── logs/                                  # Nhật ký thực thi server và lịch sử chạy eval (.jsonl, .csv)
├── Makefile                               # Tự động hóa các tác vụ dòng lệnh
├── ai-usage.md                            # Báo cáo chi tiết minh bạch về việc sử dụng AI
├── pyproject.toml                         # Khai báo gói và thư viện phụ thuộc
└── README.md                              # Hướng dẫn đồ án
```
