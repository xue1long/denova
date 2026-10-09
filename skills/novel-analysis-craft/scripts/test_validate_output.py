"""Regression checks for checkpoint integrity and bundled examples."""

import contextlib
import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate_output", ROOT / "scripts/validate_output.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ValidateOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads((ROOT / "examples/quick-demo.output.json").read_text(encoding="utf-8"))

    def check(self, output, new_input=None):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "output.json"
            path.write_text(json.dumps(output, ensure_ascii=False), encoding="utf-8")
            args = ["validate_output.py", str(path)]
            if new_input is not None:
                incoming = Path(folder) / "input.json"
                incoming.write_text(json.dumps(new_input, ensure_ascii=False), encoding="utf-8")
                args += ["--input", str(incoming)]
            stream = io.StringIO()
            with patch.object(sys, "argv", args), contextlib.redirect_stdout(stream):
                status = validator.main()
            return status, stream.getvalue()

    def test_bundled_outputs_pass(self):
        for path in ROOT.glob("examples/**/*.output.json"):
            with self.subTest(path=path.name):
                status, message = self.check(json.loads(path.read_text(encoding="utf-8")))
                self.assertEqual(status, 0, message)

    def test_evidence_must_match_source_chunk(self):
        output = copy.deepcopy(self.base)
        output["evidence"][0]["chapter_id"] = "ch99"
        status, message = self.check(output)
        self.assertEqual(status, 1)
        self.assertIn("chapter differs", message)

    def test_zero_coverage_cannot_be_complete(self):
        output = copy.deepcopy(self.base)
        output["coverage"].update(processed_chapter_ids=[], pending_chapter_ids=["ch01", "ch02", "ch03"], coverage_percent=0, completeness="partial", last_processed_chapter_id=None)
        output["run"]["status"] = "complete"
        status, message = self.check(output)
        self.assertEqual(status, 1)
        self.assertIn("no processed chapters", message)

    def test_title_only_analysis_can_finish_with_tentative_claims(self):
        output = copy.deepcopy(self.base)
        output["work"]["scope"] = "title_only"
        output["source_chunks"] = []
        output["evidence"] = []
        output["coverage"].update(expected_chapter_ids=[], received_chapter_ids=[], processed_chapter_ids=[], pending_chapter_ids=[], coverage_percent=None, completeness="unknown", last_processed_chapter_id=None)
        output["run"]["status"] = "complete"
        for claim in output["claims"]:
            claim.update(kind="inference", confidence="low", evidence_refs=[])
        for card in output["technique_cards"]:
            card.update(confidence="low", evidence_refs=[])
        status, message = self.check(output)
        self.assertEqual(status, 0, message)
        if importlib.util.find_spec("jsonschema"):
            import jsonschema
            schema = json.loads((ROOT / "schemas/output.schema.json").read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator(schema).validate(output)

    def test_unsourced_observation_is_rejected(self):
        output = copy.deepcopy(self.base)
        output["claims"][0]["evidence_refs"] = []
        status, message = self.check(output)
        self.assertEqual(status, 1)
        self.assertIn("low-confidence inference or evaluation", message)

    @unittest.skipUnless(importlib.util.find_spec("jsonschema"), "optional jsonschema package unavailable")
    def test_title_only_input_needs_no_rights_or_source(self):
        import jsonschema

        schema = json.loads((ROOT / "schemas/input.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate({
            "schema_version": "1.0", "work": {"title": "A Novel"},
            "analysis": {"mode": "quick", "scope": "title_only"},
        })

    def test_missing_schema_required_next_action_fails(self):
        output = copy.deepcopy(self.base)
        del output["run"]["next_action"]
        status, message = self.check(output)
        self.assertEqual(status, 1)
        self.assertIn("run.next_action", message)

    def test_resume_rejects_other_work_and_changed_chunk(self):
        incoming = json.loads((ROOT / "examples/quick-demo-resume.input.json").read_text(encoding="utf-8"))
        wrong_work = copy.deepcopy(incoming)
        wrong_work["work"]["title"] = "另一部作品"
        status, message = self.check(self.base, wrong_work)
        self.assertEqual(status, 1)
        self.assertIn("work.title differs", message)

        changed_chunk = copy.deepcopy(incoming)
        changed_chunk["source"]["chunks"][0]["chunk_id"] = "c01"
        status, message = self.check(self.base, changed_chunk)
        self.assertEqual(status, 1)
        self.assertIn("reuses chunk ID", message)

    @unittest.skipUnless(importlib.util.find_spec("jsonschema"), "optional jsonschema package unavailable")
    def test_bundled_examples_match_json_schema(self):
        import jsonschema

        for kind in ("input", "output"):
            schema = json.loads((ROOT / f"schemas/{kind}.schema.json").read_text(encoding="utf-8"))
            for path in ROOT.glob(f"examples/**/*.{kind}.json"):
                with self.subTest(path=path.name):
                    jsonschema.Draft202012Validator(schema).validate(json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
