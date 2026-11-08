#!/usr/bin/env python3
"""Freeze/retirement tests (2026-11-13): the disallowed scoring paths must be
gone, while every existing score stays a preserved historical input.

Covers:
  A. tools/build_data.py is a score-preserving validation/rank/meta builder
     (sandbox full-dataset builds; no score ever written; legacy override /
     reaggregate / route-3 / territory-mirror behaviours no longer occur;
     no country-specific score literals in code).
  B. tools/anchored_calibrate.py is DELETED (2026-11-08, per user order): the
     retired foreign-reference lane and its fixed reference constants must not
     exist anywhere in tools/ or be importable; build_manifest must not load
     them.
  C. tools/settle_scores.py refuses --rebalance and --run (incl. force) with
     nonzero before any mutation or provider call; read-only --plan still
     works.
  D. tools/consolidate_record.py validates summaries against the SHARED
     build_data.MAX_SUMMARY_CHARS ceiling (source + behaviour parity on the
     current USA dossier and on at-/over-limit text), imported under
     a controlled env so no credential file is opened and no API call runs.

All builds run in temporary sandbox copies of data/ + boundaries/; this
suite never writes into data/ or any repo file. No score output is applied
anywhere.

Run: python3 tools/test_freeze_paths.py
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import build_data  # noqa: E402

ROUTE3_TMPL = ("No sub-national signal was identified; the national assessment "
               "applies here")
TEXT_FIELDS = ("summary", "tangentialFactors", "localsOnly", "outOfScopeNotes",
               "blindSummary", "blindTangential", "blindLocalsOnly",
               "blindOutOfScope", "sources")
# numeric literals in build_data.py that are legitimate scale/flag constants,
# not country-specific scores
LITERAL_WHITELIST = {0.0, 1.0, 0.0201}


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_sandbox() -> Path:
    sb = Path(tempfile.mkdtemp(prefix="freeze_sb_"))
    (sb / "data").mkdir()
    (sb / "boundaries").mkdir()
    for f in ("countries.json", "admin1.json"):
        shutil.copy2(ROOT / "data" / f, sb / "data" / f)
    for f in ("countries.geojson", "admin1.geojson"):
        shutil.copy2(ROOT / "boundaries" / f, sb / "boundaries" / f)
    return sb


def run_build(sb: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOLS / "build_data.py")],
                          cwd=sb, capture_output=True, text=True, timeout=300)


def load(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def set_score(rec, value):
    """Change a record's score keeping band validation consistent."""
    rec["score"] = round(value, 6)
    rec["band"] = build_data.band_label(rec["score"])


