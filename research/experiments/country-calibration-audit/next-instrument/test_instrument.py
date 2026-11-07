#!/usr/bin/env python3
"""Tests for the next-instrument candidate pilot runner.

Run:  python3 test_instrument.py

Every test uses SYNTHETIC mock model results where model output is needed;
no test calls any external API, and no test edits anything under data/,
tools/, or anywhere outside research/experiments/country-calibration-audit/
next-instrument/.

Requirement -> test mapping:
  no country input contains region scores/aggregates
      -> CountryInputsTests.test_no_region_scores_or_aggregates
  no hardcoded actual scores / foreign anchors
      -> SourcePolicyTests.test_no_hardcoded_scores_or_anchors
  national baseline from candidate national assessment, not published score
      -> CandidateBaselineTests.test_baseline_and_prompt_from_mock_national
  thin-evidence records get region identity and no fake evidence
      -> ThinRegionTests (identity, allowlist, unverified flags)
  missing national score / missing model output fail closed
      -> FailClosedTests
  input snapshots reproducible
      -> DeterminismTests.test_two_dry_runs_byte_identical
  proper output scale and invalid NaNs rejected
      -> ScaleContractTests
  no writes outside experiment, no API on dry-run
      -> WriteAndNetworkGuardTests
  single-dossier contract (no two-dossier output fields)
      -> ScaleContractTests.test_single_dossier_contract
"""
from __future__ import annotations

import builtins
import io
import json
import os
import shutil
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import instrument as inst  # noqa: E402


def temp_dir(tag: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=f"{tag}_", dir=HERE))


def mock_national_response(score: float, why: str = "synthetic mock") -> dict:
    return {
        "score": score,
        "uncertainty": "synthetic mock uncertainty for tests only",
        "evidence_date": "2026-01",
        "visitor_applicability": "synthetic mock visitor applicability",
        "social_friction": "synthetic mock friction",
        "social_hostility": "synthetic mock hostility",
        "state_threat_framing": "synthetic mock state framing",
        "why": why,
    }


def write_results(path: Path, rows: list) -> Path:
    path.write_text("".join(json.dumps(r) + "\n" for r in rows),
                    encoding="utf-8")
    return path


def mock_region_response(region_id: str, mode: str, delta: float) -> dict:
    base = {
        "assessment_mode": mode,
        "region_id": region_id,
        "local_delta": delta,
        "sourced_local_evidence": [],
        "knowledge_statements": [],
        "knowledge_confidence": "n/a",
        "knowledge_is_unverified": False,
        "inherited_national_exposure": [
            "synthetic mock: national factor not re-counted"],
        "uncertainty": "synthetic mock uncertainty",
        "evidence_date": "2026-01",
        "visitor_applicability": "synthetic mock visitor applicability",
        "social_friction": "none documented",
        "social_hostility": "none documented",
        "state_threat_framing": "none documented",
        "notes": "synthetic mock note",
        "departures": [],
    }
    if mode == "model_knowledge":
        base.update({
            "knowledge_confidence": "low",
            "knowledge_is_unverified": True,
            "knowledge_statements": ["synthetic mock recalled statement"],
        })
    return base


def published_score_strings() -> set:
    """Every published score in data/, formatted the ways text could show it."""
    out = set()
    countries = inst.load_countries()
    admin1 = inst.load_admin1()
    for rec in list(countries.values()) + list(admin1.values()):
        v = rec.get("score")
        if isinstance(v, (int, float)) and v not in (0.0, 0.5, 1.0):
            out.add(f"{v}")
            out.add(f"{v:.6f}")
        ds = rec.get("divisionSpread")
        if isinstance(ds, dict):
            for stat in ("min", "max", "sd"):
                sv = ds.get(stat)
                if isinstance(sv, (int, float)) and sv not in (0.0, 0.5, 1.0):
                    out.add(f"{sv}")
                    out.add(f"{sv:.6f}")
    return out


class DryRunMixin:
    @classmethod
    def render_once(cls, national_results=None):
        out = temp_dir("dryrun")
        manifest = inst.dry_run(out, national_results=national_results)
        return out, manifest


