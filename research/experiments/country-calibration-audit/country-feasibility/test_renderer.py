#!/usr/bin/env python3
"""Targeted offline unit tests for the country-feasibility renderer/validator.

Run from this directory (no network, no writes, no model calls):

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_renderer
"""
import json
import re
import unittest
from pathlib import Path

import renderer as R

HERE = Path(__file__).resolve().parent


class _fx:  # namespace holder for shared fixtures (populated in setUpModule)
    pass


def setUpModule():
    R.RESULTS.clear()  # keep unit runs independent of the CLI check log
    _fx.ledger = R.load(HERE / "ledger.json")
    _fx.cands = R.derive_prompts(_fx.ledger)
    _fx.dm = R.data_meta()
    _fx.packets = {iso: R.render_packet(iso, _fx.dm["data"], _fx.ledger)
                   for iso in R.ISOS}
    _fx.sched = R.build_schedule()
    _fx.msgs = R.build_messages(_fx.sched, _fx.packets)


class FailClosedEdits(unittest.TestCase):
    def test_apply_once_fails_closed(self):
        with self.assertRaises(SystemExit):       # missing source block
            R.apply_once("abc", "not-there", "x", "missing")
        with self.assertRaises(SystemExit):       # nonunique source block
            R.apply_once("aXa", "a", "b", "nonunique")
        self.assertEqual(R.apply_once("abc", "b", "X", "ok"), "aXc")  # exactly once


class DerivedPromptInvariants(unittest.TestCase):
    def test_scale_invariants_survive_conversion(self):
        for v in R.VARIANTS:
            t = _fx.cands[v]
            for s in R.PROMPT_REQUIRED:
                self.assertIn(s, t, f"[{v}] missing {s!r}")
            for s in R.PROMPT_FORBIDDEN:
                self.assertNotIn(s, t, f"[{v}] pairwise remnant {s!r}")

    def test_single_score_schema_and_abstention_in_both_variants(self):
        for v in R.VARIANTS:
            t = _fx.cands[v]
            self.assertIn('"status": "ok", "score": <float 0.0-1.0>', t)
            self.assertIn('"status": "insufficient_evidence" and "score": null', t)
            self.assertIn("Never resolve a missing or empty dossier to a midpoint", t)
        oa = _fx.cands["A"][_fx.cands["A"].index("## Output format"):]
        ob = _fx.cands["B"][_fx.cands["B"].index("## Output format"):]
        self.assertEqual(oa, ob)

    def test_ab_difference_preserved_after_masking_declared_sites(self):
        sites = json.loads(
            (HERE.parent / "rule-contrasts" / "replacements.json").read_text(
                encoding="utf-8"))["sites"]

        def mask(text, v):
            # mask this pilot's variant edit (T2) first: it preserves the inherited
            # task_line site text inside its own after-block; then mask the seven
            # inherited variant sites (mirroring the builder's falsy-value fallback)
            for e in _fx.ledger["prompt_edits"]:
                if e["scope"] == "variant":
                    text = text.replace(e["after"][v], f"<<{e['id']}>>")
            for s in sites:
                text = text.replace(s[v] if s[v] else s["before"],
                                     f"<<{s['id']}>>")
            return text

        ma, mb = mask(_fx.cands["A"], "A"), mask(_fx.cands["B"], "B")
        self.assertEqual(ma, mb)
        for s in sites:
            if s["id"] == "task_line":
                # subsumed: the T2 edit replaced this site's frozen text wholesale,
                # preserving its A/B difference inside the new task line
                continue
            self.assertIn(f"<<{s['id']}>>", ma)
        self.assertIn("<<T2_task_line>>", ma)


class PilotOnlyPackets(unittest.TestCase):
    def test_whitelist_no_published_values_no_name_literals(self):
        for iso in R.ISOS:
            rec = _fx.dm["data"][iso]
            self.assertEqual(set(R.pilot_fields(iso, _fx.dm["data"], _fx.ledger)),
                             set(R.WHITELIST))
            pkt = _fx.packets[iso]
            for val in (rec["score"], rec.get("nationalFrameworkScore"),
                        rec.get("band")):
                if val is not None:
                    self.assertNotRegex(pkt, r"\b%s\b" % re.escape(str(val)))
            for anchor in rec.get("anchorRefs") or []:
                self.assertNotRegex(pkt, r"\b%s\b" % re.escape(anchor))
        src = (HERE / "renderer.py").read_text(encoding="utf-8").lower()
        self.assertNotIn(("adm" + "1"), src)  # division score file never referenced
        blob = "\n".join(_fx.packets.values())
        for name in R.COUNTRY_NAMES:
            self.assertNotRegex(blob, r"\b%s\b" % re.escape(name))

    def test_gbr_pilot_only_view_excludes_index_scores_keeps_facts(self):
        g = _fx.packets["GBR"]
        for s in ("22nd", "third steepest", "86% score", "45%", "9th in 2020",
                  "66% and concern", "down from 1st"):
            self.assertNotIn(s, g)
        for s in ("hostile climate on trans rights", "steepest",
                  "86% of national respondents"):
            self.assertIn(s, g)
        self.assertEqual({e["iso"] for e in _fx.ledger["packet_edits"]}, {"GBR"})

    def test_packet_edits_touch_gbr_only(self):
        for iso in ("USA", "NPL", "VAT"):
            rec = _fx.dm["data"][iso]
            raw = {k: rec[k] for k in R.WHITELIST}
            self.assertEqual(_fx.packets[iso], R.render_packet_from_fields(raw))