class SandboxFullBuild(unittest.TestCase):
    """One full-dataset build in a sandbox; then preservation assertions."""

    @classmethod
    def setUpClass(cls):
        cls.sb = make_sandbox()
        cls.in_c = load(ROOT / "data" / "countries.json")
        cls.in_a = load(ROOT / "data" / "admin1.json")
        cls.proc = run_build(cls.sb)
        cls.out_c = load(cls.sb / "data" / "countries.json")
        cls.out_a = load(cls.sb / "data" / "admin1.json")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.sb, ignore_errors=True)

    def test_0_build_succeeds_with_no_validation_errors(self):
        # 2026-11-13 follow-up: the shared summary ceiling is now 16000, so
        # the current USA dossier validates and the sandbox build
        # must be fully green — this test expects SUCCESS, not a known
        # failure, and will keep passing only while no new validation error
        # appears.
        errors = [l for l in self.proc.stdout.splitlines()
                  if l.startswith("ERROR:")]
        self.assertEqual(errors, [])
        self.assertEqual(self.proc.returncode, 0,
                         self.proc.stdout + self.proc.stderr)

    def test_7_actual_usa_summary_accepted(self):
        import apply_rework
        usa = self.in_c["USA"]["summary"]
        self.assertTrue(build_data.valid_summary(usa), "USA summary rejected")
        self.assertTrue(apply_rework.valid_summary(usa))
        self.assertEqual(apply_rework.MAX_SUMMARY_CHARS,
                         build_data.MAX_SUMMARY_CHARS)
        self.assertGreaterEqual(build_data.MAX_SUMMARY_CHARS, 12000)

    def test_8_summary_length_ceiling_still_rejects_over_limit(self):
        import apply_rework
        at_limit = "<p>" + "a" * (build_data.MAX_SUMMARY_CHARS - 7) + "</p>"
        self.assertEqual(len(at_limit), 16000)
        self.assertTrue(build_data.valid_summary(at_limit))
        self.assertTrue(apply_rework.valid_summary(at_limit))
        over = "<p>" + "a" * (build_data.MAX_SUMMARY_CHARS - 6) + "</p>"
        self.assertEqual(len(over), 16001)
        self.assertFalse(build_data.valid_summary(over))
        self.assertFalse(apply_rework.valid_summary(over))

    def test_1_every_country_score_preserved(self):
        self.assertEqual(set(self.in_c), set(self.out_c))
        for iso in self.in_c:
            self.assertEqual(self.in_c[iso]["score"], self.out_c[iso]["score"],
                             f"country score changed: {iso}")

    def test_2_every_admin1_score_preserved(self):
        self.assertEqual(set(self.in_a), set(self.out_a))
        for sid in self.in_a:
            self.assertEqual(self.in_a[sid]["score"], self.out_a[sid]["score"],
                             f"division score changed: {sid}")

    def test_3_historical_provenance_preserved_verbatim(self):
        for iso, r in self.in_c.items():
            o = self.out_c[iso]
            for fld in ("scoreProvenance", "provisionalCalibration",
                        "derivedFrom", "nationalFrameworkScore", "band",
                        "rubricVersion", "ratedAt", "ratedBy"):
                self.assertEqual(r.get(fld, "\u00absent"),
                                 o.get(fld, "\u00absent"),
                                 f"{iso}.{fld} not preserved")
        for sid, r in self.in_a.items():
            o = self.out_a[sid]
            for fld in ("derivedFrom", "band", "ratedAt", "ratedBy",
                        "estimated", "inherited"):
                self.assertEqual(r.get(fld, "\u00absent"),
                                 o.get(fld, "\u00absent"),
                                 f"{sid}.{fld} not preserved")

    def test_4_local_summaries_and_sources_preserved(self):
        for sid, r in self.in_a.items():
            for fld in TEXT_FIELDS:
                self.assertEqual(r.get(fld, "\u00absent"),
                                 self.out_a[sid].get(fld, "\u00absent"),
                                 f"{sid}.{fld} not preserved")
        for iso, r in self.in_c.items():
            for fld in ("summary", "sources", "blindSummary"):
                self.assertEqual(r.get(fld, "\u00absent"),
                                 self.out_c[iso].get(fld, "\u00absent"),
                                 f"{iso}.{fld} not preserved")

    def test_5_admin1_records_byte_identical_and_country_diffs_rank_only(self):
        # admin1 round-trips exactly; for countries the ONLY field any build
        # may recompute is `rank` (stored ranks are stale for 14 countries at
        # HEAD - a pre-existing staleness, refreshed by old AND new builds).
        self.assertEqual(self.in_a, self.out_a)
        changed = {}
        for iso in self.in_c:
            diff = [f for f in self.in_c[iso]
                    if self.in_c[iso].get(f) != self.out_c[iso].get(f)]
            if diff:
                changed[iso] = diff
        self.assertTrue(set(changed) <= set(self.in_c))
        for iso, fields in changed.items():
            self.assertEqual(set(fields), {"rank"},
                             f"{iso} changed non-rank fields: {fields}")

    def test_6_usa_historical_value_not_replaced(self):
        # DO NOT replace USA 0.330 with 0.264 or anything else: USA must come
        # through byte-identical (score, band, provisionalCalibration block).
        usa_in, usa_out = self.in_c["USA"], self.out_c["USA"]
        self.assertEqual(usa_in["score"], usa_out["score"])
        self.assertEqual(usa_in.get("provisionalCalibration"),
                         usa_out.get("provisionalCalibration"))
        self.assertNotEqual(usa_out["score"],
                            usa_out.get("nationalFrameworkScore"))
        # nothing was asserted "correct": build output carries no new
        # provenance text at all
        self.assertEqual(usa_in["scoreProvenance"], usa_out["scoreProvenance"])


