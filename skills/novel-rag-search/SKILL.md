---
name: novel-rag-search
description: "通用 markdown 语料检索（RAG 模式），把任意 .md 文件（写作方法论 / 笔记 / 参考书）做 FAISS 索引，写章节时按关键词 + 任务域召 top-5 段落作为 LLM 上下文。Triggers: 语料检索 / RAG / method search / 方法论参考."
category: general
---

# Novel RAG Search (通用 markdown RAG)

把 novel-writing-beginner 等任意 .md 语料做语义检索，给 novel-standard 提供"方法论参考"上下文。

## Workflow

1. **首次**：跑 `scripts/build_index.py` 把语料切块 + 嵌入 + 建索引
   - 嵌入模型：sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
   - 索引：FAISS cosine
   - 切块：每段 200–500 字
2. **每次写章节**：主 Agent 调 `scripts/retrieve.py`
   - 输入：当前任务关键词（如"开篇切入点""人物对白""爽点排布"）
   - 输出：top-5 段落 + 任务域标签 + 来源文件
3. LLM 写正文时把这 5 段塞进 `参考方法论` 上下文

## 与 Denova 原生 `query_lore_items` 的区别

| 维度 | query_lore_items | novel-rag-search |
|---|---|---|
| 检索对象 | 平台 lore 库 | 任意 .md 语料 |
| 范围 | 限项目 lore | 跨项目/方法论文档 |
| 适用 | 当前小说设定 | 写作方法/通用参考 |

## 语料默认

- `E:\002-Pr\cangjie-skill-main\books\novel-writing-beginner\`（261 篇原始方法论）
- 也可指向任意 .md 目录

## 工具依赖

- Python 3.10+（用 novel-stack/.venv）
- sentence-transformers
- faiss-cpu
- jieba（中文）

## 边界

- 不抓版权小说作语料
- 用户已合法持有的本地 .md 目录可用
- RAG 检索召回 top-5，重排序后进 prompt
