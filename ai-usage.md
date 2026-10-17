# BÁO CÁO MINH BẠCH VỀ VIỆC SỬ DỤNG TRÍ TUỆ NHÂN TẠO (AI USAGE REPORT)

> **Trường Đại học Sư phạm Kỹ thuật TP.HCM (HCMUTE)**  
> **Khoa Công nghệ Thông tin — Bộ môn Trí tuệ Nhân tạo**  
> **Môn học:** AI Programming with Python (AIPwP)  
> **Đề tài (Topic T3):** Trợ lý học tập trên giáo trình và kế hoạch bài dạy môn học (StudyMate)  
> **Nhóm sinh viên thực hiện:** Khuê & Hiển  
> **Công cụ AI hỗ trợ:** Google Antigravity / Gemini

---

## 1. Tư vấn Định dạng Dữ liệu Bài giảng (Data Type Consultation)

Ở giai đoạn đầu khi bắt đầu thực hiện đề tài, nhóm chưa được cung cấp bộ dữ liệu bài giảng chuẩn. Nhóm đã chủ động tham vấn AI về việc lựa chọn định dạng lưu trữ tối ưu giữa PDF, Markdown (`.md`) và Text thuần (`.txt`) cho bài toán RAG trên giáo trình môn học:
- **Tư vấn của AI:** AI đã phân tích ưu/nhược điểm và khuyến nghị nhóm nên sử dụng định dạng **Markdown (`.md`)**, đồng thời gợi ý sử dụng khối **YAML front-matter** ở đầu mỗi file (ví dụ: `doc_id`, `title`, `week`, `course`) để dễ dàng quản lý metadata phục vụ cho việc lọc dữ liệu sau này.
- **Thực hiện của nhóm:** Nhóm đã tiếp thu giải pháp này để cấu trúc toàn bộ 6 file bài giảng (`w1_lecture_notes.md` đến `w6_lecture_notes.md`) trong thư mục `data/`.

---

## 2. Định hướng Kế hoạch & Luồng Hoạt động Tổng thể (Project Planning)

Trước khi bắt tay vào viết mã, nhóm sử dụng AI để hỗ trợ phân rã yêu cầu đề bài và lập lộ trình triển khai:
- **Đóng góp của AI:**
  - Hỗ trợ đọc hiểu và phân tích 2 file yêu cầu của giảng viên (`01-De-tai-upload-for-student.pdf` và `02-Yeu-cau-Thuc-hien.pdf`).
  - Định hướng luồng đi và hoạt động tổng thể của hệ thống: phân tầng rõ rệt giữa Tầng tra cứu RAG, Tầng giao tiếp công cụ MCP Server và Tầng suy luận ReAct Agent.
  - Đề xuất chia sẵn bố cục dự kiến các thư mục và module trong project để phân chia công việc cân bằng giữa 2 thành viên.
- **Thực hiện của nhóm:** Nhóm thống nhất lộ trình, lập 2 nhánh Git riêng biệt (`Khue` và `Hien`) để cộng tác và trực tiếp quản lý tiến độ.

---

## 3. Phân tích Chi tiết Từng File Mã Nguồn (Detailed File-by-File Breakdown)

Dưới đây là bản kê khai chi tiết mức độ hỗ trợ của AI và công việc tự thực hiện của sinh viên trên từng file code trong dự án:

### 3.1. Cấu hình hệ thống & Giao diện dòng lệnh (`config.py`, `cli.py`, `main.py`)
- **`src/studymate/config.py`:**
  - *Vai trò của AI:* AI hướng dẫn cách tổ chức tập trung các biến môi trường (API keys, đường dẫn ROOT, tham số RAG, ngưỡng điểm) bằng `pathlib.Path` và `dotenv` để project hoạt động độc lập với môi trường chạy.
  - *Sinh viên:* Tự gõ code và cấu hình lại các tham số phù hợp với đề tài môn học.