# --------------------------------------------------------------------------- #
class CountryInputsTests(DryRunMixin, unittest.TestCase):
    """No country input may contain region scores or ADM1 aggregates."""

    @classmethod
    def setUpClass(cls):
        cls.out, cls.manifest = cls.render_once()
        cls.national_texts = [
            (cls.out / c["user_prompt_file"]).read_text(encoding="utf-8")
            for c in cls.manifest["calls"] if c["phase"] == "national"
        ] + [
            (cls.out / "prompts" / "system_national.txt").read_text("utf-8"),
            (cls.out / "prompts" / "system_region.txt").read_text("utf-8"),
        ]
        cls.snapshot_texts = [
            p.read_text("utf-8") for p in sorted((cls.out / "snapshots").glob("*.json"))
        ]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out, ignore_errors=True)

    def test_no_region_scores_in_country_prompts(self):
        admin1 = inst.load_admin1()
        for rec in admin1.values():
            v = rec.get("score")
            if not isinstance(v, (int, float)):
                continue
            for form in (f"{v}", f"{v:.6f}"):
                for text in self.national_texts:
                    self.assertNotIn(
                        form, text,
                        f"region score {form} ({rec.get('name')}) leaked into "
                        "a country/system prompt")

    def test_no_admin1_aggregates_in_country_prompts(self):
        countries = inst.load_countries()
        for iso in inst.COUNTRY_IDS:
            ds = countries[iso].get("divisionSpread")
            if not isinstance(ds, dict):
                continue
            blob = json.dumps(ds)
            for text in self.national_texts:
                self.assertNotIn(blob, text, f"divisionSpread of {iso} leaked")
                for stat in ("min", "max", "sd"):
                    sv = ds.get(stat)
                    if isinstance(sv, (int, float)):
                        self.assertNotIn(f"{sv:.6f}", text,
                                         f"divisionSpread {stat} of {iso} leaked")
        for token in ("divisionSpread", "countryRank", "worldRank",
                      "unitsInCountry", "anchorRefs", "derivedFrom",
                      "nationalFrameworkScore"):
            for text in self.national_texts + self.snapshot_texts:
                self.assertNotIn(token, text, f"{token} leaked into input")

    def test_snapshots_whitelisted(self):
        for path in sorted((self.out / "snapshots").glob("*.json")):
            snap = json.loads(path.read_text("utf-8"))
            inst.assert_no_forbidden_keys(snap, path.name)
            if snap["subject_kind"] == "country":
                self.assertEqual(set(snap["fields"]),
                                 set(inst.COUNTRY_DOSSIER_FIELDS))
                self.assertNotIn("score", snap)


# --------------------------------------------------------------------------- #
class SourcePolicyTests(unittest.TestCase):
    """No hardcoded actual scores or foreign-country anchors in the runner."""

    def test_no_hardcoded_scores_or_anchors(self):
        source = Path(inst.__file__).read_text(encoding="utf-8")
        for lit in published_score_strings():
            self.assertNotIn(
                lit, source,
                f"published score literal {lit!r} hardcoded in instrument.py")
        for iso in ("ISL", "NLD", "TUR", "EGY", "AFG", "CIV", "BLR"):
            self.assertNotIn(f'"{iso}"', source,
                             f"foreign anchor {iso} hardcoded")
        self.assertNotIn("ANCHOR_ISOS", source)
        self.assertNotIn("anchorRating", source)
        # policy lists are the ONLY place forbidden field names may appear,
        # and they exist to exclude, never to read:
        self.assertIn("score", inst.FORBIDDEN_INPUT_KEYS)
        self.assertIn("divisionSpread", inst.FORBIDDEN_INPUT_KEYS)
        self.assertIn("derivedFrom", inst.FORBIDDEN_INPUT_KEYS)

    def test_no_published_scores_in_rendered_inputs(self):
        out, manifest = DryRunMixin.render_once()
        try:
            literals = published_score_strings()
            texts = [p.read_text("utf-8") for p in
                     (out / "prompts").glob("*.txt")] + \
                    [p.read_text("utf-8") for p in
                     (out / "snapshots").glob("*.json")]
            for lit in literals:
                for text in texts:
                    self.assertNotIn(lit, text,
                                     f"published score {lit} appears in input")
        finally:
            shutil.rmtree(out, ignore_errors=True)


# --------------------------------------------------------------------------- #
class CandidateBaselineTests(unittest.TestCase):
    """National baseline comes from the candidate national assessment in
    shadow results, never from a published score; region prompts show it."""

    @classmethod
    def setUpClass(cls):
        cls.dir = temp_dir("baseline")
        cls.usa_scores = [0.412345, 0.412555]  # synthetic mock only
        cls.rows = [
            {"call_id": "NAT-USA-d1", "phase": "national", "country_id": "USA",
             "draw": 1, "status": "ok",
             "response": mock_national_response(cls.usa_scores[0])},
            {"call_id": "NAT-USA-d2", "phase": "national", "country_id": "USA",
             "draw": 2, "status": "ok",
             "response": mock_national_response(cls.usa_scores[1])},
        ]
        cls.results = write_results(cls.dir / "results.ndjson", cls.rows)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_national_result_reads_mock_scores(self):
        nat = inst.national_result_for("USA", self.results)
        expected = round(sum(self.usa_scores) / 2, 6)
        self.assertEqual(nat["baseline"], expected)
        self.assertEqual(nat["source_call_ids"], ["NAT-USA-d1", "NAT-USA-d2"])

    def test_region_prompt_contains_candidate_baseline_not_published(self):
        nat = inst.national_result_for("USA", self.results)
        spec = next(s for s in inst.REGION_SPECS if s["region_id"] == "USA-CA")
        prompt = inst.build_region_user_prompt(spec, nat)
        expected = round(sum(self.usa_scores) / 2, 6)
        self.assertIn(f"- candidate national score: {expected}", prompt)
        self.assertIn("NAT-USA-d1", prompt)          # provenance shown
        self.assertIn("NOT a published score", prompt)
        published = inst.load_countries()["USA"]["score"]
        self.assertNotEqual(expected, published)
        self.assertNotIn(f"{published:.6f}", prompt)
        # the complete national dossier is included for the comparison
        self.assertIn("### THE COMPLETE NATIONAL DOSSIER", prompt)

    def test_assemble_estimates_from_shadow_results_only(self):
        region_row = {
            "call_id": "REG-USA-CA-d1", "phase": "region",
            "region_id": "USA-CA", "country_id": "USA", "draw": 1,
            "status": "ok",
            "response": mock_region_response("USA-CA", "sourced", 0.02),
        }
        results = write_results(self.dir / "results2.ndjson",
                                self.rows + [region_row])
        out_path = self.dir / "estimates.ndjson"
        rows = inst.assemble(results, out_path)
        baseline = next(r for r in rows if r["kind"] == "national_baseline"
                        and r["country_id"] == "USA")
        self.assertEqual(baseline["candidate_national_score"],
                         round(sum(self.usa_scores) / 2, 6))
        self.assertEqual(baseline["source_call_ids"],
                         ["NAT-USA-d1", "NAT-USA-d2"])
        est = next(r for r in rows if r["kind"] == "region_estimate"
                   and r["region_id"] == "USA-CA")
        self.assertAlmostEqual(est["local_estimate"],
                               round(sum(self.usa_scores) / 2, 6) + 0.02,
                               places=6)
        self.assertEqual(est["candidate_national_score"],
                         baseline["candidate_national_score"])
        # and the written file matches the returned rows
        written = [json.loads(x) for x in
                   out_path.read_text("utf-8").splitlines() if x.strip()]
        self.assertEqual(written, rows)


