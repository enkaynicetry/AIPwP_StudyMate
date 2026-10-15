import sys
from pathlib import Path

# Thêm đường dẫn src để import package
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from studymate.config import DATA_DIR, INDEX_PATH, JINA_API_KEY
from studymate.rag.corpus import load_documents_and_chunks, validate_corpus
from studymate.rag.store import LessonPlanStore, embed_texts

def main():
    print(f"Đọc dữ liệu tại: {DATA_DIR}")
    stats = validate_corpus(DATA_DIR)
    print(f"- Số tài liệu: {stats['num_docs']}")
    print(f"- Tổng số chunk: {stats['num_chunks']}")
    print(f"- Độ dài chunk: min={stats['min_len']}, avg={stats['avg_len']}, max={stats['max_len']}")

    if not JINA_API_KEY:
        print("Cảnh báo: Thiếu JINA_API_KEY, bỏ qua tạo embeddings.")
        embeddings = [None] * stats['num_chunks']
    else:
        print("Đang tạo embeddings qua Jina API...")
        docs, chunks = load_documents_and_chunks(DATA_DIR)
        texts_to_embed = [c.content for c in chunks]
        embeddings = embed_texts(texts_to_embed, task="retrieval.passage", batch_size=16)
        print(f"Đã tạo {len(embeddings)} embeddings.")

    docs, chunks = load_documents_and_chunks(DATA_DIR)
    store = LessonPlanStore()
    for d in docs:
        store.add_doc(d)
    for c, emb in zip(chunks, embeddings):
        c.embedding = emb
    store.add_chunks(chunks)

    store.save(INDEX_PATH)
    print(f"Đã lưu index tại: {INDEX_PATH}")

if __name__ == "__main__":
    main()
