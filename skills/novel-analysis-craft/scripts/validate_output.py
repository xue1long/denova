#!/usr/bin/env python3
"""Check novel-analysis output structure, coverage, and evidence links."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


REQUIRED_TOP = {
    "schema_version", "work", "run", "coverage", "evidence", "stages",
    "claims", "technique_cards", "sops", "correction_log", "quality_review",
    "source_chunks",
}
STAGE_NAMES = {"skeleton", "flesh", "soul", "technique", "practice"}
VALID_STAGE_STATUS = {"not_started", "partial", "complete", "blocked"}
VALID_GATES = {"not_checked", "pass", "revise", "blocked"}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def unique_values(values, label, errors):
    if len(values) != len(set(values)):
        errors.append(f"{label} contains duplicate IDs.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=Path, help="Analysis output JSON file")
    parser.add_argument("--input", type=Path, help="New input JSON to check against this checkpoint before resuming")
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
    if data.get("schema_version") != "1.1":
        errors.append("schema_version must be 1.1; re-ingest source chunks for older checkpoints.")

    work = data.get("work")
    if not isinstance(work, dict) or not isinstance(work.get("title"), str) or not work["title"].strip():
        errors.append("work.title must be a non-empty string.")
    run = data.get("run")
    if not isinstance(run, dict):
        errors.append("run must be an object.")
        run = {}
    for field in ("mode", "status", "updated_at", "next_action"):
        if not isinstance(run.get(field), str):
            errors.append(f"run.{field} must be a string.")

    coverage = data.get("coverage", {})
    evidence = data.get("evidence", [])
    source_chunks = data.get("source_chunks", [])
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
    if not isinstance(source_chunks, list):
        source_chunks = []
        errors.append("source_chunks must be an array.")
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

    chapter_of_chunk = {}
    for chunk in source_chunks:
        if not isinstance(chunk, dict):
            errors.append("Each source chunk must be an object.")
            continue
        chunk_id = chunk.get("chunk_id")
        chapter_id = chunk.get("chapter_id")
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            errors.append("Source chunk is missing a non-empty chunk_id.")
            continue
        if chunk_id in chapter_of_chunk:
            errors.append(f"source_chunks contains duplicate chunk ID {chunk_id!r}.")
        if not isinstance(chapter_id, str) or not chapter_id.strip():
            errors.append(f"Source chunk {chunk_id!r} is missing a non-empty chapter_id.")
        if not isinstance(chunk.get("sha256"), str) or not SHA256.fullmatch(chunk["sha256"]):
            errors.append(f"Source chunk {chunk_id!r} needs a lowercase SHA-256 content hash.")
        chapter_of_chunk[chunk_id] = chapter_id

    if args.input is not None:
        try:
            new_input = json.loads(args.input.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Cannot read new input JSON: {exc}")
        else:
            input_work = new_input.get("work", {}) if isinstance(new_input, dict) else {}
            if not isinstance(input_work, dict) or input_work.get("title") != (work if isinstance(work, dict) else {}).get("title"):
                errors.append("New input work.title differs from checkpoint work.title.")
            input_source = new_input.get("source", {}) if isinstance(new_input, dict) else {}
            input_chunks = input_source.get("chunks", []) if isinstance(input_source, dict) else []
            if not isinstance(input_chunks, list) or not input_chunks:
                errors.append("New input source.chunks must be a non-empty array.")
            else:
                old_chunks = {chunk["chunk_id"]: chunk for chunk in source_chunks
                              if isinstance(chunk, dict) and isinstance(chunk.get("chunk_id"), str)}
                seen_new = set()
                for chunk in input_chunks:
                    if not isinstance(chunk, dict) or not all(isinstance(chunk.get(key), str) for key in ("chunk_id", "chapter_id", "content")):
                        errors.append("Each new input chunk needs chunk_id, chapter_id, and content strings.")
                        continue
                    chunk_id = chunk["chunk_id"]
                    if chunk_id in seen_new:
                        errors.append(f"New input repeats chunk ID {chunk_id!r}.")
                    seen_new.add(chunk_id)
                    old = old_chunks.get(chunk_id)
                    digest = hashlib.sha256(chunk["content"].encode("utf-8")).hexdigest()
                    if old is not None and (old.get("chapter_id") != chunk["chapter_id"] or old.get("sha256") != digest):
                        errors.append(f"New input reuses chunk ID {chunk_id!r} with different chapter or content.")

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
    for field in ("expected_chapter_ids", "received_chapter_ids", "processed_chapter_ids",
                  "pending_chapter_ids", "coverage_percent", "completeness",
                  "last_processed_chapter_id", "scope_note"):
        if field not in coverage:
            errors.append(f"coverage.{field} is required.")
    for label, values in (("expected_chapter_ids", expected),
                          ("received_chapter_ids", received),
                          ("processed_chapter_ids", processed),
                          ("pending_chapter_ids", pending)):
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            errors.append(f"coverage.{label} must be an array of strings.")
        else:
            unique_values(values, f"coverage.{label}", errors)
    if isinstance(received, list) and all(isinstance(chapter, str) for chapter in received):
        if set(received) != {chapter for chapter in chapter_of_chunk.values() if isinstance(chapter, str)}:
            errors.append("received_chapter_ids must equal the chapters in source_chunks.")
    if all(isinstance(value, list) and all(isinstance(item, str) for item in value)
           for value in (expected, received, processed, pending)):
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
            if isinstance(actual_percent, bool) or not isinstance(actual_percent, (int, float)) or abs(actual_percent - calculated_percent) > 0.1:
                errors.append(f"coverage_percent should be {calculated_percent:.1f} for the declared chapter sets.")
            if calculated_pending and coverage.get("completeness") != "partial":
                errors.append("completeness must be partial while expected chapters remain pending.")
            if not calculated_pending and coverage.get("completeness") != "complete":
                errors.append("completeness must be complete when all expected chapters are processed.")
            if calculated_pending and run.get("status") == "complete":
                errors.append("run.status cannot be complete while expected chapters remain pending.")
        elif coverage.get("coverage_percent") is not None or coverage.get("completeness") != "unknown":
            errors.append("Without an expected chapter manifest, coverage_percent must be null and completeness must be unknown.")
    title_only = isinstance(work, dict) and work.get("scope") == "title_only"
    if not processed and not title_only:
        if run.get("status") == "complete":
            errors.append("run.status cannot be complete with no processed chapters.")
        for name, stage in stages.items():
            if isinstance(stage, dict) and (stage.get("status") == "complete" or stage.get("gate") == "pass"):
                errors.append(f"stages.{name} cannot be complete/pass with no processed chapters.")
    last_processed = coverage.get("last_processed_chapter_id")
    if last_processed is not None and last_processed not in processed:
        errors.append("last_processed_chapter_id must be null or in processed_chapter_ids.")

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
        chunk_id = item.get("chunk_id")
        if not isinstance(chunk_id, str) or chunk_id not in chapter_of_chunk:
            errors.append(f"Evidence {item.get('evidence_id', '?')} refers to a missing source chunk {chunk_id!r}.")
        elif item.get("chapter_id") != chapter_of_chunk[chunk_id]:
            errors.append(f"Evidence {item.get('evidence_id', '?')} chapter differs from its source chunk.")
    unique_values(evidence_ids, "evidence.evidence_id", errors)
    evidence_set = set(evidence_ids)

    def check_refs(refs, label):
        if not isinstance(refs, list):
            errors.append(f"{label}.evidence_refs must be an array.")
            return
        for ref in refs:
            if not isinstance(ref, str) or ref not in evidence_set:
                errors.append(f"{label} refers to missing evidence ID {ref!r}.")

    claim_ids = []
    for claim in claims:
        if not isinstance(claim, dict):
            errors.append("Each claim must be an object.")
            continue
        if isinstance(claim.get("claim_id"), str):
            claim_ids.append(claim["claim_id"])
        if claim.get("stage") not in STAGE_NAMES:
            errors.append(f"Claim {claim.get('claim_id', '?')} has an invalid stage.")
        check_refs(claim.get("evidence_refs"), f"claim {claim.get('claim_id', '?')}")
        if claim.get("evidence_refs") == [] and (claim.get("kind") == "observation" or claim.get("confidence") != "low"):
            errors.append(f"Claim {claim.get('claim_id', '?')} without source evidence must be a low-confidence inference or evaluation.")
    unique_values(claim_ids, "claims.claim_id", errors)

    card_ids = []
    for card in cards:
        if not isinstance(card, dict):
            errors.append("Each technique card must be an object.")
            continue
        if isinstance(card.get("card_id"), str):
            card_ids.append(card["card_id"])
        check_refs(card.get("evidence_refs"), f"technique card {card.get('card_id', '?')}")
        if card.get("evidence_refs") == [] and card.get("confidence") != "low":
            errors.append(f"Technique card {card.get('card_id', '?')} without source evidence must have low confidence.")
    unique_values(card_ids, "technique_cards.card_id", errors)
    card_set = set(card_ids)

    sop_ids = []
    for sop in sops:
        if not isinstance(sop, dict):
            errors.append("Each SOP must be an object.")
            continue
        if isinstance(sop.get("sop_id"), str):
            sop_ids.append(sop["sop_id"])
        if not isinstance(sop.get("failure_signals"), list) or not sop["failure_signals"]:
            errors.append(f"SOP {sop.get('sop_id', '?')} needs failure_signals.")
        if not isinstance(sop.get("technique_card_id"), str) or sop["technique_card_id"] not in card_set:
            errors.append(f"SOP {sop.get('sop_id', '?')} refers to a missing technique card.")
    unique_values(sop_ids, "sops.sop_id", errors)
    sop_set = set(sop_ids)

    technique_stage = stages.get("technique", {})
    if isinstance(technique_stage, dict):
        listed = technique_stage.get("technique_card_ids", [])
        if not isinstance(listed, list) or any(not isinstance(item, str) or item not in card_set for item in listed):
            errors.append("stages.technique.technique_card_ids must refer to existing technique cards.")
    for card in cards:
        if isinstance(card, dict) and card.get("sop_id") is not None and (not isinstance(card["sop_id"], str) or card["sop_id"] not in sop_set):
            errors.append(f"Technique card {card.get('card_id', '?')} refers to a missing SOP.")

    practice = stages.get("practice", {})
    if isinstance(practice, dict):
        assignment = practice.get("assignment")
        if isinstance(assignment, dict) and (not isinstance(assignment.get("technique_card_id"), str) or assignment["technique_card_id"] not in card_set):
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