# --------------------------------------------------------------------------- #
class ThinRegionTests(unittest.TestCase):
    """The genuinely thin-evidence region gets a distinct, identified,
    explicitly uncertain knowledge-only record with no fake evidence."""

    @classmethod
    def setUpClass(cls):
        cls.dir = temp_dir("thin")
        npl_rows = [
            {"call_id": "NAT-NPL-d1", "phase": "national", "country_id": "NPL",
             "draw": 1, "status": "ok",
             "response": mock_national_response(0.612345)},
            {"call_id": "NAT-NPL-d2", "phase": "national", "country_id": "NPL",
             "draw": 2, "status": "ok",
             "response": mock_national_response(0.612555)},
        ]
        cls.results = write_results(cls.dir / "results.ndjson", npl_rows)
        cls.spec = next(s for s in inst.REGION_SPECS
                        if s["region_id"] == "NPL-KAR")
        cls.nat = inst.national_result_for("NPL", cls.results)
        cls.prompt = inst.build_region_user_prompt(cls.spec, cls.nat)
        cls.snap = inst.region_snapshot(cls.spec)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_prompt_identifies_actual_named_region(self):
        self.assertIn("Karnali", self.prompt)
        self.assertIn("NPL-KAR", self.prompt)
        self.assertIn("model-knowledge assessment of this actual named "
                      "region", self.prompt)
        self.assertIn("NO provided local evidence", self.prompt)
        self.assertIn("unverified route-3 estimate text, not verified local "
                      "evidence", self.prompt)

    def test_snapshot_separates_knowledge_from_sourced_evidence(self):
        self.assertEqual(self.snap["local_evidence_allowlist"], [])
        self.assertTrue(self.snap["country_level_sources_not_local"])
        self.assertEqual(self.snap["evidence_path"], "knowledge-only")
        inst.assert_no_forbidden_keys(self.snap, "NPL-KAR")

    def test_valid_knowledge_record_accepted(self):
        resp = mock_region_response("NPL-KAR", "model_knowledge", -0.02)
        parsed = inst.validate_region(resp, self.spec, self.snap)
        self.assertEqual(parsed["assessment_mode"], "model_knowledge")
        self.assertIs(parsed["knowledge_is_unverified"], True)

    def test_fake_evidence_rejected(self):
        resp = mock_region_response("NPL-KAR", "model_knowledge", -0.02)
        resp["sourced_local_evidence"] = ["https://example.org/invented"]
        with self.assertRaises(inst.ValidationError):
            inst.validate_region(resp, self.spec, self.snap)

    def test_knowledge_guess_cannot_claim_verified(self):
        resp = mock_region_response("NPL-KAR", "model_knowledge", -0.02)
        resp["knowledge_is_unverified"] = False
        with self.assertRaises(inst.ValidationError):
            inst.validate_region(resp, self.spec, self.snap)

    def test_knowledge_record_cannot_smuggle_departures(self):
        resp = mock_region_response("NPL-KAR", "model_knowledge", -0.02)
        resp["departures"] = [{"fact": "x", "local_evidence": "y",
                               "direction": "safer", "magnitude": 0.01,
                               "visitor_applicability": "z",
                               "already_in_national_bundle": False,
                               "counted_in_delta": True,
                               "evidence_date": "2026-01",
                               "uncertainty": "u"}]
        with self.assertRaises(inst.ValidationError):
            inst.validate_region(resp, self.spec, self.snap)

    def test_region_identity_echo_enforced(self):
        resp = mock_region_response("NPL-KAR", "model_knowledge", -0.02)
        resp["region_id"] = "NPL-BAG"
        with self.assertRaises(inst.ValidationError):
            inst.validate_region(resp, self.spec, self.snap)

    def test_sourced_region_cannot_claim_knowledge_mode(self):
        ca_spec = next(s for s in inst.REGION_SPECS
                       if s["region_id"] == "USA-CA")
        ca_snap = inst.region_snapshot(ca_spec)
        resp = mock_region_response("USA-CA", "model_knowledge", -0.02)
        with self.assertRaises(inst.ValidationError):
            inst.validate_region(resp, ca_spec, ca_snap)


