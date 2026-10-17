import asyncio
import json
import re
import sys
from typing import Any

from studymate.agent import run_agent
from studymate.models import AgentRun

# Đảm bảo hiển thị tiếng Việt trên terminal Windows không bị lỗi mã hóa
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


BANNER = """======================================================================
  🎓 STUDYMATE — TRỢ LÝ HỌC TẬP AI PROGRAMMING WITH PYTHON (AIPwP) 🎓
======================================================================
Nhập câu hỏi của bạn (hoặc gõ 'exit'/'quit'/'q' để thoát)."""


def format_trace_step(step_data: dict[str, Any], obs_text: str | None = None) -> str:
    """Định dạng 1 bước suy luận ReAct (Thought -> Action -> Observation)."""
    reply = step_data.get("reply", "")
    lines: list[str] = [f"  [Bước {step_data.get('step', '?')}]"]

    # Bóc tách Thought
    thought_match = re.search(
        r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)",
        reply,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if thought_match:
        thought_str = thought_match.group(1).strip()
        lines.append(f"    Thought: {thought_str}")

    kind = step_data.get("parsed_kind")
    if kind == "action":
        tool_name = step_data.get("parsed_name", "")
        tool_args = step_data.get("parsed_args", {})
        args_str = json.dumps(tool_args, ensure_ascii=False)
        lines.append(f"    Action: {tool_name}({args_str})")
        if obs_text is not None:
            clean_obs = obs_text.strip()
            if len(clean_obs) > 400:
                clean_obs = clean_obs[:400] + "\n    [...Đã cắt bớt cho gọn...]"
            indented_obs = "\n    ".join(clean_obs.splitlines())
            lines.append(f"    Observation: {indented_obs}")
    elif kind == "final":
        lines.append("    Final Answer: (Hoàn tất kết luận)")
    elif kind == "invalid":
        lines.append(f"    Phản hồi không chuẩn ReAct: {reply[:120]}...")

    return "\n".join(lines)


def print_trace(trace: list[dict[str, Any]], observations: list[str]) -> None:
    """In chi tiết toàn bộ vết suy luận nếu bật cờ --verbose."""
    print("\n" + "-" * 70)
    print(" 🔍 VẾT SUY LUẬN TỪNG BƯỚC (REACT TRACE):")
    print("-" * 70)
    obs_idx = 0
    for s in trace:
        curr_obs = None
        if s.get("parsed_kind") == "action":
            if obs_idx < len(observations):
                curr_obs = observations[obs_idx]
                obs_idx += 1
        print(format_trace_step(s, curr_obs))
    print("-" * 70 + "\n")


def display_agent_result(result: AgentRun, verbose: bool = False) -> None:
    """Hiển thị kết quả trả về từ Agent gồm vết suy luận, câu trả lời và thống kê token."""
    if verbose and result.trace:
        print_trace(result.trace, result.observations)

    total_tokens_str = f"{result.usage.total_tokens:,}"
    step_count = len(result.trace)

    print("\n[StudyMate]")
    print(result.answer)
    print("-" * 70)
    print(f"(Suy luận: {step_count} bước | Tiêu thụ: {total_tokens_str} tokens)")


def run_single_question(question: str, verbose: bool = False) -> None:
    """Chạy trực tiếp 1 câu hỏi truyền vào từ dòng lệnh."""
    clean_q = question.strip()
    if not clean_q:
        print("Lỗi: Câu hỏi không được để trống.")
        return

    print(f"\n[Sinh viên] > {clean_q}")
    print("⏳ StudyMate đang suy luận qua bài giảng...")

    result = asyncio.run(run_agent(question=clean_q, max_steps=10))
    display_agent_result(result, verbose=verbose)


