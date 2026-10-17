import asyncio
import sys
from pathlib import Path

# Đảm bảo hiển thị tiếng Việt trên terminal Windows không bị lỗi mã hóa
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Thêm đường dẫn src để import được module studymate
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from studymate.agent_support import parse_reply
from studymate.agent import run_agent

def test_parse_reply_cases():
    # Case A: Action chuẩn JSON
    res_a = parse_reply('Thought: Cần tìm kiếm\nAction: search_lesson_plan({"query": "tuple", "top_k": 2})')
    if res_a.kind != "action" or res_a.name != "search_lesson_plan" or res_a.args.get("query") != "tuple":
        print("Lỗi: Case A (JSON chuẩn) thất bại!")
        return False

    # Case B: Action thiếu dấu ngoặc kép quanh key
    res_b = parse_reply('Thought: Cần tìm kiếm\nAction: search_lesson_plan({query: "tuple", top_k: 2})')
    if res_b.kind != "action" or res_b.args.get("query") != "tuple":
        print("Lỗi: Case B (JSON thiếu nháy kép quanh key) thất bại!")
        return False

    # Case C: Action dạng key=val và thiếu dấu ngoặc đóng ')'
    res_c = parse_reply("Thought: Cần xem chi tiết\nAction: get_document_detail(doc_id='AIPwP-W01'")
    if res_c.kind != "action" or res_c.args.get("doc_id") != "AIPwP-W01":
        print("Lỗi: Case C (key=val & thiếu ngoặc đóng) thất bại!")
        return False

    # Case D: Final Answer kèm trích dẫn
    res_d = parse_reply("Thought: Đã có đủ dữ liệu\nFinal Answer: Tuple bất biến còn List có thể thay đổi [AIPwP-W01].")
    if res_d.kind != "final" or "[AIPwP-W01]" not in res_d.text:
        print("Lỗi: Case D (Final Answer) thất bại!")
        return False

    # Case E: Phản hồi không đúng cú pháp
    res_e = parse_reply("Tôi nghĩ câu trả lời là như thế này...")
    if res_e.kind != "invalid":
        print("Lỗi: Case E (Input không hợp lệ) thất bại!")
        return False

    print("-> test_parse_reply_cases: Thành công! Vượt qua cả 5 trường hợp bóc tách cú pháp.")
    return True

async def test_agent_execution():
    question = "Tuple và List trong Python khác nhau như thế nào và nằm ở bài học tuần mấy?"
    result = await run_agent(question=question, max_steps=5)

    if not result.answer:
        print("Lỗi: Agent không trả về câu trả lời!")
        return False

    if len(result.trace) == 0:
        print("Lỗi: Agent không có bước suy luận nào trong trace!")
        return False

    if "AIPwP-W01" not in result.answer and "[AIPwP" not in result.answer:
        print("Lỗi: Câu trả lời chưa chứa trích dẫn mã tài liệu rõ ràng ([AIPwP-W01])!")
        return False

    print(f"-> test_agent_execution: Thành công! Hoàn thành sau {len(result.trace)} bước suy luận, tiêu thụ {result.usage.total_tokens} tokens.")
    return True

async def main():
    print("=== BẮT ĐẦU KIỂM THỬ STUDYMATE AGENT ===")
    ok1 = test_parse_reply_cases()
    ok2 = await test_agent_execution()

    if ok1 and ok2:
        print("=== TẤT CẢ KIỂM THỬ AGENT ĐÃ VƯỢT QUA ===")
    else:
        print("=== CÓ LỖI XẢY RA TRONG QUÁ TRÌNH KIỂM THỬ AGENT ===")

if __name__ == "__main__":
    asyncio.run(main())