class LegacyBehaviourRemoved(unittest.TestCase):
    """Each test reproduces what the OLD branch did and proves it no longer
    happens. Every case runs its own sandbox build."""

    def _build_with(self, mutate) -> tuple:
        sb = make_sandbox()
        try:
            c = load(sb / "data" / "countries.json")
            a = load(sb / "data" / "admin1.json")
            pre = mutate(c, a)
            (sb / "data" / "countries.json").write_text(
                json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
            (sb / "data" / "admin1.json").write_text(
                json.dumps(a, ensure_ascii=False, indent=1), encoding="utf-8")
            proc = run_build(sb)
            return pre, load(sb / "data" / "countries.json"), \
                load(sb / "data" / "admin1.json"), proc
        finally:
            shutil.rmtree(sb, ignore_errors=True)

    def test_a_provisional_override_no_longer_forces_a_country_score(self):
        # LEGACY: PROVISIONAL_CALIBRATION forced the stored consensus value
        # over whatever value was in the file. New: input value preserved.
        in_c = load(ROOT / "data" / "countries.json")
        pc_iso = next(iso for iso, r in in_c.items()
                      if r.get("provisionalCalibration"))
        pc_value = in_c[pc_iso]["provisionalCalibration"]["value"]

        def mutate(c, a):
            set_score(c[pc_iso], 0.77)  # a different in-band input value
            return pc_value

        forced_legacy, out_c, _, proc = self._build_with(mutate)
        self.assertEqual(out_c[pc_iso]["score"], 0.77,
                         "build rewrote a country score (old override path?)")
        self.assertNotEqual(out_c[pc_iso]["score"], forced_legacy)

    def test_b_reaggregate_no_longer_derives_country_from_divisions(self):
        # LEGACY: for >=3 measured divisions the country score was recomputed
        # as the division mean (or forced to nationalFrameworkScore). New:
        # change a division, country stays put.
        in_c = load(ROOT / "data" / "countries.json")
        in_a = load(ROOT / "data" / "admin1.json")
        from collections import defaultdict
        per = defaultdict(list)
        for sid, r in in_a.items():
            if not r.get("inherited") and isinstance(r.get("score"), (int, float)):
                per[r.get("parentIso3") or r["iso3"]].append(sid)
        cand = [iso for iso, sids in per.items()
                if len(sids) >= 3 and iso in in_c
                and (in_c[iso].get("derivedFrom") or {}).get("mode") == "reaggregate"]
        self.assertTrue(cand, "need a reaggregate country with >=3 divisions")
        iso = cand[0]
        sid = per[iso][0]
        orig_country = in_c[iso]["score"]

        def mutate(c, a):
            set_score(a[sid], min(0.98, float(a[sid]["score"]) + 0.05))
            return iso

        _, out_c, out_a, _ = self._build_with(mutate)
        self.assertEqual(out_a[sid]["score"],
                         round(min(0.98, float(in_a[sid]["score"]) + 0.05), 6),
                         "division write lost")
        self.assertEqual(out_c[iso]["score"], orig_country,
                         "country score was re-aggregated from divisions")
        self.assertEqual((out_c[iso].get("derivedFrom") or {}),
                         (in_c[iso].get("derivedFrom") or {}),
                         "derivedFrom rewritten (old reaggregate path?)")

    def test_c_route3_template_no_longer_copied_from_parent(self):
        # LEGACY: estimated regions carrying the no-signal template had their
        # score forced to the parent's national score on every build. New:
        # thin local scores are never auto-replaced by the national score.
        in_c = load(ROOT / "data" / "countries.json")
        in_a = load(ROOT / "data" / "admin1.json")
        kid = next(sid for sid, r in in_a.items()
                   if r.get("estimated") and ROUTE3_TMPL in str(r.get("summary", "")))
        parent_iso = in_a[kid].get("parentIso3") or in_a[kid]["iso3"]
        orig_local = in_a[kid]["score"]

        def mutate(c, a):
            set_score(c[parent_iso], min(0.98, float(c[parent_iso]["score"]) + 0.03))
            return parent_iso

        _, out_c, out_a, _ = self._build_with(mutate)
        self.assertEqual(out_c[parent_iso]["score"],
                         round(min(0.98, float(in_c[parent_iso]["score"]) + 0.03), 6),
                         "country write lost")
        self.assertEqual(out_a[kid]["score"], orig_local,
                         "thin local score was overwritten from the parent "
                         "(route-3 auto-copy still active)")

    def test_d_territory_mirror_no_longer_copies_division_into_country(self):
        # LEGACY: a single-division territory's admin1 row overwrote the
        # country record's score AND text. New: neither the score nor ANY
        # text of either side is touched (score AND text asserted below).
        in_c = load(ROOT / "data" / "countries.json")
        in_a = load(ROOT / "data" / "admin1.json")
        from collections import defaultdict
        per = defaultdict(list)
        for sid, r in in_a.items():
            per[r["iso3"]].append(sid)
        cand = [iso for iso, sids in per.items()
                if len(sids) == 1 and iso in in_c
                and in_a[sids[0]].get("parentIso3")]
        self.assertTrue(cand, "need a single-division territory")
        iso = cand[0]
        sid = per[iso][0]
        orig_country = in_c[iso]["score"]
        child_summary_probe = "<p>territory child text probe</p>"
        child_blind_probe = "<p>territory child blind probe</p>"

        def mutate(c, a):
            set_score(a[sid], min(0.98, float(a[sid]["score"]) + 0.06))
            # child TEXT too: legacy mirrored child text into the country
            a[sid]["summary"] = child_summary_probe
            a[sid]["blindSummary"] = child_blind_probe
            return iso

        _, out_c, out_a, _ = self._build_with(mutate)
        self.assertEqual(out_c[iso]["score"], orig_country,
                         "territory division score was copied into the country")
        for fld in TEXT_FIELDS:
            self.assertEqual(out_c[iso].get(fld, "\u00absent"),
                             in_c[iso].get(fld, "\u00absent"),
                             f"territory child text was copied into country.{fld}")
        self.assertEqual(out_a[sid]["summary"], child_summary_probe)
        self.assertEqual(out_a[sid]["blindSummary"], child_blind_probe)
        for fld in TEXT_FIELDS:
            if fld in ("summary", "blindSummary"):
                continue
            self.assertEqual(out_a[sid].get(fld, "\u00absent"),
                             in_a[sid].get(fld, "\u00absent"),
                             f"parent text was copied into child.{fld}")

    def test_e_no_country_specific_score_literals_in_build_data(self):
        src = (TOOLS / "build_data.py").read_text(encoding="utf-8")
        # constants removed outright (comments explaining the removal are ok)
        self.assertNotIn("PROVISIONAL_CALIBRATION = {", src)
        self.assertNotIn("ROLLOUT_SUBSET = {", src)
        # (detect_repo_url's `subprocess.run(["git", ...])` is legitimate
        #  read-only metadata, not scoring — not checked here.)
        # no numeric literal equals any stored actual score
        tree = ast.parse(src)
        in_c = load(ROOT / "data" / "countries.json")
        in_a = load(ROOT / "data" / "admin1.json")
        scores = {float(r["score"]) for r in list(in_c.values()) + list(in_a.values())
                  if isinstance(r.get("score"), (int, float))}
        literals = {n.value for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, float)}
        forbidden = (scores & literals) - LITERAL_WHITELIST
        self.assertFalse(forbidden, f"score literals in code: {forbidden}")
        # no string constant smuggles a country score
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                for bad in ("0.330", "0.264", "0.443529", "0.559643"):
                    self.assertNotIn(bad, n.value,
                                     f"score literal {bad} in string constant")


    def test_f_score_precision_beyond_6dp_preserved(self):
        # LEGACY: main() normalised every country score with round(x, 6)
        # before validation, silently rewriting >6-dp input. New: the exact
        # stored value must survive the build untouched.
        in_c = load(ROOT / "data" / "countries.json")
        target = None
        for iso, r in sorted(in_c.items()):
            orig = float(r["score"])
            nudged = round(orig + 1e-8, 9)
            if nudged > 1.0:
                continue
            if build_data.band_label(nudged) == r.get("band"):
                target = (iso, nudged)
                break
        self.assertIsNotNone(target, "no in-band nudge candidate")
        iso, nudged = target
        self.assertGreater(len(str(nudged).split(".")[-1]), 6,
                           "test value must exceed 6 decimal places")

        def mutate(c, a):
            c[iso]["score"] = nudged   # NO set_score: keep full precision
            return iso

        _, out_c, _, proc = self._build_with(mutate)
        errors = [l for l in proc.stdout.splitlines() if l.startswith("ERROR:")]
        self.assertEqual(errors, [])
        self.assertEqual(out_c[iso]["score"], nudged,
                         "score precision beyond 6dp was normalised away")

    def test_g_single_unit_standin_child_not_synced_from_parent(self):
        # LEGACY: for a one-division country the child score AND text were
        # overwritten from the country record every build, and the child was
        # flagged inherited=True. New: changing the parent changes neither
        # the child's score, nor its text, nor its flags.
        in_c = load(ROOT / "data" / "countries.json")
        in_a = load(ROOT / "data" / "admin1.json")
        from collections import defaultdict
        per = defaultdict(list)
        for sid, r in in_a.items():
            per[r["iso3"]].append(sid)
        parent_iso = None
        keep = deletes = None
        for iso in sorted(per):
            if iso not in in_c or len(per[iso]) < 2:
                continue
            elig = sorted(s for s in per[iso]
                          if not in_a[s].get("dossier")
                          and not in_a[s].get("parentIso3"))
            if elig:
                parent_iso = iso
                keep = elig[0]
                deletes = [s for s in per[iso] if s != keep]
                break
        self.assertIsNotNone(parent_iso, "need a multi-division country with "
                             "a non-dossier, non-territory child")
        child_before = {f: in_a[keep].get(f, "\u00absent")
                        for f in ("score", "band", "summary", "blindSummary",
                                  "inherited")}
        parent_blind_probe = "<p>parent blind probe</p>"

        def mutate(c, a):
            # synthesise the legacy single-unit precondition: exactly one child
            for s in deletes:
                del a[s]
            child = a[keep]
            child.pop("dossier", None)
            child.pop("parentIso3", None)
            set_score(c[parent_iso], float(c[parent_iso]["score"]) + 0.01)
            c[parent_iso]["blindSummary"] = parent_blind_probe
            return parent_iso

        _, out_c, out_a, proc = self._build_with(mutate)
        errors = [l for l in proc.stdout.splitlines() if l.startswith("ERROR:")]
        self.assertEqual(errors, [])
        child_after = out_a[keep]
        for f, v in child_before.items():
            self.assertEqual(child_after.get(f, "\u00absent"), v,
                             f"stand-in child.{f} overwritten from parent "
                             "(single-unit sync still active?)")
        if child_before.get("inherited") is not True:
            # legacy sync force-flagged inherited=True on every build
            self.assertNotEqual(child_after.get("inherited"), True,
                                "child was force-flagged inherited")
        # parent kept its own mutated values (country not clobbered either)
        self.assertEqual(out_c[parent_iso]["score"],
                         round(in_c[parent_iso]["score"] + 0.01, 6))
        self.assertEqual(out_c[parent_iso]["blindSummary"], parent_blind_probe)


