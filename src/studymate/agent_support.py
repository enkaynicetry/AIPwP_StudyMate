import json
import re
import sys
from typing import Any
from studymate.models import ParsedReply

# Đảm bảo hiển thị tiếng Việt trên terminal Windows không bị lỗi mã hóa
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Template System Prompt theo phong cách ReAct (Reasoning + Acting)
REACT_SYSTEM_PROMPT = """You are StudyMate, an AI Academic Assistant for HCMUTE students studying AI Programming with Python (AIPwP).
You must solve problems step by step using the ReAct (Reasoning + Acting) pattern.
At each step, write your Thought, then execute exactly ONE Action in this format:

Thought: <what you are reasoning about>
Action: <tool_name>(<json_arguments>)

When you have found the answer or concluded your task, finish with:
Final Answer: <your grounded answer with source citations [doc_id] or clear refusal if not found>

AVAILABLE TOOLS:
{tools_doc}

STRICT GROUNDING & BEHAVIOR RULES:
1. Grounding: Answer ONLY based on information returned in Observations from tools. Never invent facts from memory.
2. Search First: For any course-related question, you MUST search the lesson plans first before answering.
3. Citations: Always cite the source document id in your final answer (e.g., "[AIPwP-W01]").
4. Refusal: If the searched documents do not contain the answer, or if the question is out of scope (e.g. topics not taught in the course), your final answer MUST clearly state that the materials do not have this information, using the prefix marker: [NO_ANSWER:NOT_IN_CORPUS] followed by a polite explanation.
5. Action & Verification: When asked to add or save a study note, first call the write tool (add_study_note), then immediately call the read tool (get_study_notes) to verify the note before giving your Final Answer.
6. Language: If the user asks in Vietnamese, reply in fluent, natural Vietnamese. If the user asks in English, reply in English.
7. Efficiency: Do not call search_lesson_plan multiple times with repetitive queries. If the observation contains sufficient facts to answer the question, proceed directly to Final Answer without making redundant tool calls.
"""

def format_tools_doc(tools_list: list[Any]) -> str:
    """Tạo chuỗi tài liệu mô tả công cụ động (Dynamic Tool Discovery)."""
    tools_doc_lines: list[str] = []
    for t in tools_list:
        schema = getattr(t, "input_schema", {})
        properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
        required = schema.get("required", []) if isinstance(schema, dict) else []

        params = []
        for k, v in properties.items():
            param_type = v.get("type", "any")
            is_req = "*" if k in required else ""
            params.append(f"{k}: {param_type}{is_req}")

        params_str = ", ".join(params)
        desc = getattr(t, "description", "") or "Không có mô tả"
        tools_doc_lines.append(f"- {t.name}({{{params_str}}}): {desc}")

    return "\n".join(tools_doc_lines)

def parse_reply(reply: str) -> ParsedReply:
    """
    Phân tích cú pháp câu trả lời của model theo chuẩn ReAct:
    - Bóc tách 'Final Answer: ...'
    - Bóc tách 'Action: tool_name({...})' (xử lý an toàn khi thiếu dấu ngoặc đóng hoặc JSON lỏng)
    """
    # 1. Cắt bỏ nếu model tự sinh Observation (phòng ngừa hallucination)
    clean_reply = reply.split("Observation:")[0].strip()

    # 2. Kiểm tra Final Answer
    final_match = re.search(r"Final Answer:\s*(.+)", clean_reply, flags=re.IGNORECASE | re.DOTALL)
    if final_match:
        return ParsedReply(kind="final", text=final_match.group(1).strip())

    # 3. Kiểm tra Action: tool_name(...)
    # Ngoặc đóng ')' là tùy chọn để model thiếu ngoặc vẫn bóc tách được
    action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)\s*\((.*)\)?", clean_reply, flags=re.IGNORECASE | re.DOTALL)
    if action_match:
        tool_name = action_match.group(1).strip()
        raw_args = action_match.group(2).strip().rstrip(")")

        args_dict: dict[str, Any] = {}
        if raw_args:
            try:
                # Trường hợp 1: JSON chuẩn
                args_dict = json.loads(raw_args)
            except Exception:
                try:
                    # Trường hợp 2: JSON thiếu ngoặc kép quanh key (vd: {query: "..."})
                    fixed = re.sub(r'([{,]\s*)([a-zA-Z_]\w*)\s*:', r'\1"\2":', raw_args)
                    fixed = fixed.replace("'", '"')
                    args_dict = json.loads(fixed)
                except Exception:
                    # Trường hợp 3: Tham số dạng key=val (vd: doc_id='AIPwP-W01')
                    if "=" in raw_args and not raw_args.startswith("{"):
                        k, v = raw_args.split("=", 1)
                        args_dict = {k.strip(): v.strip().strip("\"'")}
                    else:
                        # Trường hợp 4: Tham số chuỗi trần
                        clean_str = raw_args.strip("\"'")
                        if tool_name in ["get_document", "get_document_detail"]:
                            args_dict = {"doc_id": clean_str}
                        else:
                            args_dict = {"query": clean_str}

        return ParsedReply(kind="action", name=tool_name, args=args_dict)

    # 4. Định dạng không hợp lệ
    return ParsedReply(
        kind="invalid",
        error="Không tìm thấy định dạng 'Action: tool_name({...})' hoặc 'Final Answer: <kết luận>'."
    )

if __name__ == "__main__":
    print("=== KIỂM THỬ BỘ HỖ TRỢ AGENT_SUPPORT ===")
    test_1 = parse_reply("Thought: Cần tìm kiếm\nAction: search_lesson_plan({\"query\": \"ReAct agent\"})")
    print("1. Action chuẩn JSON:", test_1.kind, test_1.name, test_1.args)

    test_2 = parse_reply("Thought: Cần đọc tài liệu\nAction: get_document(doc_id='AIPwP-W01'")
    print("2. Action dạng key=val & thiếu ngoặc đóng:", test_2.kind, test_2.name, test_2.args)

    test_3 = parse_reply("Thought: Đã có đủ dữ liệu\nFinal Answer: Khái niệm tuple nằm trong bài giảng [AIPwP-W01].")
    print("3. Final Answer:", test_3.kind, test_3.text)
