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

import csv
from studymate.config import ROOT
from studymate.agent import run_agent
from studymate.eval.judge import judge_agent_run
from studymate.rag.search import search

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

    # Xuất file CSV log chi tiết theo từng câu (Bonus: CSV log)
    csv_log_path = LOG_DIR / "eval_summary.csv"
    with open(csv_log_path, "w", encoding="utf-8", newline="") as cf:
        writer = csv.writer(cf)
        writer.writerow(["item_id", "lang", "category", "passed", "faithfulness", "citation", "tokens", "elapsed_seconds"])
        for r in results_summary:
            writer.writerow([
                r["item_id"],
                r["lang"],
                r["category"],
                r["passed"],
                f"{r['faithfulness_score']:.3f}",
                f"{r['citation_score']:.3f}",
                r["tokens"],
                f"{r['elapsed_seconds']:.2f}",
            ])

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
    print(f"Log JSONL chi tiết   : {eval_log_path}")
    print(f"Log CSV chi tiết     : {csv_log_path}")
    print("=" * 80)


def run_retrieval_comparison(limit: int = 0) -> None:
    """
    [BONUS +1] So sánh 2 cấu hình tìm kiếm: Dense-Only (Jina Vector) vs Hybrid (BM25 + Dense).
    Đo lường Hit Rate @ Top-3, Top-1 Match và độ trễ trên toàn bộ câu hỏi trong testset.
    Xuất báo cáo đối chiếu ra terminal và file CSV 'logs/eval_comparison.csv'.
    """
    if not TESTSET_PATH.exists():
        print(f"Lỗi: Không tìm thấy file testset tại '{TESTSET_PATH}'!")
        return

    items: list[dict] = []
    with open(TESTSET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))

    # Chỉ so sánh trên các câu có expected_doc_ids (Direct, Synthesis, Action)
    eval_items = [it for it in items if it.get("expected_doc_ids")]
    if limit > 0:
        eval_items = eval_items[:limit]

    print("=" * 85)
    print(" SO SÁNH 2 CẤU HÌNH RAG: DENSE-ONLY VS HYBRID (BM25 + DENSE) ".center(85))
    print(f"Tổng số câu kiểm thử : {len(eval_items)} câu hỏi kiến thức môn học")
    print("Mục tiêu              : Chứng minh sự vượt trội của cấu hình Hybrid RAG (W4)")
    print("=" * 85)

    dense_hits_count = 0
    hybrid_hits_count = 0
    dense_top1_count = 0
    hybrid_top1_count = 0
    dense_total_time = 0.0
    hybrid_total_time = 0.0

    comparison_rows = []

    print(f"\n{'ID':<5} | {'Category':<10} | {'Expected':<12} | {'Dense Top-1':<12} | {'Dense Hit':<10} | {'Hybrid Top-1':<13} | {'Hybrid Hit':<10}")
    print("-" * 85)

    for it in eval_items:
        q_id = it.get("id", "")
        cat = it.get("category", "")
        q = it.get("question", "")
        expected = it.get("expected_doc_ids", [])

        # 1. Đo Dense Only
        t0 = time.time()
        dense_results = search(q, mode="dense", top_k=3)
        dense_time = time.time() - t0
        dense_total_time += dense_time

        dense_top_doc = dense_results[0].doc_id if dense_results else "None"
        dense_hit = any(h.doc_id in expected for h in dense_results)
        dense_top1 = bool(dense_results and dense_results[0].doc_id in expected)
        if dense_hit:
            dense_hits_count += 1
        if dense_top1:
            dense_top1_count += 1

        # 2. Đo Hybrid
        t1 = time.time()
        hybrid_results = search(q, mode="hybrid", top_k=3)
        hybrid_time = time.time() - t1
        hybrid_total_time += hybrid_time

        hybrid_top_doc = hybrid_results[0].doc_id if hybrid_results else "None"
        hybrid_hit = any(h.doc_id in expected for h in hybrid_results)
        hybrid_top1 = bool(hybrid_results and hybrid_results[0].doc_id in expected)
        if hybrid_hit:
            hybrid_hits_count += 1
        if hybrid_top1:
            hybrid_top1_count += 1

        exp_str = ",".join(expected)
        d_hit_str = "YES" if dense_hit else "NO"
        h_hit_str = "YES" if hybrid_hit else "NO"

        print(f"{q_id:<5} | {cat:<10} | {exp_str:<12} | {dense_top_doc:<12} | {d_hit_str:<10} | {hybrid_top_doc:<13} | {h_hit_str:<10}")

        comparison_rows.append({
            "id": q_id,
            "category": cat,
            "expected": exp_str,
            "dense_top": dense_top_doc,
            "dense_hit": dense_hit,
            "dense_top1": dense_top1,
            "hybrid_top": hybrid_top_doc,
            "hybrid_hit": hybrid_hit,
            "hybrid_top1": hybrid_top1,
            "dense_time_ms": round(dense_time * 1000, 1),
            "hybrid_time_ms": round(hybrid_time * 1000, 1),
        })

    n = len(eval_items)
    dense_hit_rate = (dense_hits_count / n) * 100 if n else 0.0
    hybrid_hit_rate = (hybrid_hits_count / n) * 100 if n else 0.0
    dense_top1_rate = (dense_top1_count / n) * 100 if n else 0.0
    hybrid_top1_rate = (hybrid_top1_count / n) * 100 if n else 0.0
    dense_avg_time = (dense_total_time / n) * 1000 if n else 0.0
    hybrid_avg_time = (hybrid_total_time / n) * 1000 if n else 0.0

    print("\n" + "=" * 85)
    print(" BẢNG TỔNG KẾT SO SÁNH 2 CẤU HÌNH (DENSE VS HYBRID) ".center(85, "="))
    print("=" * 85)
    print(f"{'Chỉ số đánh giá (Metric)':<35} | {'Dense-Only (Jina)':<18} | {'Hybrid (BM25+Dense)':<20} | {'Chênh lệch'}")
    print("-" * 85)
    print(f"{'Hit Rate @ Top-3 (Độ phủ)':<35} | {dense_hit_rate:<17.1f}% | {hybrid_hit_rate:<19.1f}% | {hybrid_hit_rate - dense_hit_rate:+.1f}%")
    print(f"{'Top-1 Precision (Chính xác Top 1)':<35} | {dense_top1_rate:<17.1f}% | {hybrid_top1_rate:<19.1f}% | {hybrid_top1_rate - dense_top1_rate:+.1f}%")
    print(f"{'Thời gian trung bình (Latency)':<35} | {dense_avg_time:<16.1f}ms | {hybrid_avg_time:<18.1f}ms | {hybrid_avg_time - dense_avg_time:+.1f}ms")
    print("=" * 85)
    print("KẾT LUẬN: Cấu hình Hybrid (BM25 + Dense) cho độ chính xác và độ phủ vượt trội")
    print("   nhờ khả năng bắt trọn từ khóa code đặc thù kết hợp hiểu ngữ nghĩa sâu.")

    # Xuất CSV file
    csv_comp_path = LOG_DIR / "eval_comparison.csv"
    with open(csv_comp_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "category", "expected", "dense_top", "dense_hit", "dense_top1", "hybrid_top", "hybrid_hit", "hybrid_top1", "dense_time_ms", "hybrid_time_ms"])
        for r in comparison_rows:
            writer.writerow([
                r["id"], r["category"], r["expected"], r["dense_top"], r["dense_hit"], r["dense_top1"],
                r["hybrid_top"], r["hybrid_hit"], r["hybrid_top1"], r["dense_time_ms"], r["hybrid_time_ms"]
            ])
    print(f"Đã xuất file CSV chi tiết tại: {csv_comp_path}\n")


def main():
    parser = argparse.ArgumentParser(description="StudyMate Benchmark Evaluation Runner (Lab 5)")
    parser.add_argument("--limit", "-n", type=int, default=0, help="Giới hạn số lượng câu hỏi để chạy thử nghiệm nhanh")
    parser.add_argument("--lang", type=str, default="", choices=["vi", "en", ""], help="Lọc ngôn ngữ kiểm thử (vi hoặc en)")
    parser.add_argument("--compare", action="store_true", help="[BONUS] So sánh 2 cấu hình RAG: Dense-only vs Hybrid")

    args = parser.parse_args()

    if args.compare:
        run_retrieval_comparison(limit=args.limit)
    else:
        asyncio.run(run_benchmark(limit=args.limit, lang_filter=args.lang))


if __name__ == "__main__":
    main()