- **`src/studymate/cli.py` & `src/studymate/main.py`:**
  - *Vai trò của AI:* Đóng góp phần lớn trong việc thiết lập hệ thống dòng lệnh: xây dựng cấu trúc cờ lệnh bằng `argparse` (`--demo`, `--verbose`), quản lý luồng asyncio khi gọi Agent, và thiết kế kịch bản 3 tầng trong `run_demo()`.
  - *Sinh viên:* Trực tiếp tinh chỉnh giao diện xuất ra terminal, loại bỏ các icon/emoji rườm rà để đảm bảo hiển thị văn bản thuần túy chuẩn mực trên Windows, và cấu hình `sys.path` an toàn cho lệnh khởi động của giảng viên.

### 3.2. Khối suy luận & Giao tiếp công cụ (`llm.py`, `mcp_server.py`, `agent.py`, `agent_support.py`)
- **`src/studymate/llm.py`:**
  - *Sinh viên:* Tự viết hàm gọi Groq API dựa trên kiến thức đã học ở Tuần 2 (`client.chat.completions.create`).
  - *Vai trò của AI:* Góp ý bổ sung cơ chế bắt lỗi RateLimit 429 và thuật toán bóc tách số giây yêu cầu chờ từ thông báo lỗi của Groq để tự động sleep retry chuẩn xác.
- **`src/studymate/mcp_server.py`:**
  - *Sinh viên:* Tự viết server dựa trên bài học Tuần 7 (`MCPServer`), khai báo 5 tools bằng decorator `@mcp.tool()`, tự thiết kế cơ sở dữ liệu `study_notes.json` để thực hiện Tầng hành động (Side Effect) và Đọc kiểm chứng.
  - *Vai trò của AI:* Rà soát và góp ý việc cấu hình logging sang `stderr` và file `server.log`, đảm bảo tuyệt đối không dùng `print` ra `stdout` làm hỏng kênh truyền JSON-RPC 2.0.
- **`src/studymate/agent.py` & `src/studymate/agent_support.py`:**
  - *Sinh viên:* Tự viết vòng lặp ReAct Agent dựa trên bài học Tuần 6 (`ex2_1_react_0_unfinished.py`), thiết kế cơ chế bảo vệ **Guard Verify** (bắt buộc gọi tool đọc kiểm tra sau khi gọi tool ghi).
  - *Vai trò của AI:* Góp ý hoàn thiện System Prompt theo phong cách ReAct và gợi ý tối ưu hàm bóc tách `parse_reply()` để xử lý các biến thể JSON mà vẫn giữ code ngắn gọn, dễ hiểu.

### 3.3. Phân hệ Hybrid RAG (`src/studymate/rag/`)
- **`store.py`, `hybrid_search.py`, `search.py`:**
  - *Sinh viên:* Hầu như kế thừa và tái sử dụng trực tiếp 100% từ các bài thực hành đã làm trên lớp ở Tuần 3 và Tuần 4 (`VectorStore`, hàm `embed_texts`, thuật toán `normalise_scores` min-max scaling, và hàm `combine_hybrid_scores` kết hợp BM25 + Dense vector).
  - *Vai trò của AI:* Tư vấn viết hàm tìm kiếm có hỗ trợ lọc metadata (`week`) phục vụ cho điểm thưởng Bonus 1.
- **`src/studymate/rag/corpus.py`:**
  - *Phần mới:* Thuật toán chia nhỏ văn bản markdown theo các cấp tiêu đề (`##` và `###`) để giữ nguyên cấu trúc ngữ cảnh bài học.
  - *Thực hiện:* Sinh viên tự tay code thuật toán bóc tách regex theo heading kèm sự tư vấn phương pháp từ AI.

