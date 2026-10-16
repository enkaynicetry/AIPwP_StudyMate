import asyncio
import os
import sys
from pathlib import Path
from rich import print
from mcp import Client, StdioServerParameters

# Đảm bảo hiển thị tiếng Việt trên terminal Windows không bị lỗi mã hóa
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Thêm đường dẫn src để import được module studymate
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

async def test_mcp_discovery():
    """Kiểm tra khả năng Dynamic Tool Discovery qua MCP Client."""
    print("\n[bold blue]1. Kiểm tra Dynamic Discovery (Phát hiện công cụ qua MCP)[/bold blue]")
    
    server_env = dict(**os.environ)
    server_env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "studymate.mcp_server"],
        env=server_env,
    )

    async with Client(server_params) as client:
        tools_resp = await client.list_tools()
        tools = getattr(tools_resp, "tools", [])
        tool_names = [getattr(t, "name", "") for t in tools]

        expected_tools = [
            "list_documents",
            "search_lesson_plan",
            "get_document_detail",
            "add_study_note",
            "get_study_notes",
        ]

        all_found = True
        for exp in expected_tools:
            if exp not in tool_names:
                print(f"[red]Lỗi: Thiếu tool '{exp}' trong danh sách phát hiện![/red]")
                all_found = False

        if len(tools) != 5:
            print(f"[yellow]Cảnh báo: Số lượng tool phát hiện là {len(tools)}, kỳ vọng là 5.[/yellow]")

        if all_found:
            print(f"-> test_mcp_discovery: [green]Thành công![/green] Đã phát hiện đủ 5/5 tools:")
            for t in tools:
                doc = (getattr(t, "description", "") or "").strip().split("\n")[0]
                print(f"   + [cyan]{getattr(t, 'name', '')}[/cyan]: {doc}")

async def test_mcp_call_read_tools():
    """Kiểm tra gọi các tool đọc: list_documents, search_lesson_plan, get_document_detail."""
    print("\n[bold blue]2. Kiểm tra gọi các Tool Đọc (Read-Only Tools)[/bold blue]")

    server_env = dict(**os.environ)
    server_env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "studymate.mcp_server"],
        env=server_env,
    )

    async with Client(server_params) as client:
        # 1. Thử list_documents
        res_list = await client.call_tool("list_documents", {})
        text_list = ""
        if hasattr(res_list, "content") and res_list.content:
            text_list = getattr(res_list.content[0], "text", "")
        
        if "AIPwP-W01" not in text_list or "AIPwP-W06" not in text_list:
            print("[red]Lỗi: list_documents không trả về đủ danh sách bài giảng từ W01 đến W06![/red]")
        else:
            print("-> Gọi tool 'list_documents': [green]Thành công![/green]")

        # 2. Thử search_lesson_plan
        res_search = await client.call_tool(
            "search_lesson_plan",
            {"query": "tuple list khác nhau", "week": 1, "top_k": 2}
        )
        text_search = ""
        if hasattr(res_search, "content") and res_search.content:
            text_search = getattr(res_search.content[0], "text", "")

        if "AIPwP-W01" not in text_search:
            print("[red]Lỗi: search_lesson_plan không tìm thấy tài liệu phù hợp cho tuần 1![/red]")
        else:
            print("-> Gọi tool 'search_lesson_plan': [green]Thành công![/green] (Tìm thấy đoạn trích từ AIPwP-W01)")

        # 3. Thử get_document_detail
        res_detail = await client.call_tool("get_document_detail", {"doc_id": "AIPwP-W01"})
        text_detail = ""
        if hasattr(res_detail, "content") and res_detail.content:
            text_detail = getattr(res_detail.content[0], "text", "")

        if "Tuần 1" not in text_detail and "W01" not in text_detail:
            print("[red]Lỗi: get_document_detail không lấy được nội dung tài liệu AIPwP-W01![/red]")
        else:
            print("-> Gọi tool 'get_document_detail': [green]Thành công![/green]")

async def test_mcp_call_write_and_verify():
    """Kiểm tra gọi Tool Ghi (Side-Effect) và Tool Đọc kiểm chứng (Verify)."""
    print("\n[bold blue]3. Kiểm tra Tool Ghi và Kiểm chứng (add_study_note & get_study_notes)[/bold blue]")

    server_env = dict(**os.environ)
    server_env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "studymate.mcp_server"],
        env=server_env,
    )

    async with Client(server_params) as client:
        # 1. Ghi một note mới
        topic_test = "Ôn tập MCP Server"
        content_test = "Kiểm tra cơ chế JSON-RPC stdio và tool verify trong FinalProject StudyMate."
        res_write = await client.call_tool(
            "add_study_note",
            {"topic": topic_test, "content": content_test, "week": 6}
        )
        text_write = ""
        if hasattr(res_write, "content") and res_write.content:
            text_write = getattr(res_write.content[0], "text", "")

        if "Đã lưu thành công" not in text_write:
            print(f"[red]Lỗi: add_study_note phản hồi không như kỳ vọng! Kết quả: {text_write}[/red]")
        else:
            print(f"-> Gọi tool ghi 'add_study_note': [green]Thành công![/green]")

        # 2. Đọc lại để kiểm chứng (Verify)
        res_read = await client.call_tool("get_study_notes", {})
        text_read = ""
        if hasattr(res_read, "content") and res_read.content:
            text_read = getattr(res_read.content[0], "text", "")

        if topic_test not in text_read:
            print(f"[red]Lỗi: get_study_notes không tìm thấy ghi chú '{topic_test}' vừa lưu![/red]")
        else:
            print(f"-> Gọi tool đọc 'get_study_notes': [green]Thành công![/green] (Đã xác minh được ghi chú vừa lưu)")

async def main():
    print("=" * 65)
    print(" BẮT ĐẦU KIỂM THỬ MCP SERVER (STUDYMATE) ".center(65, "="))
    print("=" * 65)
    await test_mcp_discovery()
    await test_mcp_call_read_tools()
    await test_mcp_call_write_and_verify()
    print("\n" + "=" * 65)
    print(" HOÀN THÀNH TẤT CẢ KIỂM THỬ MCP SERVER ".center(65, "="))
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
