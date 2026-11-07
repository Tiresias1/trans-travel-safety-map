#!/usr/bin/env python3
"""Build data/*.json from research notes, compute ranks, validate.

Reads:  data/countries.json (hand/data-model maintained), data/admin1.json
        (optional), boundaries/*.geojson (for key coverage checks)
Writes: data/meta.json; augments records with rank fields.

SCORE-FREEZING BUILD (2026-11-13): this is a score-PRESERVING
validation/rank/metadata builder. No branch may change any country or
division score based on any other record or any fixed numerical value:
there is no provisional-calibration override, no ADM1-to-country (or
territory-to-country) score copy or reaggregation, and no auto-sync of
sparse local scores from the parent. Historical scores, scoreProvenance,
provisionalCalibration, derivedFrom and local summaries are preserved
verbatim as historical inputs until independently rerated; this script
never asserts they are correct and never generates a new score for any
record. Removed disallowed logic (frozen, not to be reintroduced without
independent validation): PROVISIONAL_CALIBRATION country override,
ROLLOUT_SUBSET national-score reaggregation, single-unit territory->country
score/text mirror, single-unit stand-in sync from parent, route-3
template auto-copy of the national score, and scoreProvenance rewriting.

Validation rules (fail loudly):
- score in [0,1]; stored precision is preserved EXACTLY as-is (the old
  6-dp normalisation write was removed with the score freeze — no branch
  in this builder rewrites a score). The UI displays 2 dp only.
- band consistent with score
- summary non-empty, 1-12 <p> paragraphs, <= MAX_SUMMARY_CHARS (16000) chars
- sources non-empty unless inherited
- every boundary polygon key has a data record (warning only — research in
  progress) and every data record matches a polygon (error)
"""
import json, os, re, statistics, sys
from datetime import date

BANDS = [
    (0.2, "Severe Risk"),
    (0.4, "High Risk"),
    (0.6, "Elevated Risk"),
    (0.8, "Reduced Risk"),
    (1.01, "Low Risk"),
]
GRADIENT_ANCHORS = [
    [0.0, "#67000d"], [0.1, "#d73027"], [0.3, "#fc8d59"], [0.5, "#fee08b"],
    [0.7, "#91cf60"], [0.9, "#1a9850"], [1.0, "#a8dbe8"],
]
# FROZEN (2026-11-13): the country-specific numeric PROVISIONAL_CALIBRATION
# override and the ROLLOUT_SUBSET reaggregation logic were REMOVED from this
# builder (see module docstring). Existing stored values, including the
# historical USA 0.330 and its provisionalCalibration block, remain historical
# inputs preserved verbatim - never recomputed, never asserted correct here.

def band_label(score):
    for mx, label in BANDS:
        if score < mx:
            return label
    return BANDS[-1][1]

# Shared summary-length ceiling. Raised 2026-11-13 from 8000 (itself raised
# 2026-10-05 from 2800): dossiers must carry ALL sourced claims without
# truncation — the real 8,792-char USA dossier must validate — while length
# validation STAYS strict (anything over this limit is rejected). Shared with
# tools/apply_rework.py, which imports this constant so the two gates can
# never drift apart.
MAX_SUMMARY_CHARS = 16000

def valid_summary(s):
    if not s:
        return False
    if len(s) > MAX_SUMMARY_CHARS:
        # over-limit summaries are rejected, never truncated (no facts dropped,
        # no prose rewritten by this builder)
        return False
    n_p = s.count("<p") + s.count("<P")
    return 1 <= n_p <= 12

def check_record(iso, r, errors, inherited_ok=False):
    if not isinstance(r.get("score"), (int, float)):
        errors.append(f"{iso}: missing score")
        return
    sc = r["score"]
    if not (0 <= sc <= 1):
        errors.append(f"{iso}: score out of range: {sc}")
    # NB: scores are NOT normalised before this check — stored values are
    # validated exactly as they come from the file (score freeze: the old
    # round-to-6dp write in main() was removed, so >6-dp precision survives).
    if "band" in r and r["band"] != band_label(sc):
        errors.append(f"{iso}: band mismatch: {r['band']} vs {band_label(sc)}")
    if not valid_summary(r.get("summary", "")):
        errors.append(f"{iso}: bad summary")
    if not r.get("sources") and not (inherited_ok and r.get("inherited")):
        errors.append(f"{iso}: no sources")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(r.get("researchedAt", ""))):
        errors.append(f"{iso}: bad/missing researchedAt")

