import json
import logging
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from mcp.server import MCPServer

from studymate.config import ROOT
from studymate.models import StudyNote
from studymate.rag.search import search, get_loaded_store

# Thiết lập ghi log ra stderr và file logs/server.log
# TUYỆT ĐỐI không dùng print() ra stdout vì sẽ phá hỏng kênh truyền JSON-RPC của MCP!
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "server.log"

_handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
try:
    _handlers.append(logging.FileHandler(LOG_FILE, encoding="utf-8"))
except OSError:
    pass

logging.basicConfig(
    level=logging.INFO,
    handlers=_handlers,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("studymate.mcp_server")

# Đường dẫn lưu ghi chú ôn tập của sinh viên (Side-Effect State)
NOTES_PATH = ROOT / "data" / "study_notes.json"

mcp = MCPServer(
    "studymate-server",
    description="StudyMate MCP Server hỗ trợ tra cứu bài giảng và quản lý kế hoạch học tập môn AIPwP",
)

# ==============================================================================
# CÁC TOOL ĐỌC DỮ LIỆU BÀI GIẢNG (READ-ONLY)
# ==============================================================================

@mcp.tool()
def list_documents() -> str:
    """
    Liệt kê toàn bộ các bài giảng hiện có trong cơ sở dữ liệu học tập kèm mã tuần.
    Dùng trước khi tra cứu để nắm tổng quan danh sách bài học môn AI Programming with Python.
    """
    try:
        store, _, _ = get_loaded_store()
        if not store.docs:
            return "Cơ sở dữ liệu bài giảng hiện đang rỗng."

        lines: list[str] = []
        for d in store.docs.values():
            meta = getattr(d, "metadata", {})
            course = meta.get("course", "AIPwP")
            week = meta.get("week", "-")
            lines.append(f"{d.doc_id} | {course} | Tuần {week} | {d.title}")

        return "\n".join(lines)
    except Exception as error:
        log.exception("Lỗi list_documents: %s", error)
        return f"Lỗi khi đọc danh sách tài liệu: {error}"


@mcp.tool()
def search_lesson_plan(
    query: str,
    week: int = 0,
    top_k: int = 3,
) -> str:
    """
    Tìm kiếm các đoạn trích bài giảng liên quan bằng thuật toán Hybrid Search (BM25 + Dense vector).
    - Tham số 'query': Câu truy vấn kiến thức cần tìm kiếm.
    - Tham số 'week': Tuần học cần lọc (từ 1 đến 6, nếu là 0 sẽ tìm trên toàn bộ giáo trình).
    - Tham số 'top_k': Số lượng đoạn trích tối đa trả về (mặc định 3).
    BẮT BUỘC dùng tool này cho mọi câu hỏi học tập, không tự bịa câu trả lời từ trí nhớ.
    """
    try:
        filters = {}
        if week > 0:
            filters["week"] = week

        top_k = max(1, min(top_k, 5))
        hits = search(query=query, top_k=top_k, filters=filters)

        if not hits:
            return "Không tìm thấy đoạn thông tin nào liên quan trong tài liệu bài giảng."

        results: list[str] = []
        for h in hits:
            meta = getattr(h, "metadata", {})
            header = f"[{h.doc_id}] (Độ tương đồng: {h.score:.3f} | Tuần {meta.get('week', '-')})"
            results.append(f"{header}\n{h.content}")

        return "\n\n---\n\n".join(results)
    except Exception as error:
        log.exception("Lỗi search_lesson_plan: %s", error)
        return f"Lỗi khi tìm kiếm bài giảng: {error}"


@mcp.tool()
def get_document_detail(doc_id: str) -> str:
    """
    Đọc toàn văn một bài giảng theo mã tài liệu doc_id (ví dụ: 'AIPwP-W01', 'AIPwP-W06').
    Dùng sau khi tìm kiếm nếu cần nắm trọn vẹn ngữ cảnh của cả bài học để tổng hợp hoặc so sánh.
    """
    try:
        clean_id = doc_id.strip()
        store, _, _ = get_loaded_store()
        doc = store.docs.get(clean_id)

        if not doc:
            return f"Không tìm thấy tài liệu có mã doc_id='{clean_id}'."

        text = doc.content
        if len(text) > 4000:
            text = text[:4000] + "\n\n[...Đã cắt bớt do quá dài, hãy dùng search_lesson_plan để tra cứu mục cụ thể...]"

        return f"=== {doc.title} ({doc.doc_id}) ===\n\n{text}"
    except Exception as error:
        log.exception("Lỗi get_document_detail: %s", error)
        return f"Lỗi khi lấy tài liệu '{doc_id}': {error}"


# ==============================================================================
# CÁC TOOL THAY ĐỔI TRẠNG THÁI & KIỂM CHỨNG (SIDE-EFFECT & VERIFICATION)
# ==============================================================================

@mcp.tool()
def add_study_note(topic: str, content: str, week: int = 0) -> str:
    """
    [TOOL GHI - SIDE EFFECT] Lưu lại một ghi chú học tập hoặc lời nhắc ôn tập của sinh viên vào hệ thống.
    - Tham số 'topic': Chủ đề cần ghi nhớ (ví dụ: 'Tuple bất biến', 'Cấu trúc BM25').
    - Tham số 'content': Nội dung chi tiết cần lưu ý.
    - Tham số 'week': Tuần học liên quan (từ 1 đến 6).
    Sau khi gọi tool này, BẮT BUỘC phải gọi tool đọc 'get_study_notes' để kiểm tra lại trước khi ra Final Answer.
    """
    try:
        if not topic.strip():
            return "Lỗi: Chủ đề (topic) không được để trống."

        notes_data: list[dict] = []
        if NOTES_PATH.exists():
            try:
                notes_data = json.loads(NOTES_PATH.read_text(encoding="utf-8"))
            except Exception:
                notes_data = []

        note_id = f"note_{len(notes_data) + 1:03d}"
        new_note = StudyNote(
            note_id=note_id,
            topic=topic.strip(),
            content=content.strip(),
            week=week,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )
        notes_data.append(asdict(new_note))

        NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
        NOTES_PATH.write_text(json.dumps(notes_data, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("Đã lưu ghi chú mới: %s", note_id)

        return f"Đã lưu thành công ghi chú [{note_id}]: '{topic}'. Hãy gọi tool get_study_notes để kiểm tra lại."
    except Exception as error:
        log.exception("Lỗi add_study_note: %s", error)
        return f"Lỗi khi lưu ghi chú: {error}"


@mcp.tool()
def get_study_notes() -> str:
    """
    [TOOL ĐỌC - VERIFY] Đọc lại danh sách toàn bộ các ghi chú ôn tập đã được lưu trên hệ thống.
    Dùng để kiểm chứng sau khi thêm ghi chú mới (hoặc xem lại kế hoạch học tập cá nhân).
    """
    try:
        if not NOTES_PATH.exists():
            return "Chưa có ghi chú học tập nào được lưu trên hệ thống."

        notes_data = json.loads(NOTES_PATH.read_text(encoding="utf-8"))
        if not notes_data:
            return "Danh sách ghi chú học tập hiện đang rỗng."

        lines: list[str] = [f"Danh sách {len(notes_data)} ghi chú học tập hiện có:"]
        for note in notes_data:
            week_str = f"Tuần {note.get('week')}" if note.get("week") else "Chung"
            lines.append(f"- [{note.get('note_id')}] ({week_str}) {note.get('topic')}: {note.get('content')}")

        return "\n".join(lines)
    except Exception as error:
        log.exception("Lỗi get_study_notes: %s", error)
        return f"Lỗi khi đọc ghi chú: {error}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
