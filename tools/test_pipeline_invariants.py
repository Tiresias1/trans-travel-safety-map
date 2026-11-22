"""Machine-checkable pipeline invariants (see research/PIPELINE_INVARIANTS.md).

These tests guard against regressions of defects fixed in Nov 2026:
name-collision score sync, missing operative-parent overrides, and
record-meta/score references leaking into source summaries.
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "research" / "experiments"
                        / "country-calibration-audit" / "five-way"))
import harness as H  # noqa: E402  (shared neutralizer + renderer)


def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


class TestPipelineInvariants(unittest.TestCase):
    def test_invariants_doc_exists(self):
        self.assertTrue((ROOT / "research" / "PIPELINE_INVARIANTS.md").exists())

    def test_florida_name_collision_not_resynced(self):
        # Two divisions named Florida (USA, URY) must not share provenance
        # source or score; a name-keyed sync would make them identical.
        a = load("admin1.json")
        fl = [r for r in a.values() if r.get("name") == "Florida"]
        self.assertGreaterEqual(len(fl), 2)
        usa = next(r for r in fl if r.get("iso3") == "USA")
        ury = next(r for r in fl if r.get("iso3") == "URY")
        self.assertNotEqual(usa.get("score"), ury.get("score"))
        self.assertNotEqual(
            usa.get("derivedFrom", {}).get("source"),
            ury.get("derivedFrom", {}).get("source"),
        )

    def test_occupied_regions_have_operative_parent(self):
        a = load("admin1.json")
        for sid in [
            "14850775B24260608407062",  # Crimea
            "14850775B70667807354554",  # Sevastopol
            "14850775B15615817748403",  # Donetsk
            "14850775B31033086218351",  # Luhansk
        ]:
            rec = a[sid]
            self.assertEqual(rec.get("operativeParent"), "RUS", sid)
            self.assertTrue(rec.get("operativeParentNote"), sid)
            # real dossiers, not stubs
            self.assertGreater(len(rec.get("summary", "")), 800, sid)
            self.assertGreater(len(rec.get("blindSummary", "")), 800, sid)

    def test_no_record_meta_in_sources(self):
        # First-line regex guard; paraphrases need the periodic LLM audit.
        pat = re.compile(
            r"for this record|record's (national )?score|"
            r"baseline behind|the claim this record relies on|"
            r"this record rests|supplies this record",
            re.I,
        )
        for fn in ("countries.json", "admin1.json"):
            d = load(fn)
            for rid, rec in d.items():
                if not isinstance(rec, dict):
                    continue
                texts = [
                    s.get("summary", "")
                    for s in rec.get("sources", []) or []
                    if isinstance(s, dict)
                ] + list(rec.get("blindSourceSummaries", []) or [])
                for t in texts:
                    self.assertIsNone(pat.search(t), f"{fn}:{rid}: {t[:120]}")


class TestBlindingInvariants(unittest.TestCase):
    """2026-11-21 blinding overhaul: single-render + leak gate."""

    @staticmethod
    def _fixture():
        countries = {"XXX": {
            "name": "Parentland", "score": "0.5",
            "blindSummary": "PARENT BLIND SUMMARY UNIQUEFRAME",
            "blindTangential": "PARENT TANG", "blindLocalsOnly": "PARENT LOC",
            "blindSourceSummaries": []}}
        admin1 = {"XDIV1": {
            "iso3": "XXX", "name": "Regionone", "score": 0.5,
            "summary": "PLAIN SUMMARY SHOULD NOT RENDER",
            "blindSummary": "UNIQUEFACTPHRASE for this division",
            "blindSourceSummaries": [], "blindTangential": "",
            "blindLocalsOnly": "", "blindOutOfScope": ""}}
        return admin1, countries

    def test_no_duplicate_evidence_rendering(self):
        # The rendered dossier contains the blindSummary content exactly
        # once, and the canonical build_dossier appends nothing for a
        # record that has a blindSummary (single-render rule).
        admin1, countries = self._fixture()
        dossier = H.render_admin1_dossier("XDIV1", "XXX", admin1, countries)
        self.assertEqual(dossier.count("UNIQUEFACTPHRASE"), 1)
        self.assertNotIn("PLAIN SUMMARY SHOULD NOT RENDER", dossier)
        import global_adm1_iterative as GA
        local = H.neutralize(admin1["XDIV1"]["blindSummary"], "Regionone",
                             "XXX", "Parentland")
        self.assertEqual(GA.build_dossier(dossier, local, True), dossier)
        appended = GA.build_dossier(dossier, local, False)
        self.assertEqual(appended.count("UNIQUEFACTPHRASE"), 2)  # only when no blind
        self.assertIn("DIVISION LOCAL EVIDENCE", appended)

    def test_neutralize_removes_demonyms_and_institutions(self):
        out = H.neutralize(
            "The Scottish Parliament and Police Scotland in Scotland "
            "(United Kingdom, GBR) ruled.",
            "Scotland", "GBR", "United Kingdom")
        self.assertNotIn("Scottish", out)
        self.assertNotIn("Scotland", out)
        self.assertNotIn("Parliament", out)
        self.assertNotIn("GBR", out)

    def test_leak_gate_on_four_uk_nations(self):
        admin1, countries = H.load_admin1(), H.load_countries()
        gbr = {sid: r for sid, r in admin1.items() if r.get("iso3") == "GBR"}
        self.assertEqual({r.get("name") for r in gbr.values()},
                         {"Scotland", "Wales", "Northern Ireland", "England"})
        siblings = [str(r.get("name") or "") for r in gbr.values()]
        for sid, rec in gbr.items():
            dossier = H.render_admin1_dossier(sid, "GBR", admin1, countries)
            leaks = H.find_identity_leaks(
                dossier, str(rec.get("name") or ""),
                str(countries["GBR"].get("name") or ""), "GBR", siblings)
            self.assertEqual(leaks, [], f"{rec.get('name')}: {leaks}")


if __name__ == "__main__":
    unittest.main()