def add_ranks(d, total, key="rank", tie_dp=2):
    """competition ranking: ties share best rank.

    Ties are judged at display precision (2 dp) so that scores differing only
    in the 4th-6th decimal — the residue of iterative refinement — do not
    produce a rank order the UI cannot show.
    """
    items = sorted(d.items(), key=lambda kv: -kv[1]["score"])
    prev = None; rank = 0
    for i, (k, r) in enumerate(items, 1):
        key_val = round(r["score"], tie_dp)
        if prev is None or key_val != prev:
            rank = i; prev = key_val
        r[key] = rank
    return d

def detect_repo_url():
    """HTTPS web URL of the git remote, for methodology links (empty if none)."""
    try:
        import subprocess
        url = subprocess.run(["git", "remote", "get-url", "origin"],
                             capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""
    if url.startswith("git@"):
        host, _, path = url[4:].partition(":")
        url = f"https://{host}/{path}"
    return url.removesuffix(".git")


def main():
    errors, warnings = [], []

    countries = json.load(open("data/countries.json"))
    geo = json.load(open("boundaries/countries.geojson"))
    geo_isos = {f["properties"]["iso3"] for f in geo["features"]}

    for iso, r in countries.items():
        # SCORE-PRESERVING: validate only; stored scores are never rewritten.
        check_record(iso, r, errors)
    missing = geo_isos - set(countries)
    if missing:
        warnings.append(f"{len(missing)} polygons without data (research in progress), e.g. {sorted(missing)[:8]}")
    orphans = set(countries) - geo_isos
    if orphans:
        errors.append(f"records without polygons: {sorted(orphans)}")

    add_ranks(countries, len(countries))
    json.dump(countries, open("data/countries.json", "w"), indent=1, ensure_ascii=False)

    admin1 = {}
    if os.path.exists("data/admin1.json"):
        admin1 = json.load(open("data/admin1.json"))
        geo1 = json.load(open("boundaries/admin1.geojson"))
        geo1_ids = {f["properties"]["shapeID"] for f in geo1["features"]}
        # ---- SCORE-PRESERVING FREEZE (2026-11-13) ----
        # The following historical writers are REMOVED and must not return
        # without independent validation: single-unit stand-in sync from the
        # parent, territory->country score/text mirror, ADM1->country score
        # reaggregation (destination summary / ROLLOUT_SUBSET), route-3
        # template auto-copy of the national score into thin regions, and
        # nationalFrameworkScore setdefaults. Division dispersion below is
        # METADATA only: it never feeds a score.
        _TEXT_FIELDS = ("summary", "tangentialFactors", "localsOnly", "outOfScopeNotes",
                        "blindSummary", "blindTangential", "blindLocalsOnly",
                        "blindOutOfScope", "sources")
        # SUPPLEMENTARY DIVISION DISPERSION (metadata only, scores untouched):
        # where a country has >=3 independently measured divisions, publish the
        # spread so a single number cannot hide a wide internal range.
        _by_iso = {}
        for sid, r in admin1.items():
            if r.get("inherited") or not isinstance(r.get("score"), (int, float)):
                continue
            iso_ = r.get("parentIso3") or r.get("iso3")
            _by_iso.setdefault(iso_, []).append(float(r["score"]))
        for iso, scores in _by_iso.items():
            c = countries.get(iso)
            if c is None or len(scores) < 3:
                continue
            # ENDPOINT GUARD (flag only): where more than 10% of a country's
            # divisions sit on the historical anchor-ladder floor, the spread
            # is flagged as untrustworthy — a note, never a score change.
            _clamped = sum(1 for s in scores if s <= 0.0201)
            c["divisionSpread"] = {"n": len(scores),
                                   "min": round(min(scores), 6),
                                   "max": round(max(scores), 6),
                                   "sd": round(statistics.pstdev(scores), 6)}
            if _clamped / len(scores) > 0.10:
                c["aggregationBlocked"] = ("endpoint-clamping: "
                                           f"{_clamped}/{len(scores)} divisions "
                                           "at the anchor-ladder floor")
            else:
                c.pop("aggregationBlocked", None)
        # FLOOR-BOUND divisions: an estimate that reached the clamp is not a
        # resolved score (review 2026-11-13). Flag them, keep the raw estimate for
        # diagnostics, and do not let them be ranked against each other.
        _n_floor = 0
        for sid, r in admin1.items():
            sc = r.get("score")
            if not isinstance(sc, (int, float)):
                continue
            if sc <= 0.0201:
                r["floorBound"] = True
                r["rawEstimate"] = (r.get("derivedFrom") or {}).get("anchorRating")
                r["worldRank"] = None
                r["countryRank"] = None
                _n_floor += 1
            else:
                r.pop("floorBound", None)
                r.pop("rawEstimate", None)
        if _n_floor:
            warnings.append(f"{_n_floor} divisions are floor-bound (unresolved, unranked)")
        # LOW-END UNCERTAINTY (2026-11-13): the anchor ladder's anchors disagree by
        # ~0.07 sd per target, which is larger than the differences being resolved
        # at the dangerous end. Flag such records rather than imply precision.
        _n_low = 0
        for sid, r in admin1.items():
            sc = r.get("score")
            if not isinstance(sc, (int, float)) or r.get("floorBound"):
                continue
            if sc < 0.20:
                r["lowEndUncertain"] = True
                _n_low += 1
            else:
                r.pop("lowEndUncertain", None)
        if _n_low:
            warnings.append(f"{_n_low} divisions below 0.20 carry low-end uncertainty")
        # ---- PROVENANCE FREEZE (2026-11-13) ----
        # Historical scoreProvenance, provisionalCalibration and derivedFrom
        # are preserved VERBATIM from the input file: this builder no longer
        # rewrites provenance text and no longer applies any
        # PROVISIONAL_CALIBRATION override (USA's stored 0.330 and its
        # provisionalCalibration block pass through untouched as historical
        # inputs; nothing here asserts they are correct).
        # floor flags are computed below AFTER the earlier countries dump:
        # persist them now so the file matches the validated state
        json.dump(countries, open("data/countries.json", "w"), indent=1, ensure_ascii=False)
        for sid, r in admin1.items():
            check_record(sid, r, errors, inherited_ok=True)
        # parent-inversion gate: a territory or region that the dossier documents as
        # carrying its own hostile layer must not score at/above its parent regime
        # (2026-10-16: PR scored above USA despite a care ban + emergency-era violence)
        _inv = []
        for sid, r in admin1.items():
            p3 = r.get("parentIso3")
            if not p3 or not r.get("dossier"):
                continue
            par = countries.get(p3)
            if not par:
                continue
            own_hostile = (r.get("ownHostile") is True or
                           bool(re.search(r"state of emergency|harshest|most restrictive|"
                                          r"bans (?:gender-affirming )?care",
                                          " ".join(str(r.get(f, "")) for f in _TEXT_FIELDS), re.I)))
            if own_hostile and float(r.get("score", 0)) >= float(par.get("score", 0)):
                _inv.append(f"{r.get('name')} {float(r.get('score',0)):.3f} >= {p3} {float(par.get('score',0)):.3f}")
        if _inv:
            warnings.append("PARENT-INVERSION: " + "; ".join(_inv[:8]))
        if set(admin1) - geo1_ids:
            errors.append(f"admin1 records without polygons: {sorted(set(admin1) - geo1_ids)[:8]}")
        n_missing = len(geo1_ids - set(admin1))
        warnings.append(f"{n_missing} admin1 polygons without data")
        add_ranks(admin1, len(admin1), key="worldRank")
        # within-country ranks
        by_country = {}
        for sid, r in admin1.items():
            by_country.setdefault(r["iso3"], []).append((sid, r))
        for iso, lst in by_country.items():
            lst.sort(key=lambda kv: -kv[1]["score"])
            prev = None; rank = 0; total = len(lst)
            for i, (sid, r) in enumerate(lst, 1):
                if prev is None or r["score"] != prev:
                    rank = i; prev = r["score"]
                r["countryRank"] = rank
                r["unitsInCountry"] = total
        json.dump(admin1, open("data/admin1.json", "w"), indent=1, ensure_ascii=False)

    meta = {
        "generatedAt": date.today().isoformat(),
        "edition": "2026",
        "updateCadence": "annual",
        "methodologyVersion": "2.0",
        "repoUrl": detect_repo_url(),
        "bandEdges": [0.2, 0.4, 0.6, 0.8, 1.0],
        "bandLabels": [b[1] for b in BANDS],
        "gradientAnchors": GRADIENT_ANCHORS,
        "totalCountries": len(countries),
        "totalAdmin1": len(admin1),
        "disputedBoundaryNotes": "tools/patch_dejure.md",
    }
    json.dump(meta, open("data/meta.json", "w"), indent=1)

    for w in warnings:
        print("WARN:", w)
    if errors:
        print("\n".join("ERROR: " + e for e in errors))
        sys.exit(1)
    print(f"OK: {len(countries)} countries, {len(admin1)} admin1 units; ranks written; meta written")

if __name__ == "__main__":
    main()
