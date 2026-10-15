# Voice-Shared Spec (人物声音卡规范)

> 来源：vexjoy-agent-main/skills/voice-shared/docs/VOICE-SYSTEM.md
> 用途：character-voice skill 的指标参考

## 7 个核心指标

| 指标 | 测什么 | 健康范围（参考） |
|---|---|---|
| 句长分布 | 短/中/长/超长句比例 | 短 ≤ 15% / 中 60-70% / 长 15-25% / 超长 ≤ 5% |
| 开头模式 | 段落开头：事实/疑问/故事/连词 | 看角色性格定 |
| 逗号密度 | 标点指纹 | 0.10–0.20（每 100 字符的逗号数） |
| 缩写率 | 形式化程度 | 看角色（如老人不缩写、年轻人高缩写） |
| 破句率 | 故意短句占比 | 看角色（冷静角色低、激情角色高） |
| em-dash 用法 | 标点偏好 | 看角色（叙述者常用、对话者少用） |
| 功能词签名 | 词频指纹（the/and/but/我/你） | 稳定 = 角色声音稳定 |

## Wabi-Sabi 原则

自然不完美（run-on / fragment / 随意标点）是**特征不是 bug**。无菌的语法正确是 AI tell。本系统故意保留这些特征。

## 声音卡数据结构

```json
{
  "character": "角色名",
  "samples": ["对白 1", "对白 2", "对白 3"],
  "metrics": {
    "avg_sentence_length": 18.2,
    "short_ratio": 0.10,
    "medium_ratio": 0.65,
    "long_ratio": 0.20,
    "very_long_ratio": 0.05,
    "opening_patterns": {"fact": 0.4, "question": 0.2, "story": 0.1, "conjunction": 0.3},
    "comma_density": 0.15,
    "contraction_rate": 0.30,
    "fragment_rate": 0.05,
    "em_dash_rate": 0.02,
    "function_words": {"我": 0.12, "你": 0.05, "他": 0.08, "但是": 0.02}
  },
  "stages": {
    "ch1-10": "声音版本 1（早期）",
    "ch11-20": "声音版本 2（中期）"
  },
  "banned_patterns": ["不要写', 不...'句式", "不要用'它不是 X, 它是 Y'"]
}
```

## 评分算法

```
score = 100 * (1 - mean(各指标 deviation))
阈值：≥ 60 通过 / < 60 警告
```

偏差：abs(current - target) / abs(target)，按 7 个指标平均。

## 工作流

1. **采样**：用户给 ≥ 3 段参考对白
2. **分析**：voice_analyzer.py 提 7 个指标
3. **存卡**：setting/voice-cards/<角色>.json
4. **校验**：写每章后 voice_validator.py 对比 → 警告
5. **校准**：根据实际写出来的对白逐步更新声音卡

## 重要限制

- **不要追求完美**：自然语言的"破句"是声音
- **不要追求 100 分**：稳定 ≠ 一致，60 分即合格
- **不要用 AI 自己的声音**："It's not X, it's Y" / "Moreover" / "Furthermore" 是 AI tell，禁
