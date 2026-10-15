# novel-rag-search: 索引设计

> 包装 arojit/Retrieval-Augmented-Generation 的设计思路，适配 novel-writing-beginner 261 篇方法论文献。

## 架构

```
语料目录 → 切块 → 嵌入 → FAISS 索引
  .md
  200-500 字/段
  sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
  cosine similarity
```

## 切块策略

- 按段落切（每段 200–500 字），保留所属任务域标签（立项/大纲/开篇/人物/情节/场景/复盘/题材）
- 嵌入模型：multilingual MiniLM（中文友好、CPU 可跑）
- 索引：FAISS inner-product（cosine）

## 检索

- 输入：当前任务关键词（如"开篇切入点""人物对白""爽点排布"）
- 预过滤：按任务域
- 召 top-5 段落
- 重排序（可选）

## 嵌入脚本要点（scripts/build_index.py）

```python
from sentence_transformers import SentenceTransformer
import faiss
import os, json

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
chunks = []  # [(text, source_file, task_domain)]
for md_file in glob.glob("raw/**/*.md"):
    text = read(md_file)
    for para in split_paragraphs(text):
        if 200 <= len(para) <= 500:
            chunks.append((para, md_file, detect_task_domain(md_file)))

embeddings = model.encode([c[0] for c in chunks])
index = faiss.IndexFlatIP(embeddings.shape[1])
faiss.normalize_L2(embeddings)
index.add(embeddings)
faiss.write_index(index, "index.faiss")
json.dump(chunks, open("chunks.json", "w"), ensure_ascii=False)
```

## 检索脚本要点（scripts/retrieve.py）

```python
def retrieve(query: str, top_k: int = 5, task_domain: str = None) -> list:
    q_emb = model.encode([query])
    faiss.normalize_L2(q_emb)
    D, I = index.search(q_emb, top_k)
    results = []
    for score, idx in zip(D[0], I[0]):
        if task_domain and chunks[idx]["task_domain"] != task_domain:
            continue
        results.append({
            "text": chunks[idx]["text"],
            "source": chunks[idx]["source"],
            "task_domain": chunks[idx]["task_domain"],
            "score": float(score),
        })
    return results
```

## 与 Denova 集成

- 写章节时主 Agent 调 retrieve.py
- 把 top-5 段落塞进 `参考方法论` 上下文
- 段落保留来源文件路径（透明可审计）

## 边界

- **不抓版权小说作语料**
- **用户已合法持有的本地 .md 目录可用**（如 `novel-writing-beginner`）
- **每段必须有可追溯的 source_file 字段**