# --------------------------------------------------------------------------- #
class FailClosedTests(unittest.TestCase):
    def test_region_prompt_without_baseline_fails_closed(self):
        spec = inst.REGION_SPECS[0]
        with self.assertRaises(inst.FailClosed):
            inst.build_region_user_prompt(spec, None)

    def test_national_result_missing_file_fails_closed(self):
        with self.assertRaises(inst.FailClosed):
            inst.national_result_for("USA", HERE / "does-not-exist.ndjson")

    def test_national_result_no_rows_fails_closed(self):
        d = temp_dir("failclosed")
        try:
            empty = write_results(d / "empty.ndjson", [])
            with self.assertRaises(inst.FailClosed):
                inst.national_result_for("USA", empty)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_dry_run_region_calls_pending_without_national_results(self):
        out, manifest = DryRunMixin.render_once()
        try:
            regions = [c for c in manifest["calls"] if c["phase"] == "region"]
            self.assertTrue(regions)
            for c in regions:
                self.assertEqual(c["status"], "pending_national_baseline")
                self.assertIsNone(c["user_prompt_file"])
                self.assertIsNone(c["user_sha256"])
                self.assertIsNotNone(c["snapshot_sha256"])
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_assemble_missing_model_output_fails_closed(self):
        d = temp_dir("failclosed2")
        try:
            rows = [
                {"call_id": "NAT-USA-d1", "phase": "national",
                 "country_id": "USA", "draw": 1, "status": "ok",
                 "response": mock_national_response(0.412345)},
                # region call: status ok but NO model output at all
                {"call_id": "REG-USA-CA-d1", "phase": "region",
                 "region_id": "USA-CA", "country_id": "USA", "draw": 1,
                 "status": "ok", "response": None},
                # region call: failed status with error
                {"call_id": "REG-USA-TX-d1", "phase": "region",
                 "region_id": "USA-TX", "country_id": "USA", "draw": 1,
                 "status": "failed", "error": "model output missing",
                 "response": None},
            ]
            results = write_results(d / "results.ndjson", rows)
            out_rows = inst.assemble(results, d / "est.ndjson")
            for rid in ("USA-CA", "USA-TX"):
                r = next(x for x in out_rows
                         if x["kind"] == "region_estimate"
                         and x.get("region_id") == rid)
                self.assertNotIn("local_estimate", r)
                self.assertTrue(r.get("error"))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_assemble_missing_national_baseline_fails_closed(self):
        d = temp_dir("failclosed3")
        try:
            rows = [
                {"call_id": "REG-NPL-BAG-d1", "phase": "region",
                 "region_id": "NPL-BAG", "country_id": "NPL", "draw": 1,
                 "status": "ok",
                 "response": mock_region_response("NPL-BAG", "sourced", 0.01)},
            ]
            results = write_results(d / "results.ndjson", rows)
            out_rows = inst.assemble(results, d / "est.ndjson")
            r = next(x for x in out_rows
                     if x["kind"] == "region_estimate"
                     and x.get("region_id") == "NPL-BAG")
            self.assertNotIn("local_estimate", r)
            self.assertIn("missing candidate national baseline", r["error"])
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_assemble_rejects_nan_and_out_of_scale(self):
        d = temp_dir("failclosed4")
        try:
            bad_national = mock_national_response(float("nan"))
            nan_delta = mock_region_response("USA-CA", "sourced", 0.02)
            nan_delta["local_delta"] = float("nan")
            big_delta = mock_region_response("USA-TX", "sourced", 2.5)
            rows = [
                {"call_id": "NAT-USA-d1", "phase": "national",
                 "country_id": "USA", "draw": 1, "status": "ok",
                 "response": bad_national},
                {"call_id": "REG-USA-CA-d1", "phase": "region",
                 "region_id": "USA-CA", "country_id": "USA", "draw": 1,
                 "status": "ok", "response": nan_delta},
                {"call_id": "REG-USA-TX-d1", "phase": "region",
                 "region_id": "USA-TX", "country_id": "USA", "draw": 1,
                 "status": "ok", "response": big_delta},
            ]
            results = write_results(d / "results.ndjson", rows)
            out_rows = inst.assemble(results, d / "est.ndjson")
            baseline = next(x for x in out_rows
                            if x["kind"] == "national_baseline"
                            and x["country_id"] == "USA")
            self.assertNotIn("candidate_national_score", baseline)  # NaN
            for rid in ("USA-CA", "USA-TX"):
                r = next(x for x in out_rows
                         if x["kind"] == "region_estimate"
                         and x.get("region_id") == rid)
                self.assertNotIn("local_estimate", r)
                self.assertTrue(r.get("error"))
        finally:
            shutil.rmtree(d, ignore_errors=True)


