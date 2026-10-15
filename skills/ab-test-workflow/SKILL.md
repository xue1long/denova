---
name: ab-test-workflow
description: "同一份细纲做 A/B 对照：你手写一章 + novel-standard 生成一章，5 维度对照（钩子 / 语感 / 节奏 / 合规 / 五层评审），形成人感与算法双轨训练数据。Triggers: A/B test / 对照 / 盲写对比 / AI vs 人工."
category: general
---

# A/B Test Workflow (盲写 vs AI 生成对照)

让你的盲写稿和 AI 生成稿在**同一份细纲**下做客观对比，沉淀训练数据。

## Workflow

### Step 1: 用户先手写
- 用我们已有的 `提速版-细纲.md ch1` 等细纲
- 写 800–1500 字盲写稿
- 落 `examples/ch1-ab-test/handwritten/<你写的>.md`

### Step 2: 主 Agent 调 novel-standard 生成
- 用同一份细纲
- 落 `examples/ch1-ab-test/generated/<AI 写的>.md`

### Step 3: 跑 5 维度对照

| 维度 | 工具 |
|---|---|
| 钩子强度 | writing-five-layer-review C2.3 |
| 语感/风格 | prose-stats |
| 节奏/章节推进 | 五层量表 C3.3 |
| 合规 | 五层量表 C0.1–C0.3 |
| 人物声音 | character-voice |
| L1–L5 综合 | writing-five-layer-review |

### Step 4: 输出 `examples/ch1-ab-test/compare.md`

格式：
```
| 维度 | 盲写稿 | AI 生成稿 | 优劣 |
|---|---|---|---|
| 钩子强度 | 中 | 强 | AI 优 |
| 平均句长 | 22 | 18 | 盲写优（更紧凑） |
| 对话占比 | 0.25 | 0.35 | AI 优 |
| ... |
```

### Step 5: 用户写主观判断（可选）
- 在 compare.md 末尾加 `## 我的判断` 段
- 写"这一轮我学到了什么"
- 形成长期训练数据

## 价值

- 校准 writing-five-layer-review 的"评审闸"：发现 LLM 评分与主观判断的偏差
- 校准 prose-stats 的"健康范围"：发现实际好稿与理论范围的差距
- 训练你的"挑刺能力"：通过对照发现盲写时的弱项

## 工作量

- 写 1 章盲写：1–2 小时
- 写 1 章 AI 生成：5–10 分钟
- 跑对照：5 分钟
- **周期**：建议每 5 章做 1 次 A/B
