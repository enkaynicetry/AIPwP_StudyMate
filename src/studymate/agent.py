import asyncio
import os
import sys
from pathlib import Path
from typing import Any
from mcp import Client, StdioServerParameters

from studymate.config import MAX_STEPS, OBS_MAX_CHARS, ROOT
from studymate.models import AgentRun, Usage
from studymate.llm import call_llm
from studymate.agent_support import REACT_SYSTEM_PROMPT, format_tools_doc, parse_reply

# Đảm bảo hiển thị tiếng Việt trên terminal Windows không bị lỗi mã hóa
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def run_agent(
    question: str,
    max_steps: int = MAX_STEPS,
    server_module: str = "studymate.mcp_server",
) -> AgentRun:
    """
    Vòng lặp ReAct Agent kết nối với MCP Server qua kênh truyền stdio:
    1. Khởi động MCP client và khám phá tool động (list_tools).
    2. Render System Prompt và lịch sử hội thoại.
    3. Thực thi vòng lặp suy luận tối đa max_steps bước.
    4. Kiểm soát luật Verify: gọi tool ghi thì bắt buộc gọi tool đọc trước khi kết luận.
    """
    usage = Usage()
    trace: list[dict[str, Any]] = []
    observations: list[str] = []
    pending_verify = False  # Cờ theo dõi trạng thái cần verify sau khi ghi

    server_env = dict(**os.environ)
    server_env["PYTHONPATH"] = str(ROOT / "src")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", server_module],
        env=server_env,
    )

    async with Client(server_params) as client:
        # 1. Khám phá Tool động qua MCP protocol (Tuần 7)
        tools_resp = await client.list_tools()
        tools_list = getattr(tools_resp, "tools", [])
        tools_doc = format_tools_doc(tools_list)

        # 2. Xây dựng prompt và messages khởi đầu
        system_prompt = REACT_SYSTEM_PROMPT.format(tools_doc=tools_doc)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        # 3. Vòng lặp ReAct
        for step in range(1, max_steps + 1):
            reply_text = call_llm(messages=messages, usage=usage)
            parsed = parse_reply(reply_text)

            trace.append({
                "step": step,
                "reply": reply_text,
                "parsed_kind": parsed.kind,
                "parsed_name": parsed.name,
                "parsed_args": parsed.args,
            })

            # Nhánh 1: Model đưa ra Final Answer
            if parsed.kind == "final":
                # Guard Verify: Nếu vừa gọi tool ghi mà chưa gọi tool đọc để kiểm tra
                if pending_verify:
                    pending_verify = False
                    reminder = "Observation: Cảnh báo: Bạn vừa thay đổi dữ liệu ghi chú. Hãy gọi tool đọc để kiểm tra lại trước khi đưa ra Final Answer."
                    messages.append({"role": "assistant", "content": reply_text})
                    messages.append({"role": "user", "content": reminder})
                    continue

                return AgentRun(
                    answer=parsed.text,
                    trace=trace,
                    usage=usage,
                    observations=observations,
                )

            # Nhánh 2: Model yêu cầu Action
            if parsed.kind == "action":
                tool_name = parsed.name
                tool_args = parsed.args

                # Cập nhật trạng thái Guard Verify
                if "add_" in tool_name or "write_" in tool_name:
                    pending_verify = True
                elif "get_" in tool_name or "read_" in tool_name or "list_" in tool_name:
                    pending_verify = False

                obs_text = ""
                try:
                    tool_res = await client.call_tool(tool_name, tool_args)
                    contents: list[str] = []
                    for block in getattr(tool_res, "content", []):
                        if getattr(block, "text", None):
                            contents.append(block.text)
                    obs_text = "\n".join(contents) or "(Không có nội dung trả về)"
                except Exception as error:
                    obs_text = f"Lỗi thực thi tool '{tool_name}': {error}"

                # Cắt gọn observation nếu quá dài để bảo vệ context window
                if len(obs_text) > OBS_MAX_CHARS:
                    obs_text = obs_text[:OBS_MAX_CHARS] + "\n[...Nội dung đã được cắt bớt...]"

                observations.append(obs_text)
                messages.append({"role": "assistant", "content": reply_text})
                messages.append({"role": "user", "content": f"Observation: {obs_text}"})
                continue

            # Nhánh 3: Định dạng không hợp lệ -> Hướng dẫn model tự sửa
            feedback = (
                f"Observation: {parsed.error} "
                "Hãy trả lời đúng cú pháp: 'Thought: <suy nghĩ>' rồi 'Action: tool_name({{\"key\": \"val\"}})' "
                "hoặc 'Final Answer: <kết luận>'."
            )
            messages.append({"role": "assistant", "content": reply_text})
            messages.append({"role": "user", "content": feedback})

    # Nếu chạy hết số bước tối đa mà chưa kết luận
    fallback_msg = "Không thể hoàn thành câu trả lời trong giới hạn số bước cho phép."
    return AgentRun(
        answer=fallback_msg,
        trace=trace,
        usage=usage,
        observations=observations,
        error="Exceeded max steps",
    )
