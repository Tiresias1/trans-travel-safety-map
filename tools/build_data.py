#!/usr/bin/env python3
"""Build data/*.json from research notes, compute ranks, validate.

Reads:  data/countries.json (hand/data-model maintained), data/admin1.json
        (optional), boundaries/*.geojson (for key coverage checks)
Writes: data/meta.json; augments records with rank fields.

Validation rules (fail loudly):
- score in [0,1]; stored at full precision (normalised to 6 dp) so that
  iterative refinement (tools/blind_pairwise.py) can drift scores in small
  increments. The UI displays 2 dp only.
- band consistent with score
- summary non-empty, 1-12 <p> paragraphs, <= 8000 chars
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

def band_label(score):
    for mx, label in BANDS:
        if score < mx:
            return label
    return BANDS[-1][1]

def valid_summary(s):
    if not s:
        return False
    if len(s) > 8000:  # raised 2026-10-05: dossiers must carry ALL sourced claims;
        # the old 2800 cap forced 3-4-para truncation that dropped evidence
        # (USA federal layer, NER penal code). UI scrolls; no display cap.
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
    # NB: scores are normalised to 6 dp in main() before this check runs, so
    # extra precision is silently rounded rather than rejected — that is what
    # lets tools/blind_pairwise.py drift scores in sub-cent increments.
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
        # normalise to 6 dp so tiny drift increments survive round-trips
        if isinstance(r.get("score"), float):
            r["score"] = round(r["score"], 6)
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
        # ---- single-unit stand-ins TRACK their country record ----
        # A one-division country's admin1 row IS the whole country: its score
        # must equal the country's, or the map shows different values in
        # countries vs states/provinces mode for the same place (ASM bug
        # 2026-10-05). Enforced at build time so it can never drift again.
        from collections import defaultdict
        _per = defaultdict(list)
        for sid, r in admin1.items():
            _per[r["iso3"]].append((sid, r))
        _n_sync = 0
        _TEXT_FIELDS = ("summary", "tangentialFactors", "localsOnly", "outOfScopeNotes",
                        "blindSummary", "blindTangential", "blindLocalsOnly",
                        "blindOutOfScope", "sources")
        _TERRITORIES = {r.get("iso3") for r in admin1.values() if r.get("parentIso3")}
        for iso, lst in _per.items():
            if len(lst) == 1 and iso in countries:
                if iso in _TERRITORIES:
                    # territory: admin1 record is PRIMARY (scored independently
                    # in mixed mode); the country record mirrors it for display —
                    # score AND text (the popup reads the country record)
                    sid, r = lst[0]
                    c = countries[iso]
                    c["score"] = round(float(r["score"]), 6)
                    c["band"] = band_label(c["score"])
                    for fld in _TEXT_FIELDS:
                        if fld in r:
                            c[fld] = r[fld]
                        else:
                            c.pop(fld, None)
                    continue
                if lst[0][1].get("dossier"):
                    continue
                sid, r = lst[0]
                c = countries[iso]
                c_score = round(float(c["score"]), 6)
                if abs(float(r.get("score", 0)) - c_score) > 1e-9:
                    r["score"] = c_score
                    r["band"] = band_label(c_score)
                    _n_sync += 1
                # text mirrors the country too: a one-division country IS the
                # country — its region popup must read identically (2026-10-06)
                for f in _TEXT_FIELDS:
                    if c.get(f) and r.get(f) != c[f]:
                        r[f] = c[f]
                        _n_sync += 1
                r["inherited"] = True
        if _n_sync:
            warnings.append(f"synced {_n_sync} single-unit admin1 stand-ins to country scores")
        # NATIONAL AS DESTINATION SUMMARY (2026-11-13, review recommendation):
        # where a country has >=3 independently measured divisions, its published
        # score is the visitor-weighted mean of those divisions (currently
        # unweighted, which is a declared choice, not a default). The pairwise
        # national rating is retained separately as the national-framework
        # component, and dispersion is published so a single number cannot hide a
        # wide internal range. Inherited divisions carry no independent evidence
        # and are excluded (missing-data model, not silent recursion).
        _by_iso = {}
        for sid, r in admin1.items():
            if r.get("inherited") or not isinstance(r.get("score"), (int, float)):
                continue
            iso_ = r.get("parentIso3") or r.get("iso3")
            _by_iso.setdefault(iso_, []).append(float(r["score"]))
        _n_re = 0
        for iso, scores in _by_iso.items():
            c = countries.get(iso)
            if c is None or len(scores) < 3:
                continue
            # ENDPOINT GUARD: the anchor ladder's lowest anchor is 0.10, so
            # estimates below that are extrapolated and clamp at the floor. Where
            # more than 10% of a country's divisions sit on the clamp, its
            # division mean is not trustworthy as a level: keep the framework
            # score and publish the division data as supplementary instead.
            _clamped = sum(1 for s in scores if s <= 0.0201)
            if _clamped / len(scores) > 0.10:
                c["divisionSpread"] = {"n": len(scores),
                                       "min": round(min(scores), 6),
                                       "max": round(max(scores), 6),
                                       "sd": round(statistics.pstdev(scores), 6)}
                c["aggregationBlocked"] = ("endpoint-clamping: "
                                           f"{_clamped}/{len(scores)} divisions "
                                           "at the anchor-ladder floor")
                # restore the framework score: a previously aggregated value
                # must not survive once aggregation is disallowed
                _fs = c.get("nationalFrameworkScore")
                if isinstance(_fs, (int, float)):
                    c["score"] = round(float(_fs), 6)
                    c["band"] = band_label(c["score"])
                if (c.get("derivedFrom") or {}).get("mode") == "reaggregate":
                    c["derivedFrom"] = {"mode": "pairwise"}
                continue
            c.setdefault("nationalFrameworkScore", round(float(c.get("score", 0)), 6))
            m = sum(scores) / len(scores)
            c["score"] = round(min(1.0, max(0.0, m)), 6)
            c["band"] = band_label(c["score"])
            c["divisionSpread"] = {"n": len(scores),
                                   "min": round(min(scores), 6),
                                   "max": round(max(scores), 6),
                                   "sd": round(statistics.pstdev(scores), 6)}
            c["derivedFrom"] = {"mode": "reaggregate", "source": "divisions",
                                "weighting": "unweighted"}
            _n_re += 1
        if _n_re:
            warnings.append(f"national scores re-aggregated from divisions: {_n_re}")

        # territory mirrors changed the countries dict AFTER it was dumped —
        # persist the mirror now (ASM 2026-10-08: country showed a stale score)
        _terr_mirror = any(iso in _TERRITORIES for iso in _per)
        if _terr_mirror:
            json.dump(countries, open("data/countries.json", "w"), indent=1, ensure_ascii=False)
        # ROUTE-3 INVARIANT (2026-10-29): an "estimated" region with the
        # no-signal template IS the national assessment — its score must track
        # the national score on every build. Previously these kept a stale
        # absolute copy from whichever wave generated them (Mongolia's regions
        # showed 0.68 while the country was 0.52; 94/190 countries affected).
        _TMPL = "No sub-national signal was identified; the national assessment applies here"
        _n_inh = 0
        for sid, r in admin1.items():
            if not r.get("estimated"):
                continue
            if _TMPL not in str(r.get("summary", "")):
                continue
            par = countries.get(r.get("iso3"))
            if not par:
                continue
            sc = round(float(par.get("score", 0)), 6)
            if abs(float(r.get("score", 0)) - sc) > 1e-9:
                r["score"] = sc
                r["band"] = band_label(sc)
                _n_inh += 1
            r["inherited"] = True
        if _n_inh:
            warnings.append(f"re-synced {_n_inh} route-3 regions to their national score")
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
        # 2) national-score provenance, published per record
        for _iso, _c in countries.items():
            _m = (_c.get("derivedFrom") or {}).get("mode")
            if _m == "reaggregate":
                _n = (_c.get("divisionSpread") or {}).get("n")
                _c["scoreProvenance"] = (f"destination summary: mean of {_n} measured "
                                         f"divisions")
            elif _m == "mirror":
                _c["scoreProvenance"] = "mirrors the territory's own record"
            elif _c.get("aggregationBlocked"):
                _c["scoreProvenance"] = ("framework rating: no destination summary, because "
                                         "too many division estimates reached the index floor")
            else:
                _c["scoreProvenance"] = "framework rating (no measured division set)"
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
