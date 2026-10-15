"""character-voice: voice_validator.py
对当前章节某角色对白 vs 声音卡，给出 0-100 一致性分。
"""
import argparse
import json
import sys
from pathlib import Path

# 复用 voice_analyzer 的函数
sys.path.insert(0, str(Path(__file__).parent))
from voice_analyzer import (
    split_sentences_zh, split_paragraphs,
    avg_sentence_length, sentence_length_distribution,
    opening_patterns, comma_density, contraction_rate,
    fragment_rate, em_dash_rate, function_words_signature,
)

METRIC_KEYS_NUMERIC = [
    "avg_sentence_length", "short_ratio", "medium_ratio", "long_ratio",
    "very_long_ratio", "comma_density", "contraction_rate", "fragment_rate",
    "em_dash_rate",
]


def extract_role_dialogue(chapter: str, role: str) -> str:
    """从章节正文中提取某角色的对白（简化版：按 '角色名：' 或 '角色名说' 匹配）"""
    paras = split_paragraphs(chapter)
    role_lines = []
    for p in paras:
        if role in p[:10]:  # 段落开头有角色名
            role_lines.append(p)
    return "\n".join(role_lines) if role_lines else chapter


def compute_metrics(text: str) -> dict:
    return {
        "avg_sentence_length": avg_sentence_length(text),
        **sentence_length_distribution(text),
        **opening_patterns(text),
        "comma_density": comma_density(text),
        "contraction_rate": contraction_rate(text),
        "fragment_rate": fragment_rate(text),
        "em_dash_rate": em_dash_rate(text),
        "function_words": function_words_signature(text),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", help="章节 .md 路径")
    ap.add_argument("--voice-card", required=True, help="声音卡 .json")
    ap.add_argument("--role", required=True, help="角色名")
    ap.add_argument("--out", help="可选：输出 JSON 报告")
    ap.add_argument("--threshold", type=int, default=60, help="通过阈值（默认 60）")
    args = ap.parse_args()

    chapter_text = Path(args.chapter).read_text(encoding="utf-8")
    card = json.loads(Path(args.voice_card).read_text(encoding="utf-8"))
    card_metrics = card.get("metrics", {})

    role_text = extract_role_dialogue(chapter_text, args.role)
    role_matched = bool(role_text.strip() and role_text != chapter_text)
    if not role_matched:
        # 修于 2026-10-15：fallback 用整章作对白时，降权 0.7 并标 false
        # 避免"分数高但无意义"的假阳性
        print(f"警告：本章未找到角色 '{args.role}' 的对白（按段落开头匹配），fallback 用整章，分数将降权 0.7", file=sys.stderr)

    current = compute_metrics(role_text)
    deviations = []
    metric_results = {}
    for k in METRIC_KEYS_NUMERIC:
        cur = current.get(k, 0)
        tgt = card_metrics.get(k)
        if tgt is None or tgt == 0:
            metric_results[k] = {"current": cur, "target": None, "deviation": None, "status": "skip"}
            continue
        dev = abs(cur - tgt) / max(abs(tgt), 1e-6)
        deviations.append(dev)
        if dev < 0.2:
            status = "✓"
        elif dev < 0.5:
            status = "△"
        else:
            status = "✗"
        metric_results[k] = {"current": cur, "target": tgt, "deviation": round(dev, 3), "status": status}

    # 功能词签名对比（粗略：Jaccard）
    card_fw = set(card_metrics.get("function_words", {}).keys())
    cur_fw = set(current.get("function_words", {}).keys())
    if card_fw or cur_fw:
        intersect = card_fw & cur_fw
        union = card_fw | cur_fw
        fw_jaccard = len(intersect) / len(union) if union else 0
        fw_dev = 1 - fw_jaccard
        deviations.append(fw_dev)
        fw_status = "✓" if fw_jaccard > 0.7 else "△" if fw_jaccard > 0.4 else "✗"
        metric_results["function_words"] = {
            "current": list(cur_fw),
            "target": list(card_fw),
            "jaccard": round(fw_jaccard, 3),
            "deviation": round(fw_dev, 3),
            "status": fw_status,
        }

    score_raw = round(100 * (1 - sum(deviations) / max(len(deviations), 1)), 1)
    # 修于 2026-10-15：未匹配角色时降权 0.7
    if not role_matched:
        score = round(score_raw * 0.7, 1)
        role_matched_warning = f"角色 '{args.role}' 未在本章段落开头匹配，fallback 用整章文本，原始分 {score_raw} 降权到 {score}"
    else:
        score = score_raw
        role_matched_warning = None
    pass_ = score >= args.threshold

    report = {
        "chapter": str(args.chapter),
        "role": args.role,
        "voice_card": str(args.voice_card),
        "score": score,
        "score_raw": score_raw,
        "role_matched": role_matched,
        "passed": pass_,
        "threshold": args.threshold,
        "metrics": metric_results,
        "warnings": [
            f"✗ {k} 偏差 {v['deviation']}" for k, v in metric_results.items() if v.get("status") == "✗"
        ],
    }
    if role_matched_warning:
        report["warnings"].insert(0, role_matched_warning)

    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if not pass_:
        print(f"\n[FAIL] 声音一致性分 {score} < 阈值 {args.threshold}", file=sys.stderr)
        for w in report["warnings"]:
            print(f"  {w}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
