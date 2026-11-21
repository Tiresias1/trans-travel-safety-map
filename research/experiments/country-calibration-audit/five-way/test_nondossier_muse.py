#!/usr/bin/env python3
"""Unit tests for the non-dossier knowledge pass (offline, provider-free).

Cover the {rating, basis, knowledge} output contract (including the
adjectival-"prompt" false-positive fix), the public-summary basis hygiene
rules, and the frozen scope selection with its two exclusion sets.
"""
import json
import unittest

import nondossier_muse as N


def _basis(words=80):
    return ("The region inherits the national regime, under which same-sex "
            "conduct is criminalised and no protection applies. ") + \
        "Local conditions are conservative and rural. " * 20


BASE = {"rating": 0.12, "basis": _basis(), "knowledge": "region-specific"}


class ParseNondossierTests(unittest.TestCase):
    def test_valid_output(self):
        parsed = N.parse_nondossier(json.dumps(BASE))
        self.assertEqual(parsed["rating"], 0.12)
        self.assertEqual(parsed["knowledge"], "region-specific")

    def test_fenced_json_accepted(self):
        text = "```json\n" + json.dumps(BASE) + "\n```"
        self.assertEqual(N.parse_nondossier(text)["rating"], 0.12)

    def test_extra_key_rejected(self):
        with self.assertRaises(ValueError):
            N.parse_nondossier(json.dumps(dict(BASE, note="x")))

    def test_rating_out_of_range_rejected(self):
        with self.assertRaises(ValueError):
            N.parse_nondossier(json.dumps(dict(BASE, rating=1.2)))

    def test_knowledge_enum(self):
        for value in ("region-specific", "parent-only"):
            self.assertEqual(N.parse_nondossier(
                json.dumps(dict(BASE, knowledge=value)))["knowledge"], value)
        with self.assertRaises(ValueError):
            N.parse_nondossier(json.dumps(dict(BASE, knowledge="guessed")))

    def test_basis_word_bounds(self):
        with self.assertRaises(ValueError):
            N.parse_nondossier(json.dumps(dict(BASE, basis="too short")))
        with self.assertRaises(ValueError):
            N.parse_nondossier(json.dumps(dict(BASE, basis="word " * 180)))

    def test_basis_score_number_rejected(self):
        basis = "The national rating is 0.10 here. " + _basis()
        with self.assertRaises(ValueError):
            N.parse_nondossier(json.dumps(dict(BASE, basis=basis)))

    def test_basis_meta_rejected(self):
        for meta in ("this record", "the rubric", "the anchors", "the model"):
            with self.assertRaises(ValueError):
                N.parse_nondossier(json.dumps(
                    dict(BASE, basis=f"Text about {meta}. " + _basis())))

    def test_adjectival_prompt_accepted(self):
        # Regression: three preserved draws were falsely rejected because
        # "prompt" appeared as an adjective/verb in legitimate prose.
        for phrase in ("secure prompt remedy", "not always prompt for visitors",
                       "a mismatch can prompt curiosity"):
            parsed = N.parse_nondossier(json.dumps(
                dict(BASE, basis=f"Officials {phrase}. " + _basis())))
            self.assertEqual(parsed["rating"], 0.12)

    def test_prompt_as_process_meta_rejected(self):
        with self.assertRaises(ValueError):
            N.parse_nondossier(json.dumps(
                dict(BASE, basis="As stated in the prompt. " + _basis())))


class ScopeRegionsTests(unittest.TestCase):
    def setUp(self):
        self.countries = {"XYZ": {"name": "Xanadu", "score": 0.4,
                                  "iterativeScore": 0.42, "summary": "<p>s</p>"}}
        self.admin1 = {
            "S1": {"iso3": "XYZ", "name": "Estimated", "estimated": True},
            "S2": {"iso3": "XYZ", "name": "NoDiff"},
            "S3": {"iso3": "XYZ", "name": "Dossier"},
            "S4": {"iso3": "ASM", "name": "Territory", "estimated": True},
            "14850775B24260608407062": {"iso3": "XYZ", "name": "Crimea",
                                        "estimated": True},
        }

    def test_union_and_exclusions(self):
        out = N.scope_regions(self.admin1, self.countries, {"S2:NoDiff"})
        self.assertEqual([r["sid"] for r in out], ["S1", "S2"])
        self.assertTrue(out[0]["estimated"] and not out[0]["no_differentiator"])
        self.assertTrue(out[1]["no_differentiator"] and not out[1]["estimated"])

    def test_all_occupied_sids_excluded(self):
        admin1 = {sid: {"iso3": "XYZ", "name": sid, "estimated": True}
                  for sid in N.EXCLUDED_SIDS}
        self.assertEqual(N.scope_regions(admin1, self.countries, set()), [])

    def test_parent_score_prefers_iterative(self):
        out = N.scope_regions(self.admin1, self.countries, set())
        self.assertEqual(out[0]["parent_score"], 0.42)
        del self.countries["XYZ"]["iterativeScore"]
        out = N.scope_regions(self.admin1, self.countries, set())
        self.assertEqual(out[0]["parent_score"], 0.4)


if __name__ == "__main__":
    unittest.main()