class ScheduleAndSentinels(unittest.TestCase):
    def test_schedule_structure_and_determinism(self):
        self.assertEqual(_fx.sched, R.build_schedule())  # frozen seed -> deterministic
        self.assertEqual(len(_fx.sched), 40)
        core = [r for r in _fx.sched if r["sentinel"] == "core"]
        self.assertEqual(len(core), 32)
        self.assertEqual(len({(r["case"], r["model"], r["variant"], r["draw"])
                              for r in core}), 32)
        for b in (1, 2):
            self.assertTrue(R.block_ok([r for r in _fx.sched if r["block"] == b]))

    def test_neutral_and_empty_sentinel_messages(self):
        core_same = f"{R.CORE_LABEL}\n\n{_fx.packets[R.NEUTRAL_CASE]}"
        neut = [m for m in _fx.msgs if m["sentinel"] == "neutral_label"]
        self.assertEqual(len(neut), 4)
        for m in neut:
            self.assertTrue(m["message"].startswith(R.NEUTRAL_LABEL + "\n\n"))
            self.assertEqual(m["message"].replace(R.NEUTRAL_LABEL, R.CORE_LABEL, 1),
                             core_same)
        empty = {m["message"] for m in _fx.msgs if m["sentinel"] == "empty"}
        self.assertEqual(len(empty), 1)
        for name in R.COUNTRY_NAMES:
            self.assertNotIn(name, next(iter(empty)))


class ReservationAmendment(unittest.TestCase):
    """The pre-outcome reservation amendment is pre-registered, fits the exact
    plan and preserves the original proposal verbatim."""

    def test_amendment_in_manifest_matches_constants_and_exact_plan(self):
        man = R.load(HERE / "frozen" / "manifest.json")
        am = man["reservation_amendment"]
        self.assertEqual(am["per_call_input_reservation_units"], 70_000)
        self.assertEqual(am["aggregate_input_reservation_units"], 2_400_000)
        pb = {v: len(_fx.cands[v].encode()) for v in R.VARIANTS}
        units = R.reservation_plan(_fx.sched, _fx.msgs, pb)
        self.assertEqual(max(units), 66_611)
        self.assertEqual(sum(units), 2_316_208)
        self.assertEqual(am["plan_max_per_call_units"], max(units))
        self.assertEqual(am["plan_aggregate_units"], sum(units))
        self.assertLessEqual(max(units), R.RESERVATION_PER_CALL_UNITS)
        self.assertLessEqual(sum(units), R.RESERVATION_AGGREGATE_UNITS)

    def test_original_proposal_preserved_and_annotated_not_a_bound(self):
        man = R.load(HERE / "frozen" / "manifest.json")
        am = man["reservation_amendment"]
        self.assertEqual(am["preserved_original_proposal"],
                         R.PRESERVED_PROPOSED_INPUT_CAPS)
        self.assertEqual(man["proposed_caps"]["per_call_max_input_tokens"], 20_000)
        self.assertEqual(man["proposed_caps"]["aggregate_max_input_tokens"], 800_000)
        self.assertEqual(man["proposed_caps"]["aggregate_max_usd_including_failures"],
                         10.0)
        self.assertIn("not a proven provider-native token bound", am["not_claims"])
        self.assertIn("not a provider-enforced spend limit", am["not_claims"])
        self.assertTrue(am["status"].startswith("pre-outcome"))

    def test_amendment_only_touches_reservations(self):
        # design invariants stay frozen: attempts, models, settings, retries, seed
        man = R.load(HERE / "frozen" / "manifest.json")
        self.assertEqual(man["attempt_ceiling"], 40)
        self.assertEqual(man["models"], list(R.MODELS))
        self.assertEqual(man["requested_settings"], R.REQUESTED_SETTINGS)
        self.assertEqual(man["proposed_caps"]["retries_selected_for_output"], 0)
        self.assertEqual(man["seed"], R.SEED)
        self.assertEqual(len(_fx.sched), 40)


class ReproducibilityProvenance(unittest.TestCase):
    """--verify keys on content hashes; the recorded commit is provenance only."""

    @staticmethod
    def _man(sha="a" * 64, commit="oldcommit"):
        return {"git_commit": commit, "evidence_snapshot": {"sha256": sha}}

    def test_head_advance_with_identical_content_passes(self):
        ok, note = R.evidence_snapshot_status("a" * 64, "newcommit", self._man())
        self.assertTrue(ok)
        self.assertIn("provenance only", note)
        self.assertIn("identical", note)

    def test_same_commit_with_identical_content_has_no_note(self):
        ok, note = R.evidence_snapshot_status("a" * 64, "oldcommit", self._man())
        self.assertTrue(ok)
        self.assertEqual(note, "")

    def test_content_drift_fails_with_or_without_head_move(self):
        ok, _ = R.evidence_snapshot_status("b" * 64, "oldcommit", self._man())
        self.assertFalse(ok)
        ok, note = R.evidence_snapshot_status("b" * 64, "newcommit", self._man())
        self.assertFalse(ok)
        self.assertIn("DRIFTED", note)


class NoProviderPath(unittest.TestCase):
    def test_no_network_or_credential_code(self):
        blob = ""
        for f in ("renderer.py", "test_renderer.py"):
            blob += (HERE / f).read_text(encoding="utf-8")
        for tok in ("ur" + "llib", "re" + "quests", "sock" + "et",
                    "api" + "_key", "Bear" + "er ", "call" + "_api"):
            self.assertNotIn(tok, blob)


if __name__ == "__main__":
    unittest.main()