import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Đảm bảo hiển thị tiếng Việt trên terminal Windows không bị lỗi mã hóa
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Thêm đường dẫn src để import được module studymate
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from studymate.config import ROOT
from studymate.agent import run_agent
from studymate.eval.judge import judge_agent_run

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
TESTSET_PATH = ROOT / "tests" / "testset.jsonl"

async def run_benchmark(limit: int = 0, lang_filter: str = ""):
    if not TESTSET_PATH.exists():
        print(f"Lỗi: Không tìm thấy file testset tại '{TESTSET_PATH}'!")
        return

    items: list[dict] = []
    with open(TESTSET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))

    if lang_filter:
        items = [it for it in items if it.get("lang") == lang_filter]

    if limit > 0:
        items = items[:limit]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    eval_log_path = LOG_DIR / f"eval_run_{timestamp}.jsonl"

    print("=" * 80)
    print(" BẮT ĐẦU ĐÁNH GIÁ BENCHMARK".center(80, "="))
    print(f"Số lượng câu hỏi: {len(items)} | Nguồn: tests/testset.jsonl")
    if lang_filter:
        print(f"Bộ lọc ngôn ngữ: {lang_filter.upper()}")
    print("=" * 80)

    results_summary: list[dict] = []
    total_tokens = 0
    total_time = 0.0

    print(f"\n{'ID':<5} | {'Lang':<5} | {'Category':<10} | {'Status':<6} | {'Faithful':<9} | {'Cites':<7} | {'Tokens':<7} | {'Time (s)':<8}")
    print("-" * 80)

    for idx, item in enumerate(items, 1):
        item_id = item.get("id", f"q{idx}")
        lang = item.get("lang", "vi").upper()
        cat = item.get("category", "direct")
        question = item.get("question", "")

        t0 = time.time()
        # Chạy agent trả lời
        agent_run = await run_agent(question=question, max_steps=6)
        elapsed = time.time() - t0

        tokens = agent_run.usage.total_tokens
        total_tokens += tokens
        total_time += elapsed

        # LLM Judge chấm điểm theo Lab 5
        judge_res = judge_agent_run(item, agent_run)

        status_str = "PASS" if judge_res.passed else "FAIL"
        faith_str = f"{judge_res.faithfulness_score:.1%}"
        cites_str = f"{judge_res.citation_score:.1%}"

        print(f"{item_id:<5} | {lang:<5} | {cat:<10} | {status_str:<6} | {faith_str:<9} | {cites_str:<7} | {tokens:<7} | {elapsed:<8.2f}", flush=True)

        record = {
            "item_id": item_id,
            "lang": lang,
            "category": cat,
            "question": question,
            "passed": judge_res.passed,
            "faithfulness_score": judge_res.faithfulness_score,
            "citation_score": judge_res.citation_score,
            "refusal_pass": judge_res.refusal_pass,
            "action_verify_pass": judge_res.action_verify_pass,
            "claims": judge_res.claims,
            "tokens": tokens,
            "elapsed_seconds": elapsed,
            "agent_answer": agent_run.answer,
            "observations_count": len(agent_run.observations),
        }
        results_summary.append(record)

        # Ghi log chi tiết từng câu
        with open(eval_log_path, "a", encoding="utf-8") as lf:
            lf.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Tổng kết bảng điểm
    total_q = len(results_summary)
    passed_q = sum(1 for r in results_summary if r["passed"])
    pass_rate = (passed_q / total_q) * 100 if total_q > 0 else 0.0

    avg_faith = (sum(r["faithfulness_score"] for r in results_summary) / total_q) * 100 if total_q > 0 else 0.0
    avg_cites = (sum(r["citation_score"] for r in results_summary) / total_q) * 100 if total_q > 0 else 0.0

    # Phân nhóm theo ngôn ngữ
    vi_runs = [r for r in results_summary if r["lang"] == "VI"]
    en_runs = [r for r in results_summary if r["lang"] == "EN"]
    vi_pass = (sum(1 for r in vi_runs if r["passed"]) / len(vi_runs) * 100) if vi_runs else 0.0
    en_pass = (sum(1 for r in en_runs if r["passed"]) / len(en_runs) * 100) if en_runs else 0.0

    print("\n" + "=" * 80)
    print(" BẢNG TỔNG KẾT ĐÁNH GIÁ CHẤT LƯỢNG (EVALUATION REPORT) ".center(80, "="))
    print("=" * 80)
    print(f"Tổng số câu kiểm thử : {total_q}")
    print(f"Số câu đạt (PASS)    : {passed_q} / {total_q} ({pass_rate:.1f}%)")
    print(f"Tỷ lệ Pass Tiếng Việt: {vi_pass:.1f}% ({len(vi_runs)} câu)")
    print(f"Tỷ lệ Pass Tiếng Anh : {en_pass:.1f}% ({len(en_runs)} câu)")
    print(f"Độ trung thực (Faith): {avg_faith:.1f}%")
    print(f"Độ trích nguồn (Cite): {avg_cites:.1f}%")
    print(f"Tổng lượng token     : {total_tokens:,} tokens")
    print(f"Thời gian trung bình : {total_time / total_q:.2f}s / câu")
    print(f"Log chi tiết lưu tại : {eval_log_path}")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="StudyMate Benchmark Evaluation Runner (Lab 5)")
    parser.add_argument("--limit", "-n", type=int, default=0, help="Giới hạn số lượng câu hỏi để chạy thử nghiệm nhanh")
    parser.add_argument("--lang", type=str, default="", choices=["vi", "en", ""], help="Lọc ngôn ngữ kiểm thử (vi hoặc en)")

    args = parser.parse_args()
    asyncio.run(run_benchmark(limit=args.limit, lang_filter=args.lang))

if __name__ == "__main__":
    main()
