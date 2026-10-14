import re
from pathlib import Path
from typing import Any
from studymate.models import Document, DocumentChunk

FRONT_MATTER_REGEX = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Tách khối YAML front-matter ở đầu file markdown thành dict metadata và body."""
    match = FRONT_MATTER_REGEX.match(text)
    if not match:
        return {}, text

    yaml_block = match.group(1)
    body = text[match.end():]

    metadata: dict[str, Any] = {}
    for line in yaml_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        
        # Chuyển số nguyên nếu có thể (như version, week)
        if val.isdigit():
            metadata[key] = int(val)
        else:
            metadata[key] = val

    return metadata, body

def chunk_markdown_text(
    body: str,
    meta: dict[str, Any],
    max_chars: int = 650,
) -> list[DocumentChunk]:
    """
    Chia nhỏ markdown theo tiêu đề (## và ###).
    Nếu đoạn nào dài hơn max_chars thì tách tiếp theo đoạn văn.
    """
    doc_id = str(meta.get("doc_id", "DOC"))
    title = str(meta.get("title", doc_id))
    source = str(meta.get("source", f"{doc_id}.md"))

    # Tách theo các heading ## hoặc ###
    pattern = re.compile(r"(?m)^(#{2,3}\s+.+)$")
    splits = pattern.split(body)

    sections: list[tuple[str, str]] = []
    current_heading = "Mở đầu"
    current_text = ""

    for part in splits:
        if pattern.match(part):
            if current_text.strip():
                sections.append((current_heading, current_text.strip()))
            current_heading = part.lstrip("#").strip()
            current_text = ""
        else:
            current_text += part

    if current_text.strip():
        sections.append((current_heading, current_text.strip()))

    chunks: list[DocumentChunk] = []
    chunk_idx = 0

    for heading, text in sections:
        if len(text) <= max_chars:
            chunk_id = f"{doc_id}_c{chunk_idx:03d}"
            c_meta = dict(meta)
            c_meta["section"] = heading
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                content=f"## {heading}\n{text}",
                doc_id=doc_id,
                title=title,
                source=source,
                chunk_index=chunk_idx,
                metadata=c_meta,
            ))
            chunk_idx += 1
        else:
            # Đoạn dài thì chia tiếp theo paragraph
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            buffer = ""
            for p in paragraphs:
                if len(buffer) + len(p) + 2 <= max_chars:
                    buffer = f"{buffer}\n\n{p}".strip()
                else:
                    if buffer:
                        chunk_id = f"{doc_id}_c{chunk_idx:03d}"
                        c_meta = dict(meta)
                        c_meta["section"] = heading
                        chunks.append(DocumentChunk(
                            chunk_id=chunk_id,
                            content=f"## {heading}\n{buffer}",
                            doc_id=doc_id,
                            title=title,
                            source=source,
                            chunk_index=chunk_idx,
                            metadata=c_meta,
                        ))
                        chunk_idx += 1
                    buffer = p
            if buffer:
                chunk_id = f"{doc_id}_c{chunk_idx:03d}"
                c_meta = dict(meta)
                c_meta["section"] = heading
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    content=f"## {heading}\n{buffer}",
                    doc_id=doc_id,
                    title=title,
                    source=source,
                    chunk_index=chunk_idx,
                    metadata=c_meta,
                ))
                chunk_idx += 1

    return chunks

def load_documents_and_chunks(data_dir: Path) -> tuple[list[Document], list[DocumentChunk]]:
    """Đọc tất cả file .md trong data_dir và tạo danh sách Document, DocumentChunk."""
    docs: list[Document] = []
    all_chunks: list[DocumentChunk] = []
    seen_doc_ids: set[str] = set()

    for md_file in sorted(data_dir.glob("*.md")):
        raw_text = md_file.read_text(encoding="utf-8")
        meta, body = parse_front_matter(raw_text)

        doc_id = str(meta.get("doc_id", md_file.stem))
        if doc_id in seen_doc_ids:
            raise ValueError(f"Trùng lặp doc_id: {doc_id} tại {md_file.name}")
        seen_doc_ids.add(doc_id)

        meta["source"] = md_file.name
        title = str(meta.get("title", doc_id))

        doc = Document(
            content=body,
            doc_id=doc_id,
            title=title,
            source=md_file.name,
            metadata=meta,
            created_at=str(meta.get("date", "")),
        )
        docs.append(doc)

        chunks = chunk_markdown_text(body, meta)
        all_chunks.extend(chunks)

    return docs, all_chunks

def validate_corpus(data_dir: Path) -> dict[str, Any]:
    """Kiểm tra và trả về thống kê số lượng doc, chunk và độ dài."""
    docs, chunks = load_documents_and_chunks(data_dir)
    lengths = [len(c.content) for c in chunks]
    return {
        "num_docs": len(docs),
        "num_chunks": len(chunks),
        "doc_ids": [d.doc_id for d in docs],
        "min_len": min(lengths) if lengths else 0,
        "avg_len": sum(lengths) // len(lengths) if lengths else 0,
        "max_len": max(lengths) if lengths else 0,
        "chunks_gt_900": sum(1 for l in lengths if l > 900),
    }
