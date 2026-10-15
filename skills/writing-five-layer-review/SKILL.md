---
name: writing-five-layer-review
description: "按商业化网文五层框架（L1题材/L2节奏/L3情绪/L4人物/L5数据 + 合规底座 C0）自动评审一章，输出 17 条 check 结果 + 证据引文 + 返工建议。L2 或 L3 任一层通过率 < 60% 判定不适合免费平台投稿，触发返工。Triggers: 五层评审 / layer review / 完读率自检 / 平台合规检查."
category: general
---

# Five-Layer Writing Review

按商业化网文五层框架评审当前章节。

## Workflow

1. 加载 17 条 check 条目：`references/five-layer-checklist.md`
2. 对当前章节正文逐条跑检查：
   - 12 条用关键词/正则（防 LLM 自吹）
   - 5 条用 LLM 评估（连续性/人物可共情/对话比合理性/文笔/细节）
3. 输出评审报告（JSON + Markdown 摘要）：
   - 每条 ✓/△/✗ + 首次出现位置（字符偏移）+ 证据引文
   - L2/L3 通过率
   - L2 或 L3 < 60% → 触发返工
4. 全过 → 输出 pass 状态

## 五层定义

| 层 | 致命? | 内容 |
|---|---|---|
| L1 题材匹配 | 否 | 选对战场、合规载体安全 |
| **L2 节奏引擎** | **致命** | 黄金三章、每章钩子、第一次打脸位置 |
| **L3 情绪爽感** | **致命** | 3 章小爽/10 章大爽、每 2000 字波动 |
| L4 人物手艺 | 否 | 模板 A/B/C/D 应用 |
| L5 数据闭环 | 否 | 完读率预估 |
| C0 合规 | 否 | 无荐股/不美化犯罪/主角三观 |

## 输出 schema

```json
{
  "chapter": "ch1.md",
  "items": [{"id": "C2.1", "result": "✓/△/✗", "evidence": "前 312 字出现'开除'一次", "confidence": "high"}],
  "summary": {"L1": "1/1", "L2": "4/4", "L3": "1/1", "L4": "2/2", "L5": "0/0", "C0": "3/3"},
  "must_revise": [],
  "warnings": []
}
```

## 关键边界

- 不替用户做对外决策（书名/简介/签约）
- 不重写正文（仅评审 + 返工建议）
- 与 novel-standard 评审互补：novel-standard 评"文学质量"，本 skill 评"平台算法友好度"

## 引用

- 17 条 checklist：`references/five-layer-checklist.md`
