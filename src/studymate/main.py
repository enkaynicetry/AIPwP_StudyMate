import argparse
import sys
from pathlib import Path

# Đảm bảo import được package studymate khi chạy trực tiếp file hoặc qua make
PROJECT_ROOT = Path(__file__).resolve().parents[2]
src_dir = str(PROJECT_ROOT / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from studymate.cli import run_demo, run_single_question, start_interactive_cli


def main() -> None:
    # Đảm bảo hiển thị tiếng Việt trên terminal Windows không bị lỗi font
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="StudyMate — Trợ lý học tập môn AI Programming with Python (AIPwP)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Chạy kịch bản demo 3 tầng tự động theo rubric chấm điểm",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Hiển thị chi tiết các bước suy luận Thought/Action/Observation (ReAct Trace)",
    )
    parser.add_argument(
        "question",
        nargs="?",
        type=str,
        default=None,
        help="Câu hỏi trực tiếp (nếu có)",
    )

    args = parser.parse_args()

    if args.demo:
        run_demo(verbose=args.verbose)
    elif args.question:
        run_single_question(args.question, verbose=args.verbose)
    else:
        start_interactive_cli(verbose=args.verbose)


if __name__ == "__main__":
    main()
