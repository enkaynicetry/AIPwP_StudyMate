import sys
from pathlib import Path

# Đảm bảo hiển thị tiếng Việt trên terminal Windows không bị lỗi mã hóa
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Thêm đường dẫn src để import được module studymate
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from studymate.rag.search import search

def test_hybrid_search():
    query = "ReAct agent pattern"
    results = search(query, mode="hybrid", top_k=3)
    
    if not results or len(results) == 0:
        print(f"Lỗi: Không tìm thấy kết quả nào cho truy vấn '{query}'!")
        
    top_hit = results[0]
    print(f"-> test_hybrid_search: Thành công! Tìm thấy {len(results)} kết quả. Top: [{top_hit.doc_id}] điểm={top_hit.score:.4f}")

def test_metadata_filter():
    query = "dictionary and list data structure"
    target_week = 1
    results = search(query, filters={"week": target_week}, top_k=3)
    
    if not results or len(results) == 0:
        print(f"Lỗi: Không tìm thấy kết quả nào cho tuần {target_week}!")
        
    for hit in results:
        week = hit.metadata.get("week")
        if week != target_week:
            print(f"Lỗi: Kết quả {hit.chunk_id} có week={week}, không khớp với bộ lọc week={target_week}!")
            
    print(f"-> test_metadata_filter: Thành công! Tất cả {len(results)} kết quả đều thuộc Tuần {target_week}.")

if __name__ == "__main__":
    test_hybrid_search()
    test_metadata_filter()

