---
name: prose-stats
description: "对当前章节做语感/风格统计（句长分布 / 段落句数 / 对话占比 / POV / 动作动词密度 / 章末钩子关键词 / 9 种可读性分数），输出健康度诊断 + 与目标风格卡对比。Triggers: 语感统计 / 风格分析 / prose stats / 章节诊断."
category: writing
capabilities:
  - writing-workflow
agent: ide
---

# Prose Stats (语感/风格统计)

客观量化当前章节的"语感"，取代"语感好不好"的主观判断。

## Workflow

1. 主 Agent 读当前章节正文
2. 调用 `scripts/stats.py`：
   - 调 prosegrinder 跑 9 个可读性分数（ARI/CLI/FK/FRE/GFI/LIX/RIX/SMOG/LW）
   - 补 2 个自建指标：动作动词密度、章末钩子关键词
3. 输出 JSON + Markdown 健康度报告：
   - 7 个指标 + 9 个可读性分数
   - 与"目标风格卡"对比（如有），偏差 > 阈值给警告
4. 报告同步写入 `setting/style-baseline.md` 累积

## 7 个核心指标

| 指标 | 公式 | 健康范围 |
|---|---|---|
| 平均句长 | 字符数 / 句数 | 15–25 字（快节奏） |
| 段落平均句数 | 句数 / 段数 | 2–4 句 |
| 对话占比 | 对话字符 / 总字符 | 25–40% |
| 动作动词密度 | 动作动词数 / 1000 字 | ≥ 8 |
| 形容词密度 | 形容词数 / 1000 字 | ≤ 15 |
| 章末钩子关键词 | 末 200 字含 ['？', '但', '不料', '突然'] 数 | ≥ 1 |
| POV 一致性 | 主视角代词占比 | ≥ 80% |

## 9 种可读性分数（prosegrinder）

ARI / Coleman-Liau / Flesch-Kincaid / Flesch Reading Ease / Gunning Fog / Linsear Write / LIX / RIX / SMOG

## 工具依赖

- Python 3.10+
- prosegrinder（已装到 `novel-stack/.venv`）
- jieba（中文分词）

## 边界

- 不评估内容质量（交给 novel-standard / writing-five-layer-review）
- 不评估人物声音（交给 character-voice）
- 仅作"语感指纹"记录与对比
