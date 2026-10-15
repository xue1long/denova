"""character-voice: voice_analyzer.py
按 voice-shared 规范从角色对白样本中提取 7 个指标，生成声音卡。
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import jieba
except ImportError:
    print("jieba 未装。pip install jieba", file=sys.stderr)
    sys.exit(2)


def split_sentences_zh(text: str) -> list:
    return [s.strip() for s in re.split(r"[。！？；…\n]+", text) if s.strip()]


def split_paragraphs(text: str) -> list:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def avg_sentence_length(text: str) -> float:
    sents = split_sentences_zh(text)
    if not sents:
        return 0.0
    return round(sum(len(s) for s in sents) / len(sents), 2)


def sentence_length_distribution(text: str) -> dict:
    sents = split_sentences_zh(text)
    if not sents:
        return {"short": 0, "medium": 0, "long": 0, "very_long": 0}
    short = sum(1 for s in sents if len(s) <= 10)
    medium = sum(1 for s in sents if 10 < len(s) <= 25)
    long = sum(1 for s in sents if 25 < len(s) <= 50)
    very_long = sum(1 for s in sents if len(s) > 50)
    total = len(sents)
    return {
        "short_ratio": round(short / total, 3),
        "medium_ratio": round(medium / total, 3),
        "long_ratio": round(long / total, 3),
        "very_long_ratio": round(very_long / total, 3),
    }


def opening_patterns(text: str) -> dict:
    """段落开头：事实/疑问/故事/连词"""
    paras = split_paragraphs(text)
    if not paras:
        return {"fact": 0, "question": 0, "story": 0, "conjunction": 0}
    fact = sum(1 for p in paras if re.match(r"^[\u4e00-\u9fa5]", p) and not re.match(r"^[但是然而虽然]", p))
    question = sum(1 for p in paras if "？" in p[:5] or "?" in p[:5])
    conjunction = len(paras) - fact - question
    total = len(paras)
    return {
        "fact_ratio": round(fact / total, 3),
        "question_ratio": round(question / total, 3),
        "conjunction_ratio": round(conjunction / total, 3),
    }


def comma_density(text: str) -> float:
    if len(text) < 10:
        return 0.0
    return round(text.count("，") / len(text), 3)


def contraction_rate(text: str) -> float:
    """中文：'的'/'了'/'着' 出现率"""
    if len(text) < 10:
        return 0.0
    return round((text.count("的") + text.count("了") + text.count("着")) / len(text), 3)


def fragment_rate(text: str) -> float:
    """破句率：极短句（≤ 5 字）占比"""
    sents = split_sentences_zh(text)
    if not sents:
        return 0.0
    return round(sum(1 for s in sents if len(s) <= 5) / len(sents), 3)


def em_dash_rate(text: str) -> float:
    if len(text) < 10:
        return 0.0
    return round((text.count("——") + text.count("—")) / len(text), 3)


def function_words_signature(text: str) -> dict:
    """功能词签名：词频指纹"""
    words = list(jieba.cut(text))
    total = len(words)
    if total == 0:
        return {}
    fw = ["我", "你", "他", "她", "它", "但是", "因为", "所以", "然后"]
    sig = {}
    for w in fw:
        c = words.count(w) / total
        if c > 0.001:
            sig[w] = round(c, 4)
    return sig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("samples", help="角色对白样本 .txt（每行一段）")
    ap.add_argument("--character", required=True, help="角色名")
    ap.add_argument("--out", required=True, help="输出声音卡 .json")
    args = ap.parse_args()

    samples_raw = Path(args.samples).read_text(encoding="utf-8")
    samples = [s.strip() for s in samples_raw.split("\n") if s.strip()]
    if len(samples) < 3:
        print(f"警告：样本数 {len(samples)} 少于 3，建议补足", file=sys.stderr)
    text = "\n".join(samples)

    card = {
        "character": args.character,
        "samples_count": len(samples),
        "samples": samples,
        "metrics": {
            "avg_sentence_length": avg_sentence_length(text),
            **sentence_length_distribution(text),
            **opening_patterns(text),
            "comma_density": comma_density(text),
            "contraction_rate": contraction_rate(text),
            "fragment_rate": fragment_rate(text),
            "em_dash_rate": em_dash_rate(text),
            "function_words": function_words_signature(text),
        },
        "stages": {"default": "默认声音版本"},
        "banned_patterns": [
            "不要用 '它不是 X, 它是 Y' 句式（AI tell）",
            "不要用 'Moreover' / 'Furthermore' 等 AI 标志词",
        ],
    }

    Path(args.out).write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"声音卡已生成：{args.out}")
    print(f"  角色：{args.character}")
    print(f"  样本数：{len(samples)}")
    print(f"  平均句长：{card['metrics']['avg_sentence_length']}")
    print(f"  短/中/长/超长：{card['metrics']['short_ratio']}/{card['metrics']['medium_ratio']}/{card['metrics']['long_ratio']}/{card['metrics']['very_long_ratio']}")


if __name__ == "__main__":
    main()
