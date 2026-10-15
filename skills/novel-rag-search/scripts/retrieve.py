"""novel-rag-search: retrieve.py
按 query + 任务域召 top-5 段落。

用法：
  python retrieve.py --index <索引目录> --query "开篇切入点" --top-k 5 --domain 开篇
"""
import argparse
import json
import sys
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
except ImportError:
    print("依赖未装：sentence-transformers / faiss-cpu / numpy", file=sys.stderr)
    sys.exit(2)


def load_index(index_dir: str):
    idx = Path(index_dir)
    index = faiss.read_index(str(idx / "index.faiss"))
    chunks = json.loads((idx / "chunks.json").read_text(encoding="utf-8"))
    config = json.loads((idx / "config.json").read_text(encoding="utf-8"))
    model = SentenceTransformer(config["model"])
    return index, chunks, config, model


def retrieve(index, chunks, model, query: str, top_k: int = 5, domain: str = None):
    q_emb = model.encode([query])
    faiss.normalize_L2(q_emb)
    D, I = index.search(np.array(q_emb, dtype="float32"), top_k * 3 if domain else top_k)
    results = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0 or idx >= len(chunks):
            continue
        c = chunks[idx]
        if domain and c["task_domain"] != domain:
            continue
        results.append({
            "text": c["text"],
            "source": c["source"],
            "task_domain": c["task_domain"],
            "score": round(float(score), 4),
        })
        if len(results) >= top_k:
            break
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--domain", help="任务域过滤（立项/大纲/开篇/人物/情节/场景/复盘/题材）")
    args = ap.parse_args()

    index, chunks, config, model = load_index(args.index)
    results = retrieve(index, chunks, model, args.query, args.top_k, args.domain)
    out = {
        "query": args.query,
        "domain": args.domain,
        "model": config["model"],
        "results": results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
