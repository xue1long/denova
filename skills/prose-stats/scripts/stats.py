"""prose-stats: 语感/风格统计

调 prosegrinder 跑 9 种可读性分数 + 5 个 prose 指标，再补 2 个自建指标
（动作动词密度、章末钩子关键词）。

用法：
  python stats.py <chapter.md> [--voice-card voice-card.json]
  python stats.py <chapter.md> --out stats.json

输出：
  {
    "metrics": { ... 7 个核心指标 },
    "readability": { ... 9 种可读性分数 },
    "voice_match": { ... 与目标风格卡对比（可选） },
    "diagnosis": [ ... 健康度建议 ]
  }
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    from prosegrinder import Prose
except ImportError:
    print("prosegrinder 未装。pip install prosegrinder", file=sys.stderr)
    sys.exit(2)

try:
    import jieba
    import jieba.posseg as pseg
except ImportError:
    print("jieba 未装。pip install jieba", file=sys.stderr)
    sys.exit(2)


# 7 个核心指标
HEALTHY_RANGES = {
    "avg_sentence_length": (15, 25, "平均句长（字）"),
    "avg_paragraph_sentences": (2, 4, "段落平均句数"),
    "dialogue_ratio": (0.25, 0.40, "对话占比"),
    "action_verb_density": (8, None, "动作动词密度（每 1000 字）"),
    "adjective_density": (None, 15, "形容词密度（每 1000 字）"),
    "ch_end_hook_keywords": (1, None, "章末钩子关键词数"),
    "pov_consistency": (0.80, None, "POV 一致性"),
}

# 章末钩子关键词
HOOK_KEYWORDS = ["？", "!", "但", "不料", "突然", "然而", "谁知", "却", "未想", "岂料"]


def split_sentences_zh(text: str) -> list:
    """中文分句：按 。！？；… 切"""
    return [s.strip() for s in re.split(r"[。！？；…\n]+", text) if s.strip()]


def split_paragraphs(text: str) -> list:
    """按段落切分。

    修于 2026-10-15（第二次）：网文常见两种格式——
      1) 双换行分段（散文式）：含多个 \\n\\n
      2) 单换行分段（每行一段，含 \\u3000\\u3000 中文缩进）：\\n\\n 极少
    启发式：\\n\\n 数 >= 3 且占总行数 < 50% → 按 \\n\\n 切；否则按 \\n 切。
    """
    n_double = text.count("\n\n")
    n_single = text.count("\n")
    if n_double >= 3 and n_double <= (n_single // 2 + 1):
        return [p.strip() for p in text.split("\n\n") if p.strip()]
    return [p.strip() for p in text.split("\n") if p.strip()]


def count_dialogue(text: str) -> int:
    """对话字符数：识别对话段（段开头是引号）累加字符数。

    修于 2026-10-15：原版用 `r'[""「」]'` 只能匹配 4 个全角符号，但本机 Python
    字符串里 "" 实际是半角 unicode，许多中文网文用全角双引号""会被漏。
    改为：识别对话段（段首是引号字符），累加段长。

    匹配模式：
      - 段首是半角双引号 " 或全角双引号 "" (U+201C/U+201D)
      - 段首是日式中括号 「」(U+300C/U+300D)
      - 段首是英文双引号 " 但前面有 "（连续对话）
    """
    quote_chars = {'"', "\u201c", "\u201d", "\u300c", "\u300d"}
    paras = split_paragraphs(text)
    total = 0
    for p in paras:
        stripped = p.lstrip()
        if stripped and stripped[0] in quote_chars:
            total += len(p)
    return total


def action_verb_density(text: str, total_chars: int) -> float:
    """动作动词密度：每 1000 字的动词数（粗略）"""
    if total_chars < 100:
        return 0.0
    words = pseg.cut(text)
    verbs = sum(1 for w, pos in words if pos.startswith("v"))
    return round(verbs * 1000 / total_chars, 2)


def adjective_density(text: str, total_chars: int) -> float:
    if total_chars < 100:
        return 0.0
    words = pseg.cut(text)
    adjs = sum(1 for w, pos in words if pos.startswith("a"))
    return round(adjs * 1000 / total_chars, 2)


def ch_end_hook_keywords(text: str) -> int:
    last_200 = text[-200:] if len(text) > 200 else text
    return sum(last_200.count(k) for k in HOOK_KEYWORDS)


def pov_consistency(text: str) -> float:
    """POV 一致性：第一人称 vs 第三人称 vs 第二人称占比。

    修于 2026-10-15：原版用单字代词（我/你/他/她/它）出现次数作为权重，
    但单字代词高频出现在"我们/我的/你的/他是"等非主视角标记中，导致分母过大、
    三个视角比例被稀释到恒定 0.50。改为：用"代词词族"分组，第一人称组 vs
    第三人称组对比（第二人称多用于对话，独立计算）。
    """
    first_person = ["我", "我们", "咱", "咱们", "我的", "我们的"]
    second_person = ["你", "你们", "你的", "你们的"]
    third_person = ["他", "她", "它", "他们", "她们", "它们", "他的", "她的"]

    n_first = sum(text.count(p) for p in first_person)
    n_second = sum(text.count(p) for p in second_person)
    n_third = sum(text.count(p) for p in third_person)
    n_total = n_first + n_second + n_third

    if n_total == 0:
        return 1.0  # 无代词 = 不可判定，默认通过
    # 取最大视角占比
    n_main = max(n_first, n_second, n_third)
    return round(n_main / n_total, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", help="章节 .md 路径")
    ap.add_argument("--out", help="输出 JSON 路径")
    ap.add_argument("--voice-card", help="可选：目标风格卡 .json")
    args = ap.parse_args()

    text = Path(args.chapter).read_text(encoding="utf-8")
    # 去除 markdown 标题/列表前缀，保留正文
    text_clean = re.sub(r"^#+\s.*$", "", text, flags=re.MULTILINE)
    text_clean = re.sub(r"^[-*]\s", "", text_clean, flags=re.MULTILINE)

    sentences = split_sentences_zh(text_clean)
    paragraphs = split_paragraphs(text_clean)
    total_chars = len(text_clean)
    dialogue_chars = count_dialogue(text_clean)

    # 5 个自算指标
    metrics = {
        "avg_sentence_length": round(total_chars / max(len(sentences), 1), 1),
        "avg_paragraph_sentences": round(len(sentences) / max(len(paragraphs), 1), 1),
        "dialogue_ratio": round(dialogue_chars / max(total_chars, 1), 3),
        "action_verb_density": action_verb_density(text_clean, total_chars),
        "adjective_density": adjective_density(text_clean, total_chars),
        "ch_end_hook_keywords": ch_end_hook_keywords(text_clean),
        "pov_consistency": pov_consistency(text_clean),
    }

    # 9 个 prosegrinder 可读性分数
    try:
        p = Prose(text_clean)
        readability = {
            "automated_readability_index": getattr(p, "ari", None),
            "coleman_liau_index": getattr(p, "coleman_liau", None),
            "flesch_kincaid_grade_level": getattr(p, "flesch_kincaid_grade", None),
            "flesch_reading_ease": getattr(p, "flesch_reading_ease", None),
            "gunning_fog_index": getattr(p, "gunning_fog", None),
            "linsear_write": getattr(p, "linsear_write", None),
            "lix": getattr(p, "lix", None),
            "rix": getattr(p, "rix", None),
            "smog": getattr(p, "smog", None),
        }
    except Exception as e:
        readability = {"error": str(e)}

    # 健康度诊断
    diagnosis = []
    for key, (lo, hi, label) in HEALTHY_RANGES.items():
        val = metrics.get(key, 0)
        ok = True
        if lo is not None and val < lo:
            ok = False
            diagnosis.append(f"✗ {label}={val} 低于阈值 {lo}")
        if hi is not None and val > hi:
            ok = False
            diagnosis.append(f"✗ {label}={val} 高于阈值 {hi}")
        if ok:
            diagnosis.append(f"✓ {label}={val} 达标")

    out = {
        "chapter": str(args.chapter),
        "word_count": total_chars,
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "metrics": metrics,
        "readability": readability,
        "diagnosis": diagnosis,
    }

    # 与目标风格卡对比
    if args.voice_card:
        card = json.loads(Path(args.voice_card).read_text(encoding="utf-8"))
        card_metrics = card.get("metrics", {})
        voice_match = {}
        for k, v in metrics.items():
            cv = card_metrics.get(k)
            if cv is None:
                voice_match[k] = {"current": v, "target": None, "deviation": None}
                continue
            dev = abs(v - cv) / max(abs(cv), 1e-6)
            voice_match[k] = {
                "current": v,
                "target": cv,
                "deviation": round(dev, 3),
            }
        out["voice_match"] = voice_match
        out["voice_match_score"] = round(100 * (1 - sum(v.get("deviation", 0) or 0 for v in voice_match.values()) / 7), 1)

    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
