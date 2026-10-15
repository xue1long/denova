"""novel-rag-search: build_index.py
把语料目录 .md 切块 + 嵌入 + 建 FAISS 索引。

用法：
  python build_index.py --raw <语料目录> --out <索引输出目录>
  # 例：python build_index.py --raw E:/002-Pr/cangjie-skill-main/books/novel-writing-beginner --out ./.rag_index
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("sentence-transformers 未装。pip install sentence-transformers", file=sys.stderr)
    sys.exit(2)

try:
    import faiss
    import numpy as np
except ImportError:
    print("faiss-cpu / numpy 未装。pip install faiss-cpu numpy", file=sys.stderr)
    sys.exit(2)


# 任务域识别（按文件名关键词）
TASK_DOMAIN_KEYWORDS = {
    "立项": ["创意", "书名", "简介", "选题", "题材"],
    "大纲": ["大纲", "总纲", "细纲", "结构"],
    "开篇": ["开篇", "切入", "开头", "首章", "开章"],
    "人物": ["人物", "角色", "性格", "对白", "角色塑造"],
    "情节": ["情节", "爽点", "悬念", "冲突", "高潮"],
    "场景": ["场景", "环境", "描写", "打斗", "细节"],
    "复盘": ["复盘", "修订", "审稿", "自查", "删改"],
    "题材": ["玄幻", "仙侠", "都市", "科幻", "历史"],
}


def detect_task_domain(file_name: str) -> str:
    for domain, keywords in TASK_DOMAIN_KEYWORDS.items():
        if any(kw in file_name for kw in keywords):
            return domain
    return "其他"


def split_paragraphs_zh(text: str) -> list:
    """按空行切，保留 200-500 字的块"""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    for p in paras:
        if 200 <= len(p) <= 500:
            chunks.append(p)
        elif len(p) > 500:
            # 切到 400 字一段
            for i in range(0, len(p), 400):
                seg = p[i:i+400]
                if 200 <= len(seg):
                    chunks.append(seg)
    return chunks


def build_index(raw_dir: str, out_dir: str, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
    raw = Path(raw_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] 扫描 {raw} ...")
    md_files = list(raw.rglob("*.md"))
    print(f"  发现 {len(md_files)} 个 .md 文件")

    print(f"[2/4] 切块 ...")
    chunks = []
    for f in md_files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        domain = detect_task_domain(f.name)
        for para in split_paragraphs_zh(text):
            chunks.append({
                "text": para,
                "source": str(f.relative_to(raw)),
                "task_domain": domain,
            })
    print(f"  切得 {len(chunks)} 个块")

    if not chunks:
        print("  无可索引内容，退出", file=sys.stderr)
        sys.exit(1)

    print(f"[3/4] 嵌入（{model_name}）...")
    model = SentenceTransformer(model_name)
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    print(f"[4/4] 建 FAISS 索引 ...")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(embeddings)
    index.add(np.array(embeddings, dtype="float32"))

    faiss.write_index(index, str(out / "index.faiss"))
    (out / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "config.json").write_text(json.dumps({
        "model": model_name,
        "dim": dim,
        "chunks_count": len(chunks),
    }, ensure_ascii=False, indent=2))

    print(f"\n✓ 索引完成：{out}")
    print(f"  chunks: {len(chunks)}")
    print(f"  dim: {dim}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="语料目录")
    ap.add_argument("--out", required=True, help="索引输出目录")
    ap.add_argument("--model", default="paraphrase-multilingual-MiniLM-L12-v2")
    args = ap.parse_args()
    build_index(args.raw, args.out, args.model)


if __name__ == "__main__":
    main()