class RetiredCLIs(unittest.TestCase):
    """B: anchored calibration and C: settlement mutations refuse before any
    network call or data write; data hashes must not move."""

    @classmethod
    def setUpClass(cls):
        cls.h_before = {p: sha(ROOT / "data" / p)
                        for p in ("countries.json", "admin1.json")}

    @classmethod
    def tearDownClass(cls):
        after = {p: sha(ROOT / "data" / p)
                 for p in ("countries.json", "admin1.json")}
        if cls.h_before != after:
            raise AssertionError(
                f"data files changed during retired-CLI tests: "
                f"{cls.h_before} -> {after}")

    def _run(self, *argv):
        return subprocess.run([sys.executable, *argv], capture_output=True,
                              text=True, timeout=120)

    def test_anchored_lane_and_constants_deleted(self):
        # 2026-11-08, per user order: the retired anchor lane and its fixed
        # reference constants are deleted, not merely retired.
        self.assertFalse((TOOLS / "anchored_calibrate.py").exists(),
                         "anchored_calibrate.py must be deleted")
        for py in sorted(TOOLS.glob("*.py")):
            if py.name == "test_freeze_paths.py":
                continue  # this file names the deleted symbols in its assertions
            src = py.read_text(encoding="utf-8")
            self.assertNotIn("ANCHOR_CALIBRATION", src,
                             f"anchor constants referenced in {py.name}")
            self.assertNotIn("FROZEN_ANCHOR_SCORES", src,
                             f"anchor constants referenced in {py.name}")
            self.assertNotIn("anchored_calibrate", src,
                             f"deleted module referenced in {py.name}")

    def test_freeze_suite_wired_into_ci_before_build(self):
        # P1-1: the enforcement suite must run in CI BEFORE the build step.
        wf = (ROOT / ".github" / "workflows" /
              "validate.yml").read_text(encoding="utf-8")
        self.assertIn("tools/test_freeze_paths.py", wf)
        self.assertLess(wf.index("tools/test_freeze_paths.py"),
                        wf.index("tools/build_data.py"))

    def test_settle_mutations_refuse_nonzero(self):
        for argv in (["--rebalance"], ["--run"],
                     ["--run", "--force-legacy-invariant"],
                     ["--rebalance", "--run", "--force-legacy-invariant"]):
            p = self._run(str(TOOLS / "settle_scores.py"), *argv)
            self.assertEqual(p.returncode, 2,
                             f"settle did not refuse: {argv}")
            self.assertIn("RETIRED", p.stderr)
            if "--force-legacy-invariant" in argv:
                self.assertIn("re-enables NOTHING", p.stderr)

    def test_settle_refuses_in_process_with_network_poisoned(self):
        import settle_scores

        def no_net(*_a, **_k):
            raise AssertionError("provider attempted by retired settlement")

        with mock.patch("socket.socket", no_net), \
                mock.patch("socket.create_connection", no_net), \
                mock.patch("socket.getaddrinfo", no_net), \
                mock.patch.object(sys, "argv",
                                  ["settle_scores.py", "--run",
                                   "--force-legacy-invariant"]):
            self.assertEqual(settle_scores.main(), 2)

    def test_settle_plan_remains_readonly_and_zero(self):
        empty_logs = Path(tempfile.mkdtemp(prefix="freeze_logs_")) / "empty.jsonl"
        empty_logs.write_text("", encoding="utf-8")
        try:
            p = self._run(str(TOOLS / "settle_scores.py"), "--plan",
                          "--logs", str(empty_logs))
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("settlement queue", p.stdout)
        finally:
            shutil.rmtree(empty_logs.parent, ignore_errors=True)

    def test_settle_source_has_no_mutation_writers_left(self):
        src = (TOOLS / "settle_scores.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess.run", src)
        self.assertNotIn("write_text", src)   # no data writes anywhere
        self.assertNotIn('rec["score"] =', src)  # no score assignment left


