"""Machine-checkable pipeline invariants (see research/PIPELINE_INVARIANTS.md).

These tests guard against regressions of defects fixed in Nov 2026:
name-collision score sync, missing operative-parent overrides, and
record-meta/score references leaking into source summaries.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


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


if __name__ == "__main__":
    unittest.main()