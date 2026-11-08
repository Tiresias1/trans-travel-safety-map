#!/usr/bin/env python3
"""Offline tests for the five-way harness. No network, no credentials, no
provider calls. All fixture writes go to temporary directories; nothing under
data/ or the repository is written, and the harness's own frozen/ and runs/
directories are only exercised through monkeypatched temp paths.

Run:  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_harness
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402
import blind_pairwise as BP  # noqa: E402  (harness already put tools/ on sys.path)

# Fixture ISO3 -> score (14 records incl. one territory PRI and parent XXX).
COUNTRY_SCORES = {
    "XXX": "0.02", "AAA": "0.05", "BBB": "0.10", "CCC": "0.15",
    "DDD": "0.20", "EEE": "0.25", "FFF": "0.30", "PRI": "0.40",
    "USA": "0.4217", "GGG": "0.55", "HHH": "0.65", "III": "0.75",
    "JJJ": "0.85", "KKK": "0.95",
}
PARENT_ISO = "XXX"
PARENT_SCORE_SENTINEL = "0.7771"


def country_record(iso3: str, score: str) -> dict:
    return {
        "name": f"Country-{iso3}",
        "score": score,
        "band": "High Risk",
        "rank": 7,
        "summary": f"PLAIN SUMMARY {iso3}",
        "comparisons": f"COMPARISON SENTINEL {iso3}",
        "sources": [{"url": f"https://invalid.example/{iso3}", "summary": "s"}],
        "blindSummary": f"BLIND SUMMARY {iso3}",
        "blindSourceSummaries": [f"{iso3} SRC {k}" for k in range(1, 11)],
        "blindTangential": f"BLIND TANGENTIAL {iso3}",
        "blindLocalsOnly": f"BLIND LOCALS {iso3}",
        "blindOutOfScope": f"BLIND OOS {iso3}",
        "outOfScopeNotes": "claims unresolved",
        "nationalFrameworkScore": PARENT_SCORE_SENTINEL,
        "rubricVersion": "r2026-11-13",
    }


def parent_country_record() -> dict:
    rec = country_record(PARENT_ISO, PARENT_SCORE_SENTINEL)
    rec["name"] = "Parentland"
    rec["summary"] = "PARENT PLAIN SUMMARY"
    rec["comparisons"] = "PARENT COMPARISON"
    rec["blindSummary"] = "PARENT BLIND SUMMARY"
    rec["blindTangential"] = "PARENT TANGENTIAL"
    rec["blindLocalsOnly"] = "PARENT LOCALS"
    rec["blindOutOfScope"] = "PARENT OOS"
    rec["blindSourceSummaries"] = [f"PSRC {k}" for k in range(1, 11)]
    return rec


def division_record(rid: str, idx: int, estimated: bool = False) -> dict:
    return {
        "iso3": PARENT_ISO,
        "name": f"Region{idx}",
        "score": round(0.05 * idx, 2),
        "summary": f"PLAIN DIV SUMMARY {idx}",
        "modelContext": f"MODEL CONTEXT {idx}",
        "blindSummary": f"BLIND DIV SUMMARY {idx}",
        "blindSourceSummaries": [f"DSRC {idx}-1", f"DSRC {idx}-2"],
        "blindTangential": f"DIV TANGENTIAL {idx}",
        "blindLocalsOnly": f"DIV LOCALS {idx}",
        "blindOutOfScope": f"DIV OOS {idx}",
        "outOfScopeNotes": "not counted",
        "estimated": estimated,
        "rubricVersion": "r2026-11-13",
    }


def make_fixture_tree(base: Path, omit_diversity: tuple[str, ...] = ()) -> None:
    data = base / "data"
    data.mkdir(parents=True, exist_ok=True)
    countries = {iso: country_record(iso, score)
                 for iso, score in COUNTRY_SCORES.items()}
    countries[PARENT_ISO] = parent_country_record()
    (data / "countries.json").write_text(json.dumps(countries, indent=1),
                                         encoding="utf-8")
    admin1 = {f"XDIV{i}": division_record(f"XDIV{i}", i, estimated=(i == 7))
              for i in range(1, 8)}
    for i in range(1, 4):                      # a parent with too few divisions
        admin1[f"YDIV{i}"] = dict(division_record(f"YDIV{i}", i), iso3="YYY")
    (data / "admin1.json").write_text(json.dumps(admin1, indent=1), encoding="utf-8")
    research = base / "research"
    research.mkdir(exist_ok=True)
    (research / "outing-risk-taxonomy.md").write_text(
        "Fixture taxonomy reference text for five-way tests.\n", encoding="utf-8")
    diversity_dir = base / "frozen" / "diversity"
    diversity_dir.mkdir(parents=True, exist_ok=True)
    batch = {}
    for iso3 in COUNTRY_SCORES:
        if iso3 in omit_diversity or iso3 == "PRI":
            continue
        batch[iso3] = {"iso3": iso3,
                       "diversity": f"PLAIN DIVERSITY {iso3}",
                       "blindDiversity": f"DIVERSITY BLIND {iso3}",
                       "basis": "fixture"}
    (diversity_dir / "batch-0.json").write_text(json.dumps(batch, indent=1),
                                                encoding="utf-8")


def independent_percentiles(countries: dict) -> dict[str, float]:
    """Reference implementation: average-rank percentile, written separately
    from harness.percentile_ranks on purpose."""
    values = sorted(float(r["score"]) for r in countries.values())
    n = len(values)
    out = {}
    for iso3, rec in countries.items():
        s = float(rec["score"])
        less = sum(1 for v in values if v < s)
        equal = sum(1 for v in values if v == s)
        out[iso3] = 100.0 * (less + (equal - 1) / 2.0) / (n - 1)
    return out


def valid_response() -> str:
    return json.dumps({"results": [
        {"slot": s, "score": 0.1 * s, "why": f"why {s}"} for s in range(1, 6)]})


def _pre_runs_snapshot():
    out = {"accounting.lock": (HERE / "accounting.lock").exists()}
    runs = HERE / "runs"
    out["runs"] = (runs.exists(),
                   sorted(e.name for e in runs.iterdir()) if runs.exists() else ())
    return out


_PRE_RUNS_SNAPSHOT = _pre_runs_snapshot()


class FakeCaller:
    def __init__(self, results):
        self.results = list(results)
        self.count = 0

    def __call__(self, system_text, user_text):
        self.count += 1
        item = self.results[min(self.count - 1, len(self.results) - 1)]
        if isinstance(item, Exception):
            raise item
        return item


class FixtureCase(unittest.TestCase):
    """Patches every harness path onto one temporary fixture tree."""
    OMIT_DIVERSITY: tuple[str, ...] = ()

    def setUp(self):
        super().setUp()
        self.root = Path(tempfile.mkdtemp(prefix="five-way-test-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        make_fixture_tree(self.root, omit_diversity=self.OMIT_DIVERSITY)
        self._patch("COUNTRIES_PATH", self.root / "data" / "countries.json")
        self._patch("ADMIN1_PATH", self.root / "data" / "admin1.json")
        self._patch("TAXONOMY_PATH",
                    self.root / "research" / "outing-risk-taxonomy.md")
        self._patch("FROZEN_DIR", self.root / "frozen")
        self._patch("DIVERSITY_DIR", self.root / "frozen" / "diversity")
        self._patch("RUNS_DIR", self.root / "runs")
        self._patch("LOCK_PATH", self.root / "accounting.lock")

    def _patch(self, name, value):
        old = getattr(harness, name)
        setattr(harness, name, value)
        self.addCleanup(setattr, harness, name, old)

    def build_country(self, n_calls=8, seed=20261119, us_locked=True):
        return harness.make_country_schedule(n_calls, seed, us_locked=us_locked)

    def schedule_files(self):
        return sorted(p.name for p in (self.root / "frozen").glob("schedule_*.json"))


# --------------------------------------------------------------------------- #
# Production rubric reuse
# --------------------------------------------------------------------------- #

class PromptRubricTests(unittest.TestCase):
    def setUp(self):
        self.tax = Path(harness.TAXONOMY_PATH).read_text(encoding="utf-8")
        self.country = harness.build_country_system(self.tax)
        self.admin1 = harness.build_admin1_system(self.tax)

    def test_rating_rules_reused_verbatim(self):
        self.assertIs(harness.RATING_RULES, BP.RATING_RULES)
        self.assertEqual(harness.RUBRIC_VERSION, BP.RUBRIC_VERSION)
        self.assertIn(BP.RATING_RULES, self.country)
        self.assertIn(BP.RATING_RULES, self.admin1)

    def test_scale_blocks_are_production_substrings(self):
        prod_country = BP.build_system_prompt(self.tax)
        dummy = {"name": "?", "score": 0.0, "sources": []}
        prod_admin1 = BP.build_admin1_system_prompt(self.tax, dummy, "ZZZ", {})
        self.assertIn(harness._production_scale(self.tax, admin1=False), prod_country)
        self.assertIn(harness._production_scale(self.tax, admin1=True), prod_admin1)
        self.assertIn("## The scale", self.country)
        self.assertIn("## The scale", self.admin1)

    def test_diagnostic_env_hooks_refused(self):
        old = os.environ.get("STRIP_RULE_10B")
        os.environ["STRIP_RULE_10B"] = "1"
        try:
            with self.assertRaises(harness.HarnessError):
                harness.build_country_system(self.tax)
            with self.assertRaises(harness.HarnessError):
                harness.build_admin1_system(self.tax)
        finally:
            if old is None:
                os.environ.pop("STRIP_RULE_10B", None)
            else:
                os.environ["STRIP_RULE_10B"] = old

    def test_five_way_framing_and_mean_local_instruction(self):
        for text, needle in (
                (self.country, "anonymised research dossiers, numbered 1 to 5"),
                (self.country, "local regime in addition to the national picture"),
                (self.country, "SUBNATIONAL REGIMES paragraph"),
                (self.admin1, "anonymised dossiers, numbered 1 to 5"),
                (self.admin1, "Identities are withheld"),
                (self.admin1, "the division's rating should reflect the mean"),
                (self.admin1, "local regime in addition to the national picture")):
            self.assertIn(needle, text)
        # pairwise framing from production must be gone
        self.assertNotIn("labelled A and B", self.country)
        self.assertNotIn("labelled A and B", self.admin1)

    def test_output_format_lists_five_slots(self):
        for text in (self.country, self.admin1):
            self.assertIn('"results"', text)
            for slot in range(1, 6):
                self.assertIn(f'{{"slot": {slot},', text)
            self.assertIn("every slot appearing", text.replace("\n", " "))


# --------------------------------------------------------------------------- #
# Stratified drawing
# --------------------------------------------------------------------------- #

class PercentileAndDrawTests(unittest.TestCase):
    def test_percentiles_match_independent_reference(self):
        countries = {iso: country_record(iso, score)
                     for iso, score in COUNTRY_SCORES.items()}
        harness_got = harness.percentile_ranks(countries)
        want = independent_percentiles(countries)
        for iso3 in countries:
            self.assertAlmostEqual(harness_got[iso3], want[iso3], places=12)
        self.assertEqual(min(harness_got.values()), 0.0)
        self.assertEqual(max(harness_got.values()), 100.0)

    def test_draw_overlap_forces_distinct_countries(self):
        # Bands overlap; without exclusion a later band could redraw an
        # already-selected country. Crafted pools force one path.
        pcts = {"A": 25.0, "B": 40.0, "C": 55.0, "D": 75.0, "E": 90.0}
        rng = harness.random.Random(7)
        selection, slot_map = harness._draw_call(rng, sorted(pcts), pcts, False)
        self.assertEqual([e["iso3"] for e in selection], ["A", "B", "C", "D", "E"])
        self.assertEqual(len(set(slot_map[str(s)]["iso3"] for s in range(1, 6))), 5)
        self.assertEqual([e["band"] for e in selection], [list(b) for b in harness.BANDS])

    def test_draw_empty_band_fails_closed(self):
        pcts = {"A": 5.0, "B": 95.0}          # band [35,65] has nobody
        with self.assertRaises(harness.HarnessError):
            harness._draw_call(harness.random.Random(1), sorted(pcts), pcts, False)

    def test_us_locked_owns_first_containing_band(self):
        pcts = {"USA": 25.0, "B": 40.0, "C": 55.0, "D": 75.0, "E": 90.0,
                "F": 10.0}
        # 25.0 lies in BOTH [0,30] and [20,50]; the first band owns USA.
        rng = harness.random.Random(3)
        selection, slot_map = harness._draw_call(rng, sorted(pcts), pcts, True)
        self.assertEqual(selection[0], {"band": [0, 30], "iso3": "USA",
                                        "forced_usa": True})
        drawn = [e["iso3"] for e in selection]
        self.assertEqual(drawn.count("USA"), 1)
        self.assertEqual(len(set(drawn)), 5)   # distinct, USA once
        self.assertNotIn("USA", drawn[1:])
        self.assertTrue(set(drawn) <= {"USA", "A", "B", "C", "D", "E"})

    def test_us_locked_requires_usa_in_pool(self):
        pcts = {"A": 5.0, "B": 40.0, "C": 55.0, "D": 75.0, "E": 90.0}
        with self.assertRaises(harness.HarnessError):
            harness._draw_call(harness.random.Random(1), sorted(pcts), pcts, True)


# --------------------------------------------------------------------------- #
# Country schedule (fixture data)
# --------------------------------------------------------------------------- #

class CountryScheduleTests(FixtureCase):
    def test_strata_membership_and_no_overlap(self):
        doc = self.build_country(n_calls=10, seed=11)
        countries = harness.load_countries()
        pcts = independent_percentiles(countries)
        for call in doc["calls"]:
            sel = call["selection"]
            self.assertEqual([e["band"] for e in sel],
                             [list(b) for b in harness.BANDS])
            isos = [e["iso3"] for e in sel]
            self.assertEqual(len(set(isos)), 5, "no overlap within a call")
            for entry in sel:
                lo, hi = entry["band"]
                self.assertTrue(lo <= pcts[entry["iso3"]] <= hi,
                                f"{entry['iso3']} outside band {entry['band']}")
            # display slot map covers exactly the same five countries
            slots = {call["slot_map"][str(s)]["iso3"] for s in range(1, 6)}
            self.assertEqual(slots, set(isos))

    def test_us_locked_every_call(self):
        doc = self.build_country(n_calls=10, seed=11, us_locked=True)
        pcts = independent_percentiles(harness.load_countries())
        expected_band = harness.BANDS[harness.bands_containing(pcts["USA"])[0]]
        for call in doc["calls"]:
            sel = call["selection"]
            forced = [e for e in sel if e["forced_usa"]]
            self.assertEqual(len(forced), 1, "USA forced exactly once per call")
            self.assertEqual(forced[0]["iso3"], "USA")
            self.assertEqual(forced[0]["band"], list(expected_band))
            self.assertEqual(sel[harness.BANDS.index(tuple(expected_band))]["iso3"],
                             "USA")
            others = [e["iso3"] for e in sel if not e["forced_usa"]]
            self.assertNotIn("USA", others)
            self.assertEqual(len(set(others)), 4)

    def test_us_unlocked_builds_without_forcing(self):
        doc = self.build_country(n_calls=10, seed=13, us_locked=False)
        self.assertFalse(doc["us_locked"])
        for call in doc["calls"]:
            isos = [call["selection"][i]["iso3"] for i in range(5)]
            self.assertEqual(len(set(isos)), 5)
            self.assertFalse(any(e["forced_usa"] for e in call["selection"]))

    def test_seed_determinism_same_seed_identical(self):
        a = self.build_country(n_calls=8, seed=4242)
        b = self.build_country(n_calls=8, seed=4242)
        self.assertEqual(a, b)                 # includes all message hashes

    def test_different_seed_changes_draws(self):
        a = self.build_country(n_calls=8, seed=4242)
        b = self.build_country(n_calls=8, seed=4243)
        self.assertNotEqual([c["selection"] for c in a["calls"]],
                            [c["selection"] for c in b["calls"]])

    def test_territory_never_eligible_and_never_drawn(self):
        countries = harness.load_countries()
        self.assertIn("PRI", countries, "fixture territory present in data")
        eligible = harness.eligible_countries(countries)
        self.assertNotIn("PRI", eligible, "territories excluded from country mode")
        doc = self.build_country(n_calls=30, seed=99, us_locked=False)
        for call in doc["calls"]:
            self.assertNotIn("PRI", [e["iso3"] for e in call["selection"]])

    def test_schedule_gates_and_verify_cli_pass(self):
        doc = self.build_country(n_calls=4, seed=5)
        path = harness.country_schedule_path()
        got = harness.run_schedule_gates(path)
        self.assertEqual(got["seed"], doc["seed"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = harness.main(["verify", "--schedule", str(path)])
        self.assertEqual(code, 0)

    def test_tampered_message_hash_and_source_pin_refuse(self):
        self.build_country(n_calls=3, seed=5)
        path = harness.country_schedule_path()
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["calls"][0]["user_sha256"] = "0" * 64
        harness.write_json(path, doc)
        with self.assertRaisesRegex(harness.HarnessError, "hash mismatch"):
            harness.run_schedule_gates(path)
        # fresh (good) schedule, then tamper only the source pin
        doc = self.build_country(n_calls=3, seed=5)
        doc["sources"]["data/countries.json"] = "0" * 64
        harness.write_json(path, doc)
        with self.assertRaisesRegex(harness.HarnessError, "source drift"):
            harness.run_schedule_gates(path)


class MissingDiversityTests(FixtureCase):
    # every member of band [70,100] lacks its diversity paragraph, so the
    # first call is guaranteed to hit the fail-closed path deterministically
    OMIT_DIVERSITY = ("HHH", "III", "JJJ", "KKK")

    def test_missing_diversity_fails_closed_before_write(self):
        with self.assertRaisesRegex(harness.HarnessError,
                                    "frozen/diversity|blindDiversity"):
            self.build_country(n_calls=1, seed=1)
        self.assertEqual(self.schedule_files(), [], "nothing may be written")


# --------------------------------------------------------------------------- #
# ADM1 schedule and blinding (fixture data)
# --------------------------------------------------------------------------- #

class Admin1ScheduleTests(FixtureCase):
    def test_admin1_schedule_gates_pass(self):
        doc = harness.make_admin1_schedule(PARENT_ISO, 4, 77)
        path = harness.admin1_schedule_path(PARENT_ISO)
        self.assertTrue(path.is_file())
        harness.run_schedule_gates(path)
        for call in doc["calls"]:
            rids = [call["selection"][i] for i in range(5)]
            self.assertEqual(len(set(rids)), 5)
            self.assertTrue(all(r.startswith("XDIV") for r in rids))

    def test_admin1_messages_exclude_identities_scores_and_diversity(self):
        doc = harness.make_admin1_schedule(PARENT_ISO, 4, 77)
        system_text, users = zip(*harness.rebuild_messages(doc))
        everything = "\n".join(list(system_text) + list(users))
        # parent identity / score / unblinded text never appear
        for sentinel in ("Parentland", PARENT_SCORE_SENTINEL, "PARENT PLAIN SUMMARY",
                         "PARENT COMPARISON", "PARENT OOS", "DIVERSITY BLIND",
                         "PLAIN DIVERSITY"):
            self.assertNotIn(sentinel, everything)
        # division identities and unblinded fields never appear
        for i in range(1, 8):
            self.assertNotIn(f"Region{i}", everything)
            self.assertNotIn(f"PLAIN DIV SUMMARY {i}", everything)
            self.assertNotIn(f"MODEL CONTEXT {i}", everything)
        for user in users:
            # the parent framework is embedded in EACH of the five dossiers
            self.assertEqual(user.count("### PARENT NATIONAL FRAMEWORK"), 5)
            self.assertEqual(user.count("PARENT BLIND SUMMARY"), 5)
            self.assertEqual(user.count("PARENT TANGENTIAL"), 5)
            self.assertEqual(user.count("PARENT LOCALS"), 5)
            # parent sources capped at 8 per dossier: 5 dossiers x 8
            self.assertEqual(user.count("- PSRC "), 40)
            self.assertNotIn("PSRC 9", user)
            self.assertNotIn("PSRC 10", user)
            self.assertNotIn("PARENT OOS", user)
            # division blind evidence present per dossier
            self.assertEqual(user.count("### DIVISION EVIDENCE"), 5)
        # no scores anywhere, no pairwise framing
        self.assertNotIn("0.4217", everything)
        self.assertIn("Identities are withheld", system_text[0])

    def test_admin1_estimated_division_gets_data_status(self):
        admin1 = harness.load_admin1()
        text = harness.render_admin1_dossier("XDIV7", PARENT_ISO,
                                             admin1, harness.load_countries())
        self.assertIn("### DATA STATUS", text)
        text2 = harness.render_admin1_dossier("XDIV1", PARENT_ISO,
                                              admin1, harness.load_countries())
        self.assertNotIn("### DATA STATUS", text2)

    def test_admin1_seed_determinism(self):
        a = harness.make_admin1_schedule(PARENT_ISO, 4, 77)
        b = harness.make_admin1_schedule(PARENT_ISO, 4, 77)
        self.assertEqual(a, b)
        c = harness.make_admin1_schedule(PARENT_ISO, 4, 78)
        self.assertNotEqual([x["selection"] for x in a["calls"]],
                            [x["selection"] for x in c["calls"]])

    def test_too_few_divisions_fails(self):
        countries = harness.load_countries()
        countries["YYY"] = country_record("YYY", "0.5")
        harness.COUNTRIES_PATH.write_text(json.dumps(countries, indent=1),
                                          encoding="utf-8")
        with self.assertRaisesRegex(harness.HarnessError, "at least 5"):
            harness.make_admin1_schedule("YYY", 2, 1)

    def test_invalid_iso3_rejected(self):
        for bad in ("US", "USA!", "united", ""):
            with self.assertRaises(harness.HarnessError):
                harness.make_admin1_schedule(bad, 2, 1)


# --------------------------------------------------------------------------- #
# Country prompt blinding (fixture data)
# --------------------------------------------------------------------------- #

class CountryPromptBlindingTests(FixtureCase):
    def test_country_prompts_blind_with_diversity_paragraph(self):
        doc = self.build_country(n_calls=6, seed=21, us_locked=False)
        system_text, users = zip(*harness.rebuild_messages(doc))
        sys0 = system_text[0]
        self.assertNotIn("Country-", sys0)
        for iso3 in COUNTRY_SCORES:
            self.assertNotIn(f"Country-{iso3}", sys0)
        used = set()
        for call in doc["calls"]:
            used.update(e["iso3"] for e in call["selection"])
        for user in users:
            self.assertEqual(user.count("## DOSSIER"), 5)
            self.assertEqual(user.count("### SUBNATIONAL REGIMES"), 5)
        everything = "\n".join(list(system_text) + list(users))
        for iso3 in used:
            # blinded paragraph present, plain text absent, identity absent
            self.assertIn(f"DIVERSITY BLIND {iso3}", everything)
            self.assertNotIn(f"PLAIN DIVERSITY {iso3}", everything)
            self.assertNotIn(f"Country-{iso3}", everything)
            self.assertNotIn(f"PLAIN SUMMARY {iso3}", everything)
            self.assertNotIn(f"COMPARISON SENTINEL {iso3}", everything)
            self.assertNotIn(f"{iso3} SRC 10", sys0)  # only in user dossiers
        for user in users:
            self.assertNotIn("0.4217", user)          # no score leakage
            self.assertNotIn("Country-", user)

    def test_country_source_summaries_uncapped(self):
        doc = self.build_country(n_calls=1, seed=21, us_locked=False)
        _, users = zip(*harness.rebuild_messages(doc))
        # 10 sources per fixture country; the cap of 8 is ADM1-parent-only
        for entry in doc["calls"][0]["selection"]:
            iso3 = entry["iso3"]
            self.assertIn(f"- {iso3} SRC 10", users[0])
            self.assertEqual(users[0].count(f"- {iso3} SRC "), 10)

    def test_country_user_prompt_names_all_five_slots(self):
        doc = self.build_country(n_calls=1, seed=3)
        _, users = zip(*harness.rebuild_messages(doc))
        for slot in range(1, 6):
            self.assertIn(f"## DOSSIER {slot}\n", users[0])


# --------------------------------------------------------------------------- #
# Output contract
# --------------------------------------------------------------------------- #

class OutputContractTests(unittest.TestCase):
    def test_valid_response_parses_in_slot_order(self):
        raw = '  ' + valid_response() + '\n\n'
        entries = harness.parse_five_way_response(raw)
        self.assertEqual([e["slot"] for e in entries], [1, 2, 3, 4, 5])
        self.assertEqual(entries[0]["why"], "why 1")

    def test_invalid_responses_rejected(self):
        good = {"slot": 1, "score": 0.5, "why": "ok"}
        results5 = lambda *e: json.dumps({"results": [e[0]] * 5})  # noqa: E731
        cases = {
            "not json": "I think 0.4",
            "markdown fences": "```json\n" + valid_response() + "\n```",
            "top-level list": json.dumps([good] * 5),
            "missing results": json.dumps({"scores": [good] * 5}),
            "extra top key": json.dumps({"results": [good] * 5, "meta": 1}),
            "four entries": json.dumps({"results": [good] * 4}),
            "six entries": json.dumps({"results": [good] * 6}),
            "duplicate slots": results5(good),
            "slot zero": json.dumps({"results": [
                dict(good, slot=s if s < 5 else 0) for s in range(1, 6)]}),
            "slot out of range": json.dumps({"results": [
                dict(good, slot=s if s < 5 else 6) for s in range(1, 6)]}),
            "slot as string": json.dumps({"results": [
                dict(good, slot="1") for _ in range(5)]}),
            "score above one": json.dumps({"results": [
                dict(good, score=1.5) for _ in range(5)]}),
            "score below zero": json.dumps({"results": [
                dict(good, score=-0.01) for _ in range(5)]}),
            "score as string": json.dumps({"results": [
                dict(good, score="0.5") for _ in range(5)]}),
            "score as bool": json.dumps({"results": [
                dict(good, score=True) for _ in range(5)]}),
            "score NaN": '{"results": [{"slot": 1, "score": NaN, "why": "x"}]}',
            "missing why": json.dumps({"results": [
                {"slot": s, "score": 0.5} for s in range(1, 6)]}),
            "empty why": json.dumps({"results": [
                dict(good, why="   ") for _ in range(5)]}),
            "extra entry key": json.dumps({"results": [
                dict(good, evidence="x") for _ in range(5)]}),
            "entry not object": json.dumps({"results": ["x"] * 5}),
            "empty string": "",
            "None": None,
        }
        for label, raw in cases.items():
            with self.subTest(label):
                with self.assertRaises(harness.OutputRejected):
                    harness.parse_five_way_response(raw)


# --------------------------------------------------------------------------- #
# Accounting: exact Decimal, unknown charge, budget, the ONE shared lock
# --------------------------------------------------------------------------- #

class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="five-way-acc-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.lock = self.tmp / "accounting.lock"
        self.holder = harness.LOCK_HOLDER_PREFIX + "test"

    def test_classify_usage_exact(self):
        cost, tin, tout = harness.classify_usage(
            {"cost_usd": "0.000000001", "input_tokens": 10, "output_tokens": 5})
        self.assertEqual(cost, Decimal("0.000000001"))
        self.assertEqual((tin, tout), (10, 5))
        cost2, tin2, tout2 = harness.classify_usage({"cost_usd": 0.0005})
        self.assertEqual(cost2, Decimal("0.0005"))
        self.assertEqual((tin2, tout2), (None, None))

    def test_unknown_charge_paths(self):
        bad = {
            "usage missing": None,
            "usage not dict": "0.001",
            "cost missing": {"input_tokens": 1},
            "cost not decimal": {"cost_usd": "abc"},
            "cost negative": {"cost_usd": "-0.1"},
            "cost NaN": {"cost_usd": "NaN"},
            "cost bool": {"cost_usd": True},
            "cost object": {"cost_usd": {"usd": 1}},
            "tokens float": {"cost_usd": "0.1", "input_tokens": 1.5},
            "tokens negative": {"cost_usd": "0.1", "output_tokens": -3},
            "tokens bool": {"cost_usd": "0.1", "input_tokens": True},
        }
        for label, usage in bad.items():
            with self.subTest(label):
                with self.assertRaises(harness.UnknownCharge):
                    harness.classify_usage(usage)

    def test_ledger_exact_decimal_and_budget(self):
        harness.acquire_lock(self.lock, self.holder)
        try:
            ledger = harness.Ledger(self.tmp / "ledger.json", Decimal("0.01"))
            ledger.add_usage({"cost_usd": "0.000000001"}, 1)
            ledger.add_usage({"cost_usd": "0.000000002"}, 2)
            self.assertEqual(ledger.total, Decimal("0.000000003"))
            self.assertEqual(ledger.doc["total_usd"], "0.000000003")
            self.assertEqual(ledger.doc["input_tokens"], 0)
        finally:
            harness.release_lock(self.lock, self.holder)
        # reload persisted ledger
        harness.acquire_lock(self.lock, self.holder)
        try:
            again = harness.Ledger(self.tmp / "ledger.json", Decimal("0.01"))
            self.assertEqual(again.total, Decimal("0.000000003"))
            again.check_budget()
            with self.assertRaises(harness.BudgetExceeded):
                harness.Ledger(self.tmp / "ledger.json",
                               Decimal("0.000000001")).check_budget()
        finally:
            harness.release_lock(self.lock, self.holder)

    def test_unknown_charge_leaves_ledger_untouched(self):
        harness.acquire_lock(self.lock, self.holder)
        try:
            ledger = harness.Ledger(self.tmp / "ledger.json", Decimal("10"))
            with self.assertRaises(harness.UnknownCharge):
                ledger.add_usage({}, 1)
            self.assertFalse((self.tmp / "ledger.json").exists())
            self.assertEqual(ledger.total, Decimal("0"))
        finally:
            harness.release_lock(self.lock, self.holder)

    def test_lock_contention_refuses_and_foreign_lock_untouched(self):
        foreign = json.dumps({"holder": "someone-else", "pid": 12345}) + "\n"
        self.lock.write_text(foreign, encoding="utf-8")
        with self.assertRaises(harness.LockHeld):
            harness.acquire_lock(self.lock, self.holder)
        self.assertEqual(self.lock.read_text(encoding="utf-8"), foreign)
        harness.release_lock(self.lock, self.holder)   # never deletes foreign
        self.assertTrue(self.lock.exists())

    def test_lock_release_only_own_holder(self):
        harness.acquire_lock(self.lock, self.holder)
        harness.release_lock(self.lock, "other-holder")
        self.assertTrue(self.lock.exists())
        harness.release_lock(self.lock, self.holder)
        self.assertFalse(self.lock.exists())


# --------------------------------------------------------------------------- #
# Runner: gates, stops, raw-response preservation (injected caller only)
# --------------------------------------------------------------------------- #

class ExecuteTests(FixtureCase):
    def setUp(self):
        super().setUp()
        self.build_country(n_calls=3, seed=9)
        self.schedule = harness.country_schedule_path()
        self.runs = self.root / "runs"
        self.lock = self.root / "execute.lock"

    def execute(self, caller, **kw):
        return harness.execute_schedule(self.schedule, kw.pop("run_id", "r1"), caller,
                                        runs_dir=self.runs, lock_path=self.lock,
                                        **kw)

    def test_execute_happy_path_preserves_raw(self):
        self.build_country(n_calls=2, seed=9)     # exactly two calls to dispatch
        raw1 = '  ' + valid_response() + "\n\n"
        raw2 = valid_response()
        caller = FakeCaller([
            {"raw_response": raw1,
             "usage": {"cost_usd": "0.001", "input_tokens": 12, "output_tokens": 7}},
            {"raw_response": raw2,
             "usage": {"cost_usd": "0.0005", "input_tokens": 11, "output_tokens": 6}},
        ])
        summary = self.execute(caller, max_usd=Decimal("10"))
        self.assertEqual(summary["calls_completed"], 2)
        self.assertEqual(summary["total_usd"], "0.0015")
        self.assertEqual(caller.count, 2)
        att1 = json.loads((self.runs / "r1" / "attempt-0001.json").read_text())
        self.assertEqual(att1["raw_response"], raw1)     # verbatim preservation
        att2 = json.loads((self.runs / "r1" / "attempt-0002.json").read_text())
        self.assertEqual(att2["raw_response"], raw2)
        ledger = json.loads((self.runs / "r1" / "ledger.json").read_text())
        self.assertEqual(ledger["total_usd"], "0.0015")
        res1 = json.loads((self.runs / "r1" / "result-0001.json").read_text())
        self.assertEqual(res1["status"], "ok")
        self.assertFalse(self.lock.exists(), "shared lock released")

    def test_execute_rejects_bad_output_without_retry(self):
        caller = FakeCaller([{"raw_response": "not json at all", "usage":
                              {"cost_usd": "0.001"}}])
        with self.assertRaises(harness.OutputRejected):
            self.execute(caller)
        self.assertEqual(caller.count, 1, "no retry selected by outcome")
        att = json.loads((self.runs / "r1" / "attempt-0001.json").read_text())
        self.assertEqual(att["raw_response"], "not json at all")
        res = json.loads((self.runs / "r1" / "result-0001.json").read_text())
        self.assertEqual(res["status"], "rejected")
        self.assertFalse(self.lock.exists())

    def test_execute_unknown_charge_stops_run(self):
        caller = FakeCaller([{"raw_response": valid_response(), "usage": {}}])
        with self.assertRaises(harness.UnknownCharge):
            self.execute(caller)
        self.assertEqual(caller.count, 1)
        self.assertTrue((self.runs / "r1" / "attempt-0001.json").exists())
        self.assertFalse((self.runs / "r1" / "ledger.json").exists())
        self.assertFalse(self.lock.exists())

    def test_execute_budget_guard_stops_after_recording(self):
        caller = FakeCaller([{"raw_response": valid_response(),
                              "usage": {"cost_usd": "0.000005"}}])
        with self.assertRaises(harness.BudgetExceeded):
            self.execute(caller, max_usd=Decimal("0.000005"))
        self.assertEqual(caller.count, 1, "guard stops before the next call")
        ledger = json.loads((self.runs / "r1" / "ledger.json").read_text())
        self.assertEqual(ledger["total_usd"], "0.000005")
        self.assertFalse(self.lock.exists())

    def test_execute_adapter_failure_logged_not_retried(self):
        caller = FakeCaller([RuntimeError("boom")])
        with self.assertRaises(harness.StopRun):
            self.execute(caller)
        self.assertEqual(caller.count, 1)
        att = json.loads((self.runs / "r1" / "attempt-0001.json").read_text())
        self.assertEqual(att["status"], "error")
        self.assertIn("boom", att["error"])
        self.assertFalse(self.lock.exists())

    def test_gates_refuse_before_any_write_or_call(self):
        # tampered message hash
        doc = json.loads(self.schedule.read_text())
        doc["calls"][0]["user_sha256"] = "0" * 64
        harness.write_json(self.schedule, doc)
        caller = FakeCaller([])
        with self.assertRaises(harness.HarnessError):
            self.execute(caller)
        self.assertEqual(caller.count, 0)
        self.assertFalse((self.runs / "r1").exists(), "no run dir before gates pass")
        # invalid run id (fresh good schedule)
        self.build_country(n_calls=3, seed=9)
        caller = FakeCaller([])
        with self.assertRaises(harness.HarnessError):
            harness.execute_schedule(harness.country_schedule_path(),
                                     "../../evil", caller,
                                     runs_dir=self.runs, lock_path=self.lock)
        self.assertEqual(caller.count, 0)
        self.assertFalse(self.lock.exists())

    def test_lock_contention_refuses_before_call(self):
        foreign = json.dumps({"holder": "other", "pid": 1}) + "\n"
        self.lock.write_text(foreign, encoding="utf-8")
        caller = FakeCaller([])
        with self.assertRaises(harness.LockHeld):
            self.execute(caller)
        self.assertEqual(caller.count, 0)
        self.assertEqual(self.lock.read_text(), foreign)


# --------------------------------------------------------------------------- #
# Runner disabled by default; harness stays offline
# --------------------------------------------------------------------------- #

class DisabledByDefaultTests(FixtureCase):
    def _main(self, argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = harness.main(argv)
        return code, err.getvalue()

    def test_run_refuses_without_execute(self):
        code, err = self._main(["run", "--schedule", str(self.root / "nope.json"),
                                "--run-id", "r1"])
        self.assertEqual(code, 2)
        self.assertIn("--execute", err)
        self.assertIn("disabled by default", err)
        self.assertFalse((self.root / "runs").exists())
        self.assertFalse((self.root / "accounting.lock").exists())

    def test_run_execute_requires_provider(self):
        code, err = self._main(["run", "--schedule", str(self.root / "nope.json"),
                                "--run-id", "r1", "--execute"])
        self.assertEqual(code, 2)
        self.assertIn("--provider", err)
        self.assertFalse((self.root / "runs").exists())
        self.assertFalse((self.root / "accounting.lock").exists())

    def test_real_lock_and_runs_dirs_never_touched_by_tests(self):
        # This suite must leave the experiment dir untouched: these paths are
        # only reachable through execute_schedule with explicit temp dirs.
        # Existence-agnostic: real runs/ artifacts may legitimately exist; the
        # test asserts the SUITE changed nothing (snapshot taken at import).
        def snap():
            out = {"accounting.lock": (harness.HERE / "accounting.lock").exists()}
            runs = harness.HERE / "runs"
            out["runs"] = (runs.exists(),
                           sorted(e.name for e in runs.iterdir()) if runs.exists() else ())
            return out
        self.assertEqual(snap(), _PRE_RUNS_SNAPSHOT)

    def test_harness_has_no_network_or_credential_code(self):
        src = (HERE / "harness.py").read_text(encoding="utf-8")
        banned = ["urllib", "requests", "httpx", "httplib", "urlopen",
                  "http://", "https://", "api_key", "API_KEY", "ANTHROPIC",
                  "OPENAI", "Bearer ", "ftplib", "telnetlib"]
        for token in banned:
            self.assertNotIn(token, src, f"banned token {token!r} in harness.py")
        for word in ("socket", "ssl", "subprocess"):
            self.assertIsNone(re.search(rf"\b{word}\b", src),
                              f"banned import {word!r} in harness.py")


# --------------------------------------------------------------------------- #
# Real-data checks (read-only)
# --------------------------------------------------------------------------- #

class RealDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="five-way-real-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        old = harness.FROZEN_DIR
        harness.FROZEN_DIR = self.tmp / "frozen"
        self.addCleanup(setattr, harness, "FROZEN_DIR", old)

    def test_real_data_percentiles_and_eligibility(self):
        countries = harness.load_countries()
        got = harness.percentile_ranks(countries)
        want = independent_percentiles(countries)
        self.assertEqual(set(got), set(countries))
        for iso3 in got:
            self.assertAlmostEqual(got[iso3], want[iso3], places=9)
        eligible = harness.eligible_countries(countries)
        self.assertGreaterEqual(len(eligible), 100)
        self.assertFalse(set(eligible) & set(harness.TERRITORY_ISOS))
        self.assertNotIn("PRI", eligible)
        for band in harness.BANDS:
            members = [i for i in eligible if band[0] <= got[i] <= band[1]]
            self.assertGreaterEqual(len(members), 5,
                                    f"band {band} too small for a five-way draw")

    def test_real_usa_admin1_schedule_builds_and_verifies(self):
        doc = harness.make_admin1_schedule("USA", 3, 20261119)
        path = harness.admin1_schedule_path("USA")
        self.assertTrue(path.is_file())
        harness.run_schedule_gates(path)
        for call in doc["calls"]:
            self.assertEqual(len(set(call["selection"])), 5)
        system_text, users = zip(*harness.rebuild_messages(doc))
        everything = "\n".join(list(system_text) + list(users))
        usa = harness.load_countries()["USA"]
        self.assertNotIn(usa["name"], system_text[0])     # "United States"
        self.assertNotIn(str(usa["score"]), "".join(users))
        self.assertIn("Identities are withheld", system_text[0])

    def test_real_small_country_fails_closed(self):
        with self.assertRaises(harness.HarnessError):
            harness.make_admin1_schedule("ABW", 2, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

class TestPromptLeakGate(unittest.TestCase):
    """2026-11-08: fail-closed gate — score-bearing text must never render."""

    def test_gate_rejects_score_phrases(self):
        for bad in ("the national score is high",
                    "scores below the national score 0.36",
                    "rated at 0.42 on the index",
                    "sub-national score published",
                    "top score of 4.88 and below"):
            with self.assertRaises(harness.HarnessError):
                harness.assert_user_text_clean("dossier text " + bad)

    def test_gate_accepts_clean_text_and_percentages(self):
        harness.assert_user_text_clean(
            "HIV incidence remained under 0.1 percent through the period.")

    def test_rendered_prompts_pass_gate(self):
        for sched in (harness.country_schedule_path(),
                      harness.admin1_schedule_path("USA")):
            if sched.exists():
                doc = json.loads(sched.read_text())
                for sys_t, usr_t in harness.rebuild_messages(doc):
                    harness.assert_user_text_clean(usr_t)


class TestProviderEnvelope(unittest.TestCase):
    """2026-11-08: adapters may return the raw provider body; unwrap strictly."""

    @staticmethod
    def _content():
        return json.dumps({"results": [
            {"slot": s, "score": 0.5, "why": "w"} for s in range(1, 6)]})

    def test_valid_envelope_parses(self):
        env = json.dumps({"choices": [{"message": {"content": self._content()}}],
                          "usage": {}})
        parsed = harness.parse_five_way_response(env)
        self.assertEqual(len(parsed), 5)

    def test_envelope_empty_content_rejected(self):
        env = json.dumps({"choices": [{"message": {"content": ""}}]})
        with self.assertRaises(harness.OutputRejected):
            harness.parse_five_way_response(env)

    def test_envelope_bad_content_rejected(self):
        env = json.dumps({"choices": [{"message": {"content": '{"results": []}'}}]})
        with self.assertRaises(harness.OutputRejected):
            harness.parse_five_way_response(env)

    def test_plain_content_still_parses(self):
        parsed = harness.parse_five_way_response(self._content())
        self.assertEqual([e["slot"] for e in parsed], [1, 2, 3, 4, 5])


class CallSubsetTests(FixtureCase):
    """2026-11-08: --calls continuation subsets — dispatch only selected cells,
    never renumber or re-draw anything."""

    def setUp(self):
        super().setUp()
        self.build_country(n_calls=4, seed=5)
        self.schedule = harness.country_schedule_path()
        self.runs = self.root / "runs"
        self.lock = self.root / "execute.lock"

    def test_subset_dispatches_only_selected_cells(self):
        caller = FakeCaller([{"raw_response": valid_response(),
                              "usage": {"cost_usd": "0.001"}} for _ in range(2)])
        res = harness.execute_schedule(self.schedule, "r-sub", caller,
                                       runs_dir=self.runs, lock_path=self.lock,
                                       call_subset=frozenset({2, 4}))
        self.assertEqual(res["calls_completed"], 2)
        present = sorted(p.name for p in (self.runs / "r-sub").glob("result-*.json"))
        self.assertEqual(present, ["result-0002.json", "result-0004.json"])

    def test_parse_call_subset(self):
        self.assertEqual(harness.parse_call_subset("17-20"),
                         frozenset({17, 18, 19, 20}))
        self.assertEqual(harness.parse_call_subset("3,1"), frozenset({1, 3}))
        for bad in ("", "0", "5-2", "x"):
            with self.assertRaises(Exception):
                harness.parse_call_subset(bad)
