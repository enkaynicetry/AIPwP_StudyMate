import sys
from pathlib import Path
from rich import print

# Đảm bảo hiển thị tiếng Việt trên terminal Windows không bị lỗi mã hóa
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Thêm đường dẫn src để import được module studymate
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from studymate.config import DATA_DIR
from studymate.rag.corpus import validate_corpus, parse_front_matter

SAMPLE= """---
doc_id: AIPwP-TEST
course: AIPwP
title: Bài kiểm thử mẫu
week: 1
---
# Nội dung kiểm thử
Đây là phần thân tài liệu.
"""

def test_parse_front_matter():
    meta, body = parse_front_matter(SAMPLE)
    
    if meta.get("doc_id") != "AIPwP-TEST": 
        print("Lỗi: doc_id không khớp!")
    if meta.get("course") != "AIPwP": 
        print("Lỗi: course không khớp!")
    if meta.get("week") != 1: 
        print("Lỗi: week không khớp!")
    if "Đây là phần thân tài liệu" not in body: 
        print("Lỗi: Phần thân văn bản bị thiếu!")
        
    print("-> test_parse_front_matter: Thành công!")

def test_corpus_validation():
    stats = validate_corpus(DATA_DIR)
    
    if stats["num_docs"] != 6: 
        print(f"Lỗi: Số tài liệu đọc được là {stats['num_docs']}, kỳ vọng là 6!")
    if stats["num_chunks"] <= 100: 
        print(f"Lỗi: Số chunk quá ít ({stats['num_chunks']})!")
    if "AIPwP-W01" not in stats["doc_ids"] or "AIPwP-W06" not in stats["doc_ids"]:
        print("Lỗi: Danh sách bài giảng thiếu tuần 1 hoặc tuần 6!")
        
    print(f"-> test_corpus_validation: Thành công! \n Đã nạp {stats}")

if __name__ == "__main__":
    test_parse_front_matter()
    test_corpus_validation()
