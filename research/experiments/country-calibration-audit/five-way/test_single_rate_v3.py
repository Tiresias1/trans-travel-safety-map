#!/usr/bin/env python3
"""Unit tests for the v3 structured rating output.

These tests are deliberately offline and provider-free. They validate the
schema that forces a combined-regime factor matrix and anchor comparisons.
"""
import copy
import json
import unittest

import single_rate_v3 as V3

BASE = {
    "rating": 0.62,
    "explanation": "A combined operative regime with strong local protections "
                   "but unremedied national entry and custody exposures.",
    "factor_matrix": {
        key: {"exposure": "Documented exposure.", "protection": "Not documented.",
              "interaction": "No operative interaction documented.",
              "status": "documented"}
        for key in V3.FACTOR_KEYS
    },
    "anchor_checks": [
        {"anchor_id": "0.35-A", "comparison": "More severe nationwide exposure."},
        {"anchor_id": "0.55-B", "comparison": "Similar mixed national/local regime."},
        {"anchor_id": "0.75-C", "comparison": "Strong protections without the same federal exposure."},
    ],
    "synthesis": "State protections are local; national entry, facilities, "
                 "investigation, and custody authorities remain operative.",
}


class ParseV3Tests(unittest.TestCase):
    def test_valid_output(self):
        parsed = V3.parse_v3(json.dumps(BASE))
        self.assertEqual(parsed["rating"], 0.62)
        self.assertEqual(len(parsed["anchor_checks"]), 3)

    def test_fenced_json_accepted(self):
        parsed = V3.parse_v3("```json\n" + json.dumps(BASE) + "\n```")
        self.assertEqual(parsed["rating"], 0.62)

    def test_exposure_alias_accepted(self):
        alias = copy.deepcopy(BASE)
        alias["exposure"] = alias.pop("explanation")
        parsed = V3.parse_v3(json.dumps(alias))
        self.assertEqual(parsed["summary_key_used"], "exposure")

    def test_missing_factor_rejected(self):
        bad = copy.deepcopy(BASE)
        del bad["factor_matrix"]["minors_guardians"]
        with self.assertRaises(ValueError):
            V3.parse_v3(json.dumps(bad))

    def test_unknown_anchor_rejected(self):
        bad = copy.deepcopy(BASE)
        bad["anchor_checks"][0]["anchor_id"] = "0.99-Z"
        with self.assertRaises(ValueError):
            V3.parse_v3(json.dumps(bad))

    def test_prompt_forbids_parent_arithmetic(self):
        cells = V3.build("admin1")
        system_text = cells[0]["_system"].lower()
        for needle in ("combined operative regime",
                       "do not estimate a parent score",
                       "factor_matrix",
                       "three different synthetic-anchor ids"):
            self.assertTrue(needle in system_text, f"missing: {needle}")


if __name__ == "__main__":
    unittest.main()
