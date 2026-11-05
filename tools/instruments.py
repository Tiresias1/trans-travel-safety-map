"""Canonical score-instrument vocabulary.

Three places needed to name how a score was produced (the published manifest, the
reproducibility audit, and the settlement guard) and they had drifted into calling the
same 63 country records "pairwise", "framework rating" and "encounter mean". This module
is the single definition, so they cannot disagree again.

Precedence matters: a country's provenance prose contains "anchor-ladder floor" when
describing endpoint clamping, so a naive substring match on "anchor" misclassifies those
records as anchored. Classify on the most specific signal first.
"""
from __future__ import annotations

ANCHORED = "anchored"
DESTINATION_SUMMARY = "destination summary"
COUNTRY_MEAN = "country-level rating (encounter mean)"
MIRROR = "territory mirror"
UNKNOWN = "unknown"

# Only an instrument whose published score IS the encounter mean may be moved to it.
SETTLEABLE = {COUNTRY_MEAN}


def classify(rec: dict) -> str:
    """Return the canonical instrument name for one published record."""
    prov = str(rec.get("scoreProvenance") or "").lower()
    d = rec.get("derivedFrom") or {}
    mode = d.get("mode") or ""

    # Prose is the most specific statement of how the published number was formed.
    # Negative context must be tested BEFORE the phrase it negates: "no destination
    # summary, because endpoint-clamping" and "anchor-ladder floor" both contain the
    # positive phrase as a substring and would otherwise be misclassified.
    if "territory" in prov and "mirror" in prov:
        return MIRROR
    if "endpoint-clamping" in prov or "no destination summary" in prov:
        # divisions sat at the anchor-ladder floor, so no destination summary was
        # formed and the country-level rating was published instead
        return COUNTRY_MEAN
    if "framework rating" in prov:
        return COUNTRY_MEAN
    if "destination summary" in prov:
        return DESTINATION_SUMMARY
    if "encounter mean" in prov:
        return COUNTRY_MEAN

    # Structured field next.
    if mode == "mirror":
        return MIRROR
    if mode == "reaggregate":
        return DESTINATION_SUMMARY
    if mode == "anchored" or "anchorRating" in d:
        return ANCHORED
    if "anchored" in prov:
        return ANCHORED
    # A record with a rater but no derivation is a country-level rating.
    if rec.get("ratedBy"):
        return COUNTRY_MEAN
    return UNKNOWN
