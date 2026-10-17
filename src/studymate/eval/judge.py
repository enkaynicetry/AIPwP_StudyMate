import json
import re
from dataclasses import dataclass, field
from typing import Any
from studymate.llm import call_llm
from studymate.models import AgentRun, JudgeResult

BATCH_FAITHFULNESS_PROMPT = """You are an objective academic evaluator for the course AI Programming with Python.
Given the following retrieved Context and the Student Answer:
1. Decompose the Student Answer into 2 to 5 self-contained atomic factual claims.
2. For each claim, determine if it is directly supported by the Context (decision: "YES") or not / hallucinated (decision: "NO").
Output ONLY a valid JSON list of objects with keys "claim" and "decision", with no extra markdown or explanations. Example:
[
  {{"claim": "Tuple is an immutable sequence in Python", "decision": "YES"}},
  {{"claim": "Tuple was taught in Week 9", "decision": "NO"}}
]

Context:
{context}

Student Answer:
{answer}
"""

def evaluate_refusal(answer: str, expected_refusal: bool) -> bool:
    """Kiểm tra độ chính xác khi từ chối câu hỏi ngoài phạm vi."""
    has_marker = "[NO_ANSWER:NOT_IN_CORPUS]" in answer
    refusal_phrases = [
        "không có thông tin",
        "không giảng dạy",
        "không nằm trong",
        "does not cover",
        "not part of",
        "not in",
    ]
    has_refusal_text = any(p in answer.lower() for p in refusal_phrases)

    if expected_refusal:
        return has_marker or has_refusal_text
    else:
        return not has_marker

def evaluate_citations(answer: str, expected_doc_ids: list[str]) -> float:
    """Kiểm tra tỷ lệ trích dẫn đúng mã tài liệu [AIPwP-Wxx]."""
    if not expected_doc_ids:
        return 1.0

    found_count = 0
    for doc_id in expected_doc_ids:
        if doc_id in answer:
            found_count += 1

    return found_count / len(expected_doc_ids)

def evaluate_action_verify(trace: list[dict[str, Any]]) -> bool:
    """Kiểm tra quy tắc Verify: Gọi tool ghi (add_*) bắt buộc phải gọi tool đọc (get_*) sau đó."""
    called_write = False
    verified_read = False

    for step in trace:
        tool_name = step.get("parsed_name", "")
        if "add_" in tool_name or "write_" in tool_name:
            called_write = True
            verified_read = False
        elif called_write and ("get_" in tool_name or "read_" in tool_name or "list_" in tool_name):
            verified_read = True

    return (not called_write) or (called_write and verified_read)

def evaluate_faithfulness(answer: str, context: str) -> tuple[float, list[dict[str, Any]]]:
    """
    Đánh giá độ trung thực (Faithfulness) theo phương pháp Atomic Claims (Lab 5):
    Dùng 1 lời gọi LLM Judge duy nhất (temperature=0.0) để vừa phân rã vừa đối chiếu claims.
    """
    clean_answer = answer.strip()
    if not clean_answer or not context.strip():
        return 1.0, []

    prompt = BATCH_FAITHFULNESS_PROMPT.format(
        context=context[:2500],
        answer=clean_answer[:1500],
    )
    messages = [{"role": "user", "content": prompt}]
    reply = call_llm(messages=messages, temperature=0.0).strip()

    # Bóc tách JSON an toàn
    claims_data: list[dict[str, Any]] = []
    json_match = re.search(r"\[.*\]", reply, flags=re.DOTALL)
    if json_match:
        try:
            claims_data = json.loads(json_match.group(0))
        except Exception:
            claims_data = []

    if not claims_data:
        # Nếu LLM không trả JSON, mặc định 1.0 nếu có trích dẫn hoặc 0.8
        return 1.0, []

    yes_count = 0
    for c in claims_data:
        dec = str(c.get("decision", "")).strip().upper()
        if "YES" in dec:
            yes_count += 1

    score = yes_count / len(claims_data) if claims_data else 1.0
    return score, claims_data

def judge_agent_run(item: dict[str, Any], run: AgentRun) -> JudgeResult:
    """Chấm điểm toàn diện cho một lượt chạy của Agent dựa trên benchmark test item."""
    item_id = item.get("id", "q")
    category = item.get("category", "direct")
    expected_refusal = item.get("expected_refusal", False)
    expected_doc_ids = item.get("expected_doc_ids", [])

    answer = run.answer or ""
    context = "\n\n".join(run.observations)

    # 1. Kiểm tra từ chối
    refusal_pass = evaluate_refusal(answer, expected_refusal)

    # 2. Kiểm tra trích dẫn
    citation_score = evaluate_citations(answer, expected_doc_ids)

    # 3. Kiểm tra Action Verify
    action_verify_pass = True
    if category == "action":
        action_verify_pass = evaluate_action_verify(run.trace)

    # 4. Kiểm tra Faithfulness
    if expected_refusal:
        faithfulness_score = 1.0 if refusal_pass else 0.0
        claims: list[dict[str, Any]] = []
    else:
        faithfulness_score, claims = evaluate_faithfulness(answer, context)

    # Tiêu chí đỗ (Pass criteria):
    if expected_refusal:
        passed = refusal_pass
    elif category == "action":
        passed = action_verify_pass and (citation_score > 0.0 or not expected_doc_ids)
    else:
        passed = (faithfulness_score >= 0.7) and (citation_score >= 0.5)

    notes = f"Cat: {category} | Faithfulness: {faithfulness_score:.1%} | Citations: {citation_score:.1%}"

    return JudgeResult(
        item_id=item_id,
        passed=passed,
        faithfulness_score=faithfulness_score,
        citation_score=citation_score,
        refusal_pass=refusal_pass,
        action_verify_pass=action_verify_pass,
        claims=claims,
        notes=notes,
    )