def start_interactive_cli(verbose: bool = False) -> None:
    """Vòng lặp Chat REPL tương tác trực tiếp với sinh viên trên Terminal."""
    print(BANNER)
    if verbose:
        print("💡 Chế độ VERBOSE đang bật: Toàn bộ Thought/Action/Observation sẽ được hiển thị.")

    while True:
        try:
            user_input = input("\n[Sinh viên] > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nCảm ơn bạn đã sử dụng StudyMate! Chúc bạn học tốt! 🎓")
            break

        if not user_input:
            print("Vui lòng nhập câu hỏi hoặc gõ 'exit' để thoát.")
            continue

        if user_input.lower() in ["exit", "quit", "q"]:
            print("\nCảm ơn bạn đã sử dụng StudyMate! Chúc bạn học tốt môn AIPwP! 🎓")
            break

        print("⏳ StudyMate đang suy luận qua bài giảng...")
        try:
            result = asyncio.run(run_agent(question=user_input, max_steps=10))
            display_agent_result(result, verbose=verbose)
        except Exception as err:
            print(f"\n[Lỗi hệ thống] Không thể hoàn thành suy luận: {err}")


DEMO_SCENARIOS = [
    {
        "tier": "TẦNG 1: TRA CỨU TRỰC TIẾP (DIRECT RETRIEVAL)",
        "goal": "Tìm kiếm bài giảng Tuần 1, phân biệt Mutable vs Immutable và trích dẫn chuẩn [AIPwP-W01].",
        "question": "Tuple và List trong Python khác nhau như thế nào và nằm ở bài học tuần mấy?",
    },
    {
        "tier": "TẦNG 2: TỪ CHỐI NGOÀI PHẠM VI (GROUNDED REFUSAL)",
        "goal": "Phát hiện chủ đề không có trong giáo trình và từ chối rõ ràng với nhãn [NO_ANSWER:NOT_IN_CORPUS].",
        "question": "Kiến thức về lập trình vi điều khiển STM32 nằm ở bài học tuần mấy?",
    },
    {
        "tier": "TẦNG 3: HÀNH ĐỘNG GHI & ĐỌC KIỂM CHỨNG (ACTION & VERIFICATION)",
        "goal": "Gọi tool ghi add_study_note, kích hoạt Guard Verify tự động gọi tool đọc get_study_notes để kiểm chứng trước khi kết luận.",
        "question": "Hãy lưu ghi chú ôn tập: Cần nhớ sự khác nhau giữa Dense vector và BM25 cho bài học Tuần 4.",
    },
]


def run_demo(verbose: bool = False) -> None:
    """
    Chạy kịch bản Demo tự động minh họa 3 tầng năng lực của đề tài T3 theo rubric chấm điểm:
    1. Direct Retrieval: Tìm đúng bài giảng, phân tích chuẩn và trích dẫn.
    2. Refusal: Từ chối câu hỏi ngoài giáo trình với nhãn [NO_ANSWER:NOT_IN_CORPUS].
    3. Action & Verify: Ghi dữ liệu và tự động kiểm chứng trước khi trả lời.
    """
    print("\n" + "=" * 70)
    print("  🚀 KHỞI CHẠY KỊCH BẢN DEMO TỰ ĐỘNG 3 TẦNG NĂNG LỰC (STUDYMATE) 🚀")
    print("=" * 70)
    print(f"Tổng số kịch bản: {len(DEMO_SCENARIOS)}")
    if verbose:
        print("Chế độ: VERBOSE (Hiển thị chi tiết vết suy luận)")
    print("=" * 70)

    for idx, item in enumerate(DEMO_SCENARIOS, 1):
        print(f"\n{'#' * 70}")
        print(f" KỊCH BẢN {idx}/{len(DEMO_SCENARIOS)}: {item['tier']}")
        print(f" Mục tiêu: {item['goal']}")
        print(f"{'#' * 70}")
        print(f"\n[Sinh viên] > {item['question']}")
        print("⏳ StudyMate đang suy luận qua bài giảng...")

        try:
            result = asyncio.run(run_agent(question=item["question"], max_steps=10))
            display_agent_result(result, verbose=verbose)
        except Exception as err:
            print(f"\n[Lỗi kịch bản {idx}]: {err}")

    print("\n" + "=" * 70)
    print("  🎉 HOÀN THÀNH TOÀN BỘ KỊCH BẢN DEMO 3 TẦNG CỦA STUDYMATE 🎉")
    print("=" * 70 + "\n")


def main() -> None:
    """Hàm main dự phòng gọi sang entrypoint chính."""
    from studymate.main import main as _main
    _main()
