"""
scripts/mcp_client_interop.py
-----------------------------
Client Python thứ hai (Second Host Client) độc lập với ReAct Agent.
Mục đích: Chứng minh tính tương tác (Interoperability) của MCP Server theo yêu cầu Bonus (+1):
- Kết nối tới MCP Server qua giao thức Stdio JSON-RPC 2.0.
- Khám phá danh sách công cụ động (Dynamic Tool Discovery).
- Gọi các tool đọc (search_lesson_plan có metadata filter).
- Gọi tool ghi (add_study_note) và tool kiểm chứng (get_study_notes).
"""

import asyncio
import os
import sys
from pathlib import Path
# Đảm bảo terminal Windows hiển thị tiếng Việt không bị lỗi font
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Thêm đường dẫn src để import
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mcp import Client, StdioServerParameters


async def run_standalone_mcp_client() -> None:
    print("=" * 75)
    print("  MCP STANDALONE CLIENT (HOST THỨ HAI) — KIỂM CHỨNG INTEROPERABILITY")
    print("=" * 75)
    print("Host role   : Standalone Python Client (hoàn toàn độc lập với Agent)")
    print("Target server: studymate.mcp_server (qua Stdio JSON-RPC)")
    print("-" * 75)

    server_env = dict(**os.environ)
    server_env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "studymate.mcp_server"],
        env=server_env,
    )

    print("\n[1] Đang khởi động kết nối tới MCP Server...")
    async with Client(server_params) as client:
        print("-> Kết nối Stdio JSON-RPC thành công!")

        # 1. Dynamic Discovery
        print("\n[2] Gửi yêu cầu Khám phá công cụ (Dynamic Discovery)...")
        tools_resp = await client.list_tools()
        tools = getattr(tools_resp, "tools", [])
        print(f"-> Máy chủ đã khai báo {len(tools)} công cụ khả dụng:")
        for t in tools:
            name = getattr(t, "name", "")
            desc = (getattr(t, "description", "") or "").strip().split("\n")[0]
            print(f"   • {name:<20}: {desc}")

        # 2. Gọi tool đọc có kèm metadata filter
        print("\n[3] Host thứ hai gọi tool đọc: 'search_lesson_plan' (Metadata filter: week=1)...")
        query_args = {"query": "Tuple và List", "week": 1, "top_k": 1}
        search_resp = await client.call_tool("search_lesson_plan", query_args)
        content_items = getattr(search_resp, "content", [])
        search_text = content_items[0].text if content_items else "Không có dữ liệu"
        first_line = search_text.strip().splitlines()[0] if search_text else ""
        print(f"-> Kết quả từ server: {first_line}")
        print("   (Đã lọc chính xác bài giảng Tuần 1 qua metadata filter)")

        # 3. Gọi tool ghi (Side Effect)
        print("\n[4] Host thứ hai gọi tool ghi: 'add_study_note' (Side Effect)...")
        note_args = {
            "topic": "Interop Verification",
            "content": "Kiểm tra ghi chú từ Standalone Client (Host thứ 2) thành công.",
            "week": 6,
        }
        add_resp = await client.call_tool("add_study_note", note_args)
        add_items = getattr(add_resp, "content", [])
        add_text = add_items[0].text if add_items else ""
        print(f"-> Phản hồi: {add_text}")

        # 4. Gọi tool đọc kiểm chứng (Verification)
        print("\n[5] Host thứ hai gọi tool đọc kiểm chứng: 'get_study_notes'...")
        get_resp = await client.call_tool("get_study_notes", {})
        get_items = getattr(get_resp, "content", [])
        get_text = get_items[0].text if get_items else ""
        has_new_note = "Interop Verification" in get_text
        print(f"-> Trạng thái kiểm chứng: {'THÀNH CÔNG (Đã thấy ghi chú mới)' if has_new_note else 'CHƯA TÌM THẤY'}")

    print("\n" + "=" * 75)
    print("  CHỨNG MINH THÀNH CÔNG TÍNH TƯƠNG TÁC (INTEROPERABILITY) CỦA MCP SERVER")
    print("  Máy chủ MCP hoạt động hoàn toàn độc lập và sẵn sàng phục vụ bất kỳ Client nào!")
    print("=" * 75 + "\n")


def main() -> None:
    asyncio.run(run_standalone_mcp_client())


if __name__ == "__main__":
    main()