### 3.4. Phân hệ Đánh giá Benchmark (`src/studymate/eval/`)
- **Tình trạng:** Đây là nội dung thuộc phần tự học của nhóm (Tuần 5 - RAG Evaluation & Groundedness).
- **Quy trình phối hợp với AI:**
  1. Sinh viên nhờ AI giải thích bức tranh tổng thể về phương pháp LLM-as-a-Judge và cơ chế bóc tách khẳng định nguyên tử (Atomic Claims Decomposition).
  2. Sinh viên tự lên ý tưởng và viết mã giả (pseudo-code) cho quy trình đánh giá.
  3. Sinh viên tự tay lập trình bộ 14 câu hỏi kiểm thử song ngữ trong `tests/testset.jsonl` kèm các câu bẫy từ chối ngoài giáo trình.
  4. Nhờ AI rà soát và chỉnh sửa để tối ưu hóa từ nhiều lần gọi LLM riêng lẻ thành 1 lần gọi batch duy nhất trong `src/studymate/eval/judge.py`, giúp tiết kiệm hơn 80% token.
  5. Sinh viên tự hoàn thiện runner `src/studymate/eval/run_eval.py` để xuất ra file log JSONL và CSV.

### 3.5. Bộ kiểm thử Unit Test (`tests/`)
- **`tests/test_corpus.py`, `tests/test_search.py`, `tests/test_mcp.py`, `tests/test_agent.py`:**
  - *Vai trò của AI:* Sinh ra khung kịch bản test tự động (test cases & mock assertions).
  - *Sinh viên:* Sử dụng bộ test này để kiểm tra độc lập xem các hàm do mình tự viết có chạy đúng và đạt yêu cầu hay không.

### 3.6. Cấu hình đóng gói & Script tiền xử lý (`Makefile`, `pyproject.toml`, `tools/build_index.py`)
- **`Makefile` & `pyproject.toml`:** AI dựa vào ngữ cảnh và cấu trúc thư mục của dự án để sinh ra file cấu hình dependencies và các phím tắt lệnh `make`.
- **`tools/build_index.py`:** Đã có sẵn sườn bài mẫu trên lớp ở Tuần 4 và Tuần 7. Sinh viên nhờ AI hướng dẫn cách kết hợp tạo vector embedding offline lưu vào `data/index.json` để khi Agent vận hành thực tế không phải mất thời gian embedding lại từ đầu.

### 3.7. Điểm thưởng Interoperability (`scripts/mcp_client_interop.py`)
- **Đóng góp của sinh viên chiếm 80%:** Sinh viên trực tiếp vận dụng kiến thức về MCP Client đã học ở Tuần 7 (`mcp.Client(StdioServerParameters)`) để tự viết script Client thứ hai độc lập, chứng minh tính tương tác của server mà không cần thông qua Agent.
- **AI đóng góp 20%:** Góp ý cấu trúc in kết quả kiểm chứng trực quan trên terminal.

---

## 4. Tóm tắt Tỷ lệ Đóng góp Thực tế

| Nhóm công việc / Thành phần | Tỷ lệ Sinh viên tự làm | Tỷ lệ AI hỗ trợ | Ghi chú vai trò chính của AI |
| :--- | :---: | :---: | :--- |
| Định hướng ý tưởng, lập kế hoạch, chọn data type | 40% | 60% | Tư vấn phương pháp luận, phân rã rubric |
| Phân hệ RAG (`corpus.py`, `store.py`, `hybrid_search.py`) | 85% | 15% | Kế thừa W3–W4; AI tư vấn regex heading |
| MCP Server & Cơ sở dữ liệu ghi chú (`mcp_server.py`) | 80% | 20% | Kế thừa W7; AI hỗ trợ rà soát logging |
| ReAct Agent & Guard Verify (`agent.py`) | 75% | 25% | Kế thừa W6; AI góp ý System Prompt & regex |
| Tự học phần Benchmark Evaluation (`judge.py`, `run_eval.py`) | 65% | 35% | AI giảng giải khái niệm, sinh viên code pseudo |
| Setup hệ thống CLI & Entrypoint (`cli.py`, `main.py`) | 40% | 60% | AI hỗ trợ dựng khung argparse, sinh viên tinh chỉnh |
| Bộ kiểm thử Unit Test (`tests/`) | 30% | 70% | AI sinh mã khung test, sinh viên dùng để nghiệm thu |
| Điểm thưởng MCP Interoperability (`scripts/`) | 80% | 20% | Sinh viên tự vận dụng kiến thức Tuần 7 |