# --------------------------------------------------------------------------- #
class DeterminismTests(DryRunMixin, unittest.TestCase):
    def test_two_dry_runs_byte_identical(self):
        out1, man1 = self.render_once()
        out2, man2 = self.render_once()
        try:
            self.assertEqual(man1, man2)
            files1 = {p.relative_to(out1): p.read_bytes()
                      for p in out1.rglob("*") if p.is_file()}
            files2 = {p.relative_to(out2): p.read_bytes()
                      for p in out2.rglob("*") if p.is_file()}
            self.assertEqual(set(files1), set(files2))
            for rel, data in files1.items():
                self.assertEqual(data, files2[rel], f"{rel} differs")
        finally:
            shutil.rmtree(out1, ignore_errors=True)
            shutil.rmtree(out2, ignore_errors=True)

    def test_manifest_hashes_match_saved_files(self):
        out, manifest = self.render_once()
        try:
            self.assertEqual(manifest["instrument"]["mode"], "dry-run")
            self.assertIs(manifest["instrument"]["network"], False)
            self.assertIs(manifest["instrument"]["provider_enabled"], False)
            for call in manifest["calls"]:
                if call["user_prompt_file"]:
                    text = (out / call["user_prompt_file"]).read_text("utf-8")
                    self.assertEqual(inst.sha(text), call["user_sha256"])
                snap = (out / call["snapshot_file"]).read_text("utf-8")
                self.assertEqual(inst.sha(snap), call["snapshot_sha256"])
            self.assertEqual(
                inst.sha((out / "prompts" / "system_national.txt")
                         .read_text("utf-8")),
                manifest["systems"]["national"])
            # input digests recorded for reproducibility
            for rel, digest in manifest["inputs_sha256"].items():
                p = inst.ROOT / rel
                self.assertEqual(inst.file_sha256(p), digest)
        finally:
            shutil.rmtree(out, ignore_errors=True)


# --------------------------------------------------------------------------- #
class ScaleContractTests(DryRunMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out, cls.manifest = cls.render_once()
        cls.nat_system = (cls.out / "prompts" /
                          "system_national.txt").read_text("utf-8")
        cls.reg_system = (cls.out / "prompts" /
                          "system_region.txt").read_text("utf-8")
        # prompt prose is hard-wrapped; assert against whitespace-normalised
        # text so the checks are about content, not line breaks
        cls.nat_norm = " ".join(cls.nat_system.split())
        cls.reg_norm = " ".join(cls.reg_system.split())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out, ignore_errors=True)

    def test_zero_anchor_and_no_or_execution(self):
        for text in (self.nat_norm, self.reg_norm):
            self.assertIn("near-certain imprisonment and likely execution",
                          text)
            self.assertNotIn("imprisonment or execution", text)
            self.assertIn("orientation only", text)
            self.assertIn("NO intermediate anchors", text)
            self.assertIn("no anchor country", text)

    def test_no_credit_for_passing(self):
        for text in (self.nat_norm, self.reg_norm):
            self.assertIn("no credit because a visitor could pass", text)

    def test_social_framing_distinctions_present(self):
        for text in (self.nat_norm, self.reg_norm):
            self.assertIn("Social friction, social hostility, "
                          "state threat-framing", text)
            self.assertIn("Social conservatism by itself is NOT hostility",
                          text)
            for field in ("social_friction", "social_hostility",
                          "state_threat_framing"):
                self.assertIn(f'"{field}"', text)

    def test_single_dossier_contract(self):
        self.assertIn('"score": <float 0.0-1.0>', self.nat_system)
        self.assertIn("must be no `score_a` or `score_b` field",
                      self.nat_system)
        self.assertIn('"local_delta": <float', self.reg_system)
        # neither system prompt carries the production two-dossier example
        for text in (self.nat_system, self.reg_system):
            self.assertNotIn('"score_a": <float', text)

    def test_region_schema_retains_required_fields(self):
        for field in ("uncertainty", "evidence_date",
                      "visitor_applicability", "local_delta",
                      "already_in_national_bundle", "counted_in_delta",
                      "inherited_national_exposure"):
            self.assertIn(f'"{field}"', self.reg_system)
        for field in ("uncertainty", "evidence_date",
                      "visitor_applicability"):
            self.assertIn(f'"{field}"', self.nat_system)

    def test_parse_rejects_nan_and_infinity(self):
        for bad in ('{"score": NaN, "why": "x"}',
                    '{"score": Infinity, "why": "x"}',
                    '{"score": -Infinity, "why": "x"}'):
            with self.assertRaises(inst.ValidationError):
                inst.parse_model_json(bad)
        with self.assertRaises(inst.ValidationError):
            inst.parse_model_json("no object here")
        with self.assertRaises(inst.ValidationError):
            inst.parse_model_json("")

    def test_national_scale_validation(self):
        good = mock_national_response(0.5)
        self.assertEqual(inst.validate_national(good)["score"], 0.5)
        for bad_score in (1.5, -0.1, 1.0001, float("nan"), float("inf"),
                          True, "0.5", None):
            obj = dict(good, score=bad_score)
            with self.assertRaises(inst.ValidationError,
                                   msg=f"accepted score {bad_score!r}"):
                inst.validate_national(obj)
        missing = dict(good)
        missing.pop("uncertainty")
        with self.assertRaises(inst.ValidationError):
            inst.validate_national(missing)
        two_dossier = dict(good, score_a=0.4, score_b=0.6)
        with self.assertRaises(inst.ValidationError):
            inst.validate_national(two_dossier)

    def test_region_scale_validation(self):
        spec = next(s for s in inst.REGION_SPECS
                    if s["region_id"] == "USA-CA")
        snap = inst.region_snapshot(spec)
        good = mock_region_response("USA-CA", "sourced", -0.05)
        self.assertEqual(inst.validate_region(good, spec, snap)["local_delta"],
                         -0.05)
        for bad_delta in (2.5, -1.5, float("nan"), float("inf"), "0.1",
                          True):
            obj = dict(good, local_delta=bad_delta)
            with self.assertRaises(inst.ValidationError,
                                   msg=f"accepted delta {bad_delta!r}"):
                inst.validate_region(obj, spec, snap)


