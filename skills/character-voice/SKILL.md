---
name: character-voice
description: "维护每个角色的声音卡（句长分布 / 口头禅 / 破句率 / em-dash / 功能词签名），写章节时校验角色对白是否一致；前后章偏差 > 阈值触发警告。Triggers: 人物声音 / voice consistency / 角色对白 / voice card."
category: writing
capabilities:
  - writing-workflow
agent: ide
---

# Character Voice (人物声音一致性)

多章连载后主角/配角对白风格漂移是通病。本 skill 用 voice-shared 规范维护每个角色的"声音卡"，写章节时自动校验。

## Workflow

1. 首次使用：主 Agent 让用户为每个核心角色提供 ≥ 3 段参考对白（同一作者/同一年份）
2. 调 `scripts/voice_analyzer.py`：
   - 提取 7 个指标：句长分布、开头模式、逗号密度、缩写率、破句率、em-dash 用法、功能词签名
3. 输出 `setting/voice-cards/<角色>.json` 声音卡
4. 写每章后：调 `scripts/voice_validator.py` 对该角色当章对白 vs 声音卡
5. 偏差 > 阈值（默认 60/100）→ 警告

## 7 个核心指标（voice-shared 规范）

| 指标 | 测什么 |
|---|---|
| 句长分布 | 短/中/长/超长句比例 |
| 开头模式 | 段落开头：事实/疑问/故事/连词 |
| 逗号密度 | 标点指纹 |
| 缩写率 | 形式化程度（don't vs do not） |
| 破句率 | 故意短句占比 |
| em-dash 用法 | 标点偏好 |
| 功能词签名 | 词频指纹（the/and/but/我/你） |

## 输出 schema

```json
{
  "character": "许平秋",
  "metrics": {
    "avg_sentence_length": 18.2,
    "comma_density": 0.15,
    "em_dash_rate": 0.02,
    "function_words": {"我": 0.12, "你": 0.05}
  },
  "score": 75,
  "warnings": []
}
```

## 阶段版本

角色"成长变化"会触发假阳性——声音卡支持 `stages`：ch1–10 阶段A、ch11–20 阶段B。

## 工具依赖

- Python 3.10+
- jieba（中文分词）
- scripts/voice_analyzer.py / voice_validator.py

## 引用

- voice-shared 规范全文：`references/voice-shared-spec.md`
