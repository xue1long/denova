#!/usr/bin/env python3
"""Check novel-analysis output structure and evidence links using only stdlib."""

import argparse
import json
import sys
from pathlib import Path


REQUIRED_TOP = {
    "schema_version", "work", "run", "coverage", "evidence", "stages",
    "claims", "technique_cards", "sops", "correction_log", "quality_review",
}
STAGE_NAMES = {"skeleton", "flesh", "soul", "technique", "practice"}
VALID_STAGE_STATUS = {"not_started", "partial", "complete", "blocked"}
VALID_GATES = {"not_checked", "pass", "revise", "blocked"}


def unique_values(values, label, errors):
    if len(values) != len(set(values)):
        errors.append(f"{label} contains duplicate IDs.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=Path, help="Analysis output JSON file")
    args = parser.parse_args()

    try:
        data = json.loads(args.json_file.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        print(f"ERROR: cannot read {args.json_file}: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2

    errors = []
    warnings = []
    if not isinstance(data, dict):
        print("ERROR: top-level JSON value must be an object.")
        return 2

    missing = sorted(REQUIRED_TOP - set(data))
    if missing:
        errors.append("Missing top-level fields: " + ", ".join(missing))

    coverage = data.get("coverage", {})
    evidence = data.get("evidence", [])
    stages = data.get("stages", {})
    claims = data.get("claims", [])
    cards = data.get("technique_cards", [])
    sops = data.get("sops", [])

    if not isinstance(coverage, dict):
        coverage = {}
        errors.append("coverage must be an object.")
    if not isinstance(evidence, list):
        evidence = []
        errors.append("evidence must be an array.")
    if not isinstance(stages, dict):
        stages = {}
        errors.append("stages must be an object.")
    if not isinstance(claims, list):
        claims = []
        errors.append("claims must be an array.")
    if not isinstance(cards, list):
        cards = []
        errors.append("technique_cards must be an array.")
    if not isinstance(sops, list):
        sops = []
        errors.append("sops must be an array.")

    for name in sorted(STAGE_NAMES):
        stage = stages.get(name)
        if not isinstance(stage, dict):
            errors.append(f"stages.{name} must be an object.")
            continue
        if stage.get("status") not in VALID_STAGE_STATUS:
            errors.append(f"stages.{name}.status is missing or invalid.")
        if stage.get("gate") not in VALID_GATES:
            errors.append(f"stages.{name}.gate is missing or invalid.")
        if not isinstance(stage.get("summary"), str):
            errors.append(f"stages.{name}.summary must be a string.")
        if not isinstance(stage.get("missing_inputs"), list):
            errors.append(f"stages.{name}.missing_inputs must be an array.")

    expected = coverage.get("expected_chapter_ids", [])
    received = coverage.get("received_chapter_ids", [])
    processed = coverage.get("processed_chapter_ids", [])
    pending = coverage.get("pending_chapter_ids", [])
    for label, values in (("expected_chapter_ids", expected),
                          ("received_chapter_ids", received),
                          ("processed_chapter_ids", processed),
                          ("pending_chapter_ids", pending)):
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            errors.append(f"coverage.{label} must be an array of strings.")
        else:
            unique_values(values, f"coverage.{label}", errors)
    if all(isinstance(value, list) for value in (expected, received, processed, pending)):
        if not set(processed).issubset(set(received)):
            errors.append("processed_chapter_ids must be a subset of received_chapter_ids.")
        if expected:
            if not set(received).issubset(set(expected)):
                errors.append("received_chapter_ids contains a chapter outside expected_chapter_ids.")
            calculated_pending = set(expected) - set(processed)
            if set(pending) != calculated_pending:
                errors.append("pending_chapter_ids must equal expected_chapter_ids minus processed_chapter_ids.")
            calculated_percent = 100 * len(set(processed)) / len(set(expected))
            actual_percent = coverage.get("coverage_percent")
            if not isinstance(actual_percent, (int, float)) or abs(actual_percent - calculated_percent) > 0.1:
                errors.append(f"coverage_percent should be {calculated_percent:.1f} for the declared chapter sets.")
            if coverage.get("completeness") == "complete" and (calculated_pending or not set(expected).issubset(set(received))):
                errors.append("completeness cannot be complete while an expected chapter is absent or unprocessed.")
            if calculated_pending and coverage.get("completeness") == "complete":
                errors.append("completeness is complete but pending chapters remain.")
        elif coverage.get("coverage_percent") is not None or coverage.get("completeness") != "unknown":
            errors.append("Without an expected chapter manifest, coverage_percent must be null and completeness must be unknown.")

    evidence_ids = []
    for item in evidence:
        if not isinstance(item, dict):
            errors.append("Each evidence item must be an object.")
            continue
        for field in ("evidence_id", "chapter_id", "chunk_id", "locator", "paraphrase"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"Evidence item is missing a non-empty {field}.")
        if isinstance(item.get("evidence_id"), str):
            evidence_ids.append(item["evidence_id"])
    unique_values(evidence_ids, "evidence.evidence_id", errors)
    evidence_set = set(evidence_ids)

    def check_refs(refs, label):
        if not isinstance(refs, list) or not refs:
            errors.append(f"{label} must cite at least one evidence ID.")
            return
        for ref in refs:
            if ref not in evidence_set:
                errors.append(f"{label} refers to missing evidence ID {ref!r}.")

    claim_ids = []
    for claim in claims:
        if not isinstance(claim, dict):
            errors.append("Each claim must be an object.")
            continue
        if isinstance(claim.get("claim_id"), str):
            claim_ids.append(claim["claim_id"])
        check_refs(claim.get("evidence_refs"), f"claim {claim.get('claim_id', '?')}")
    unique_values(claim_ids, "claims.claim_id", errors)

    card_ids = []
    for card in cards:
        if not isinstance(card, dict):
            errors.append("Each technique card must be an object.")
            continue
        if isinstance(card.get("card_id"), str):
            card_ids.append(card["card_id"])
        check_refs(card.get("evidence_refs"), f"technique card {card.get('card_id', '?')}")
    unique_values(card_ids, "technique_cards.card_id", errors)
    card_set = set(card_ids)

    sop_ids = []
    for sop in sops:
        if not isinstance(sop, dict):
            errors.append("Each SOP must be an object.")
            continue
        if isinstance(sop.get("sop_id"), str):
            sop_ids.append(sop["sop_id"])
        if sop.get("technique_card_id") not in card_set:
            errors.append(f"SOP {sop.get('sop_id', '?')} refers to a missing technique card.")
    unique_values(sop_ids, "sops.sop_id", errors)
    sop_set = set(sop_ids)

    technique_stage = stages.get("technique", {})
    if isinstance(technique_stage, dict):
        listed = technique_stage.get("technique_card_ids", [])
        if not isinstance(listed, list) or not set(listed).issubset(card_set):
            errors.append("stages.technique.technique_card_ids must refer to existing technique cards.")
    for card in cards:
        if isinstance(card, dict) and card.get("sop_id") is not None and card.get("sop_id") not in sop_set:
            errors.append(f"Technique card {card.get('card_id', '?')} refers to a missing SOP.")

    practice = stages.get("practice", {})
    if isinstance(practice, dict):
        assignment = practice.get("assignment")
        if isinstance(assignment, dict) and assignment.get("technique_card_id") not in card_set:
            errors.append("Practice assignment refers to a missing technique card.")
        if practice.get("draft_status") == "evaluated" and practice.get("draft_evaluation") is None:
            errors.append("Practice draft is marked evaluated but draft_evaluation is null.")

    mode = data.get("run", {}).get("mode") if isinstance(data.get("run"), dict) else None
    required_cards = {"quick": 1, "standard": 3, "deep": 3}.get(mode)
    if required_cards is not None and len(cards) < required_cards:
        warnings.append(f"{mode} mode normally targets at least {required_cards} technique card(s); confirm the technique gate explains any shortfall.")

    for warning in warnings:
        print("WARNING:", warning)
    for error in errors:
        print("ERROR:", error)

    if errors:
        print(f"Structural check failed with {len(errors)} error(s).")
        return 1
    print(f"Structural check passed: {len(evidence_ids)} evidence item(s), {len(claim_ids)} claim(s), {len(card_ids)} technique card(s).")
    print("This check does not validate literary interpretation against source text.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
