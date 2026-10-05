#!/usr/bin/env python3
"""ILGA database news harvest (source category: ILGA).

Queries the public monitor API used by https://database.ilga.org/<country>-lgbti
for recent news articles per country, which ILGA curates for every jurisdiction.
Outputs data/ilga_news.json: {iso3: [article dicts]} with the article's external
link (url), headline (title), and snippet (content).

Usage:
  python3 tools/fetch_ilga_news.py [--only NER,MLT] [--out data/ilga_news.json]

The jurisdiction id space (UN-###) comes from the app's own GraphQL:
  POST https://database.ilga.org/graphql  {"query":"query { jurisdictions { id a2_code name slug } }"}
The article feed is public:
  GET https://monitor.ilga.org/api/articles/getDbLatestFromJur/<UN-id>
No auth. Rate-limit politely (200ms between fetches, 6 workers max).
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, json, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GT = "https://database.ilga.org/graphql"
FEED = "https://monitor.ilga.org/api/articles/getDbLatestFromJur/{}"
OUT = ROOT / "data" / "ilga_news.json"
JUR_CACHE = ROOT / "data" / "ilga_jurisdictions.json"


def gql(query: str) -> dict:
    req = urllib.request.Request(
        GT, data=json.dumps({"query": query}).encode(), method="POST",
        headers={"content-type": "application/json", "user-agent": "Mozilla/5.0 (research)"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def get_jurisdictions():
    if JUR_CACHE.exists():
        try:
            return json.loads(JUR_CACHE.read_text())
        except Exception:
            pass
    d = gql("query { jurisdictions { id a2_code name slug } }")
    out = {}
    for j in d["data"]["jurisdictions"]:
        out[j["a2_code"]] = {"id": j["id"], "name": j["name"], "slug": j["slug"]}
    JUR_CACHE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def iso3_to_iso2() -> dict:
    """ISO-3166-1 alpha-3 -> alpha-2 (embedded table; pycountry if present)."""
    try:
        import pycountry  # type: ignore
        return {c.alpha_3: c.alpha_2 for c in pycountry.countries}
    except Exception:
        pass
    i3 = """AFG ALB DZA ASM AND AGO AIA ATG ARG ARM ABW AUS AUT AZE BHS BHR BGD BRB BLR BEL
 BLZ BEN BMU BTN BOL BIH BWA BRA VGB BRN BGR BFA BDI KHM CMR CAN CPV CYM CAF TCD CHL
 CHN COL COM COG COK CRI CIV HRV CUB CUW CYP CZE DNK DJI DMA DOM ECU EGY SLV GNQ ERI
 EST SWZ ETH FLK FRO FJI FIN FRA GUF PYF GAB GMB GEO DEU GHA GIB GRC GRL GRD GLP GUM
 GTM GGY GIN GNB GUY HTI HND HKG HUN ISL IND IDN IRN IRQ IRL IMN ISR ITA JAM JPN JEY
 JOR KAZ KEN KIR KOS KWT KGZ LAO LVA LBN LSO LBR LBY LIE LTU LUX MAC MDG MWI MYS MDV
 MLI MLT MHL MTQ MRT MUS MYT MEX FSM MDA MCO MNG MNE MSR MAR MOZ MMR NAM NRU NPL NLD
 NCL NZL NIC NER NGA NIU PRK MKD NOR OMN PAK PLW PSE PAN PNG PRY PER PHL PCN POL PRT
 PRI QAT KOR ROU RUS RWA BLM SHN KNA LCA VCT WSM SMR STP SAU SEN SRB SYC SLE SGP SXM
 SVK SVN SLB SOM ZAF SSD ESP LKA SDN SUR SWE CHE SYR TWN TLS THA TGO TON TTO TUN TUR
 TKM TCA TUV UGA UKR ARE GBR USA URY VIR VUT VAT VEN VNM WLF YEM ZMB ZWE ESH XKX BES
 GUF""".split()
    i2 = """AF AL DZ AS AD AO AI AG AR AM AW AU AT AZ BS BH BD BB BY BE
 BZ BJ BM BT BO BA BW BR VG BN BG BF BI KH CM CA CV KY CF TD CL
 CN CO KM CG CK CR CI HR CU CW CY CZ DK DJ DM DO EC EG SV GQ ER
 EE SZ ET FK FO FJ FI FR GF PF GA GM GE DE GH GI GR GL GD GP GU GT
 GG GN GW GY HT HN HK HU IS IN ID IR IQ IE IM IL IT JM JP JE JO
 KZ KE KI XK KW KG LA LV LB LS LR LY LI LT LU MO MG MW MY MV ML
 MT MH MQ MR MU YT MX FM MD MC MN ME MS MA MZ MM NA NR NP NL NC
 NZ NI NE NG NU KP MK NO OM PK PW PS PA PG PY PE PH PN PL PT PR
 QA KR RO RU RW BL SH KN LC VC WS SM ST SA SN RS SC SL SG SX SK
 SI SB SO ZA SS ES LK SD SR SE CH SY TW TL TH TG TO TT TN TR TM
 TC TV UG UA AE GB US UY VI VU VA VE VN WF YE ZM ZW EH XK BQ GF""".split()
    if len(i3) != len(i2):
        raise RuntimeError(f"iso3_to_iso2 table mismatch {len(i3)} vs {len(i2)}")
    return dict(zip(i3, i2))


def fetch_feed(jid: str, retries: int = 5) -> list:
    import time
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(
                        FEED.format(jid),
                        headers={"user-agent": "Mozilla/5.0 (research)",
                                 "accept": "application/json"}),
                    timeout=90) as r:
                d = json.loads(r.read().decode())
            return d.get("msg") or []
        except Exception as e:  # noqa: BLE001
            if attempt == retries - 1:
                raise
            time.sleep(1.5 * (2 ** attempt))
    return []


def normalize(art: dict) -> dict:
    """Map ILGA monitor article dict -> {url, title, snippet, date?, source}.
    Observed keys: id, h (localized headline), th (translated), d (snippet),
    u (external url), l (lang), da (published), s (source name), c (country),
    st (Media Outlet / Government / etc.).
    """
    return {
        "url": art.get("u"),
        "title": (art.get("th") or art.get("h") or "").strip(),
        "snippet": (art.get("d") or "").strip(),
        "source": (art.get("s") or "").strip(),
        "published": art.get("da"),
        "kind": art.get("st"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma ISO2 or ISO3 list")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    jurs = get_jurisdictions()
    print(f"jurisdictions: {len(jurs)}")
    only = [x.strip().upper() for x in args.only.split(",") if x.strip()]
    picks = only or list(jurs)
    iso3m = iso3_to_iso2()
    # resolve any ISO-3 codes (from --only) to ISO-2 jurisdiction keys
    by_name = {m.get("name", "").lower(): i2 for i2, m in jurs.items()}
    by_slug = {m.get("slug", "").lower(): i2 for i2, m in jurs.items()}
    results = {}

    def work(code):
        iso2 = code
        if code not in jurs:
            iso2 = iso3m.get(code)
            if iso2 is None or iso2 not in jurs:
                iso2 = by_name.get(code.lower())
            if iso2 is None or iso2 not in jurs:
                iso2 = by_slug.get(code.lower())
            if iso2 is None or iso2 not in jurs:
                raise KeyError(f"no ILGA jurisdiction for {code!r}")
        meta = jurs[iso2]
        arts = fetch_feed(meta["id"])
        return iso2, [normalize(a) for a in arts]

    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        futs = []
        for code in picks:
            time.sleep(0.05)  # gentle pacing before scheduling
            futs.append(ex.submit(work, code))
        for i, fu in enumerate(futs, 1):
            try:
                iso2, arts = fu.result()
            except Exception as e:  # noqa: BLE001
                print(f"[ERR] {e}"); continue
            results[iso2] = arts
            print(f"[{i}/{len(futs)}] {iso2}: {len(arts)} articles", flush=True)

    Path(args.out).parent.mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(v) for v in results.values())
    print(f"\nwrote {args.out}: {len(results)} countries, {n} article stubs")


if __name__ == "__main__":
    main()