# --------------------------------------------------------------------------- #
class WriteAndNetworkGuardTests(DryRunMixin, unittest.TestCase):
    """Dry-run performs no writes outside the experiment directory and no
    network calls; provider execution is off by default."""

    def test_dry_run_under_open_and_socket_guard(self):
        out = temp_dir("guarded")
        orig_open = io.open

        def guarded_open(file, mode="r", *args, **kwargs):
            if isinstance(file, (str, bytes, os.PathLike)) and any(
                    c in mode for c in "wax+"):
                resolved = Path(os.fspath(file))
                if not resolved.is_absolute():
                    resolved = Path.cwd() / resolved
                resolved = resolved.resolve()
                here = HERE.resolve()
                if str(resolved) != str(here) and not str(resolved).startswith(
                        str(here) + os.sep):
                    raise AssertionError(
                        f"WRITE OUTSIDE EXPERIMENT ATTEMPTED: {resolved}")
            return orig_open(file, mode, *args, **kwargs)

        def no_socket(*_args, **_kwargs):
            raise AssertionError("NETWORK ATTEMPTED during dry-run")

        with mock.patch.object(io, "open", guarded_open), \
                mock.patch.object(builtins, "open", guarded_open), \
                mock.patch.object(socket, "socket", no_socket), \
                mock.patch.object(socket, "create_connection", no_socket), \
                mock.patch.object(socket, "getaddrinfo", no_socket):
            # sanity: the guard really rejects an outside write
            with self.assertRaises(AssertionError):
                guarded_open("/tmp/next-instrument-guard-probe", "w")
            manifest = inst.dry_run(out)
            self.assertEqual(len(manifest["calls"]), inst.MAX_CALLS)
        shutil.rmtree(out, ignore_errors=True)

    def test_execute_unconditionally_disabled(self):
        # The live path and its network code were removed; the OLD guard
        # inputs (flag + env var) must still be unable to enable anything.
        source = Path(inst.__file__).read_text(encoding="utf-8")
        self.assertNotIn("urllib", source)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("require_provider_guard", source)
        self.assertFalse(hasattr(inst, "require_provider_guard"))

        def no_socket(*_a, **_k):
            raise AssertionError("NETWORK ATTEMPTED via execute")

        with mock.patch.object(socket, "socket", no_socket), \
                mock.patch.object(socket, "create_connection", no_socket), \
                mock.patch.object(socket, "getaddrinfo", no_socket), \
                mock.patch.dict(os.environ):
            os.environ["NEXT_INSTRUMENT_ALLOW_PROVIDER"] = "reviewed"
            rc = inst.main(["execute", "--endpoint",
                            "https://example.invalid/v1",
                            "--results", str(HERE / "no-such-file.ndjson"),
                            "--allow-provider"])
            self.assertEqual(rc, 1)
            with self.assertRaises(inst.ProviderDisabledError):
                inst.execute()  # direct call refuses unconditionally

    def test_dry_run_cli_and_out_constraint(self):
        out = temp_dir("cli")
        rc = inst.main(["dry-run", "--out", str(out)])
        self.assertEqual(rc, 0)
        rc_outside = inst.main(["dry-run", "--out",
                               "/tmp/next-instrument-outside"])
        self.assertEqual(rc_outside, 1)  # fail-closed, nothing written
        shutil.rmtree(out, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Regressions added after the independent review (BLOCK verdict)
# --------------------------------------------------------------------------- #

def _nat_rows(country, scores, call_prefix=None, run_ids=None):
    rows = []
    prefix = call_prefix or f"NAT-{country}"
    for d, s in enumerate(scores, 1):
        row = {"call_id": f"{prefix}-d{d}", "phase": "national",
               "country_id": country, "draw": d, "status": "ok",
               "response": mock_national_response(s)}
        if run_ids is not None:
            row["run_id"] = run_ids[d - 1]
        rows.append(row)
    return rows


def _departure(fact, local_evidence):
    return {"fact": fact, "local_evidence": local_evidence,
            "direction": "safer", "magnitude": 0.01,
            "visitor_applicability": "applies to a visitor",
            "already_in_national_bundle": False, "counted_in_delta": True,
            "evidence_date": "2026-01", "uncertainty": "u"}


class OutOfScaleEstimateTests(unittest.TestCase):
    """P0: baseline+delta outside [0,1] must yield an error record, never a
    value (and never a clamped value)."""

    def test_out_of_scale_estimate_rejected_without_clamping(self):
        d = temp_dir("oos")
        try:
            # LEGACY WITNESS: the pre-fix computation emitted
            # round(0.87 + 0.5, 6) = 1.37 with no error record at all.
            self.assertGreater(round(0.87 + 0.5, 6), 1.0)
            rows = _nat_rows("USA", [0.87, 0.87]) + [
                {"call_id": "REG-USA-CA-d1", "phase": "region",
                 "region_id": "USA-CA", "country_id": "USA", "draw": 1,
                 "status": "ok",
                 "response": mock_region_response("USA-CA", "sourced", 0.5)}]
            results = write_results(d / "results.ndjson", rows)
            out_rows = inst.assemble(results, d / "est.ndjson")
            est = next(r for r in out_rows
                       if r["kind"] == "region_estimate"
                       and r.get("region_id") == "USA-CA")
            self.assertNotIn("local_estimate", est)
            self.assertIn("outside the [0.0, 1.0] scale", est["error"])
            self.assertIn("without clamping", est["error"])
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_boundary_estimates_accepted_exactly(self):
        d = temp_dir("oos2")
        try:
            rows = _nat_rows("USA", [0.5, 0.5]) + [
                {"call_id": "REG-USA-CA-d1", "phase": "region",
                 "region_id": "USA-CA", "country_id": "USA", "draw": 1,
                 "status": "ok",
                 "response": mock_region_response("USA-CA", "sourced", -0.5)},
                {"call_id": "REG-USA-TX-d1", "phase": "region",
                 "region_id": "USA-TX", "country_id": "USA", "draw": 1,
                 "status": "ok",
                 "response": mock_region_response("USA-TX", "sourced", 0.5)}]
            results = write_results(d / "results.ndjson", rows)
            out_rows = inst.assemble(results, d / "est.ndjson")
            ca = next(r for r in out_rows if r.get("region_id") == "USA-CA"
                      and r["kind"] == "region_estimate")
            tx = next(r for r in out_rows if r.get("region_id") == "USA-TX"
                      and r["kind"] == "region_estimate")
            self.assertEqual(ca["local_estimate"], 0.0)   # exact floor ok
            self.assertEqual(tx["local_estimate"], 1.0)   # exact ceiling ok
        finally:
            shutil.rmtree(d, ignore_errors=True)


class BaselineIntegrityTests(unittest.TestCase):
    """Fail closed on duplicate call IDs, mixed run identity, and missing
    required national draws; report, never silently average."""

    def test_duplicate_call_ids_fail_closed(self):
        d = temp_dir("dup")
        try:
            rows = _nat_rows("USA", [0.4, 0.42])
            rows[1]["call_id"] = rows[0]["call_id"]  # duplicate identity
            f = write_results(d / "results.ndjson", rows)
            with self.assertRaises(inst.FailClosed) as cm:
                inst.national_result_for("USA", f)
            self.assertIn("duplicate call_id", str(cm.exception))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_mixed_run_identity_fail_closed(self):
        d = temp_dir("mix")
        try:
            rows = _nat_rows("USA", [0.4, 0.42],
                             run_ids=["run-earlier", "run-later"])
            f = write_results(d / "results.ndjson", rows)
            with self.assertRaises(inst.FailClosed) as cm:
                inst.national_result_for("USA", f)
            self.assertIn("mixed run identity", str(cm.exception))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_single_draw_never_averaged(self):
        d = temp_dir("onedraw")
        try:
            rows = _nat_rows("USA", [0.4]) + [
                {"call_id": "REG-USA-CA-d1", "phase": "region",
                 "region_id": "USA-CA", "country_id": "USA", "draw": 1,
                 "status": "ok",
                 "response": mock_region_response("USA-CA", "sourced", 0.02)}]
            f = write_results(d / "results.ndjson", rows)
            with self.assertRaises(inst.FailClosed) as cm:
                inst.national_result_for("USA", f)
            self.assertIn("missing required national draws", str(cm.exception))
            out_rows = inst.assemble(f, d / "est.ndjson")
            base = next(r for r in out_rows if r["kind"] == "national_baseline"
                        and r["country_id"] == "USA")
            self.assertNotIn("candidate_national_score", base)  # no averaging
            self.assertIn("missing required national draws", base["error"])
            est = next(r for r in out_rows
                       if r["kind"] == "region_estimate"
                       and r.get("region_id") == "USA-CA")
            self.assertNotIn("local_estimate", est)
            self.assertIn("missing candidate national baseline", est["error"])
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_malformed_results_line_fail_closed(self):
        d = temp_dir("badline")
        try:
            f = d / "results.ndjson"
            f.write_text('{"call_id": "NAT-USA-d1", "phase": "national"}\n'
                         "{not json at all\n", encoding="utf-8")
            with self.assertRaises(inst.FailClosed) as cm:
                inst.national_result_for("USA", f)
            self.assertIn("malformed results line 2", str(cm.exception))
        finally:
            shutil.rmtree(d, ignore_errors=True)


class SourcedEvidenceTests(unittest.TestCase):
    """Sourced-mode evidence claims must tie to actually provided local
    evidence; copied country-level URLs cannot be relabelled local."""

    @classmethod
    def setUpClass(cls):
        cls.dir = temp_dir("sourced")
        cls.ca_spec = next(s for s in inst.REGION_SPECS
                           if s["region_id"] == "USA-CA")
        cls.bag_spec = next(s for s in inst.REGION_SPECS
                            if s["region_id"] == "NPL-BAG")
        cls.ca_snap = inst.region_snapshot(cls.ca_spec)
        cls.bag_snap = inst.region_snapshot(cls.bag_spec)
        cls.npl_results = write_results(
            cls.dir / "npl.ndjson",
            _nat_rows("NPL", [0.612345, 0.612555]))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_bagmati_country_urls_not_in_local_allowlist(self):
        allow = self.bag_snap["local_evidence_allowlist"]
        urls = self.bag_snap["country_level_sources_not_local"]
        self.assertTrue(urls, "Bagmati record sources expected")
        for u in urls:
            self.assertNotIn(u, allow)
        self.assertEqual(len(allow), 1)  # only the region's own record text

    def test_bagmati_citing_actual_national_url_rejected(self):
        # actual URL from data/admin1.json for Bagmati
        hrw = self.bag_snap["country_level_sources_not_local"][0]
        self.assertIn("hrw.org", hrw)
        resp = mock_region_response("NPL-BAG", "sourced", 0.01)
        resp["sourced_local_evidence"] = [hrw]
        with self.assertRaises(inst.ValidationError) as cm:
            inst.validate_region(resp, self.bag_spec, self.bag_snap)
        self.assertIn("not provided in the snapshot", str(cm.exception))

    def test_bagmati_record_text_accepted_as_local_evidence(self):
        resp = mock_region_response("NPL-BAG", "sourced", 0.01)
        resp["sourced_local_evidence"] = [
            self.bag_snap["local_evidence_allowlist"][0]]
        parsed = inst.validate_region(resp, self.bag_spec, self.bag_snap)
        self.assertEqual(parsed["assessment_mode"], "sourced")

    def test_sourced_fabricated_evidence_rejected(self):
        resp = mock_region_response("USA-CA", "sourced", 0.02)
        resp["sourced_local_evidence"] = ["https://example.org/invented"]
        with self.assertRaises(inst.ValidationError):
            inst.validate_region(resp, self.ca_spec, self.ca_snap)

    def test_sourced_actual_provided_item_accepted(self):
        resp = mock_region_response("USA-CA", "sourced", 0.02)
        resp["sourced_local_evidence"] = [
            self.ca_snap["local_evidence_allowlist"][0]]
        inst.validate_region(resp, self.ca_spec, self.ca_snap)

    def test_departure_citing_fabricated_evidence_rejected(self):
        resp = mock_region_response("USA-CA", "sourced", 0.02)
        resp["departures"] = [_departure(
            "synthetic mock fact", "https://example.org/fabricated")]
        with self.assertRaises(inst.ValidationError) as cm:
            inst.validate_region(resp, self.ca_spec, self.ca_snap)
        self.assertIn("fabrication guard", str(cm.exception))

    def test_departure_none_provided_allowed(self):
        resp = mock_region_response("USA-CA", "sourced", 0.02)
        resp["departures"] = [_departure("synthetic mock fact",
                                         "none provided")]
        inst.validate_region(resp, self.ca_spec, self.ca_snap)

    def test_bagmati_prompt_flags_sources_and_data_status(self):
        nat = inst.national_result_for("NPL", self.npl_results)
        prompt = inst.build_region_user_prompt(self.bag_spec, nat)
        self.assertIn("COUNTRY-LEVEL RECORD SOURCES - NOT LOCAL EVIDENCE",
                      prompt)
        self.assertIn("must NOT be listed as provided local evidence",
                      prompt)
        self.assertIn("### DATA STATUS", prompt)


class WriteConfinementTests(unittest.TestCase):
    def test_write_rejects_outside_path(self):
        probe = Path("/tmp/next-instrument-write-probe.txt")
        if probe.exists():
            probe.unlink()
        with self.assertRaises(inst.FailClosed):
            inst._write(probe, "must never be written")
        self.assertFalse(probe.exists())


class BlockersRecordTests(unittest.TestCase):
    """The unresolved methodology issues must stay prominently recorded."""

    def test_blockers_file_records_required_issues(self):
        text = " ".join((HERE / "BLOCKERS.md").read_text(
            encoding="utf-8").split())  # prose is hard-wrapped
        for phrase in ("not comparable with current production scores",
                       "omits the rating rules entirely",
                       "probability-of-outing contradiction",
                       "interval-scale assumption",
                       "Bagmati provenance",
                       "Blind identity leaks",
                       "Absent substantive fact-verification",
                       "cannot and does not validate truth"):
            self.assertIn(phrase, text, f"missing blocker: {phrase}")

    def test_correction_note_present_and_prose(self):
        text = " ".join((HERE / "pilot2-correction-note.md").read_text(
            "utf-8").split())  # prose is hard-wrapped
        for phrase in ("second-listed", "pilot2-analysis.json",
                       "confounded with run time", "stable everywhere"):
            self.assertIn(phrase, text, f"missing: {phrase}")
        self.assertNotIn("regex", text)  # ordinary prose, hand-written


if __name__ == "__main__":
    unittest.main(verbosity=2)