class SharedSummaryCeilingAcrossLanes(unittest.TestCase):
    """D: the consolidation lane's summary gate must be the shared
    build_data.MAX_SUMMARY_CHARS ceiling used by build_data and apply_rework
    — no lane-local hardcoded limit that silently rejects valid dossiers.
    The lane module reads the provider key at import time, so the controlled
    env below keeps that import credential-free and network-free."""

    DUMMY_KEY = "unit-test-dummy-key-not-real"

    def setUp(self):
        self.src = (TOOLS / "consolidate_record.py").read_text(encoding="utf-8")

    def test_d1_source_shares_the_constant_and_keeps_no_hardcoded_ceiling(self):
        tree = ast.parse(self.src)
        literals = {n.value for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, int)}
        self.assertNotIn(8000, literals,
                         "stale 8000 ceiling literal in consolidate_record")
        imports = {(n.module, a.name) for n in ast.walk(tree)
                   if isinstance(n, ast.ImportFrom) for a in n.names}
        self.assertIn(("build_data", "MAX_SUMMARY_CHARS"), imports,
                      "shared ceiling not imported from build_data")
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == "valid_summary")
        names = {x.id for x in ast.walk(fn) if isinstance(x, ast.Name)}
        self.assertIn("MAX_SUMMARY_CHARS", names,
                      "valid_summary does not test against the shared name")
        # obsolete ceiling description replaced by the current shared one
        self.assertNotIn("(8000/12)", self.src)
        self.assertIn("MAX_SUMMARY_CHARS = 16000", self.src)

    def test_d2_three_lanes_agree_on_8792_and_boundary_text(self):
        import apply_rework
        sys.modules.pop("consolidate_record", None)
        key_file = Path("/tmp/.openrouter_key")
        real_read_text = Path.read_text

        def guarded_read_text(p, *args, **kwargs):
            if Path(p) == key_file:
                raise AssertionError("test opened the real API key file")
            return real_read_text(p, *args, **kwargs)

        def no_net(*_a, **_k):
            raise AssertionError("network attempted by consolidate_record import")

        with mock.patch.dict(os.environ, {"OPENROUTER_KEY": self.DUMMY_KEY}), \
                mock.patch.object(Path, "read_text", guarded_read_text), \
                mock.patch("socket.create_connection", no_net), \
                mock.patch("socket.getaddrinfo", no_net):
            import consolidate_record

        self.assertEqual(consolidate_record.KEY, self.DUMMY_KEY,
                         "controlled env not used: module saw another key")
        self.assertEqual(consolidate_record.MAX_SUMMARY_CHARS, 16000)
        self.assertEqual(consolidate_record.MAX_SUMMARY_CHARS,
                         build_data.MAX_SUMMARY_CHARS)
        self.assertEqual(consolidate_record.MAX_SUMMARY_CHARS,
                         apply_rework.MAX_SUMMARY_CHARS)

        lanes = (build_data.valid_summary, apply_rework.valid_summary,
                 consolidate_record.valid_summary)
        usa = load(ROOT / "data" / "countries.json")["USA"]["summary"]
        long_fixture = "<p>" + "a" * (8792 - 7) + "</p>"
        self.assertEqual(len(long_fixture), 8792)
        at_limit = "<p>" + "a" * (build_data.MAX_SUMMARY_CHARS - 7) + "</p>"
        over = "<p>" + "a" * (build_data.MAX_SUMMARY_CHARS - 6) + "</p>"
        self.assertEqual(len(at_limit), 16000)
        self.assertEqual(len(over), 16001)
        for lane in lanes:
            self.assertTrue(lane(usa), f"{lane.__module__}.valid_summary "
                                       f"rejected the USA summary")
            self.assertTrue(lane(long_fixture), f"{lane.__module__}: "
                                               f"8792-character fixture rejected")
            self.assertTrue(lane(at_limit), f"{lane.__module__}: at-limit "
                                            f"16000 rejected")
            self.assertFalse(lane(over), f"{lane.__module__}: over-limit "
                                         f"16001 accepted")
            self.assertFalse(lane(""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
