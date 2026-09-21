#!/usr/bin/env python3
"""Fill admin1 records for units lacking dossier-backed scores.

Route 2/3 of METHODOLOGY.md: best-knowledge estimates from the larger model,
encoded as a delta table relative to each parent's national score. Principles:

  - default delta 0.00: no inkling -> the national score IS the estimate
  - small deltas (±0.02-0.05) for soft signals (known conservatism, metros,
    resort enclaves, weak-governance regions)
  - large deltas only for genuine different-law / different-governance cases
    (sharia-emirate governance, active-war zones, autonomous stricter regions)
  - never crosses a parent's band edge without dossier-grade confidence
  - every record flagged estimated:true, source = the parent's own sources

Modes:
  default          fills units of NON-dossier countries (safe to run while the
                   dossier pipeline is active; never touches dossier countries)
  --dossier-tail   fills remaining unscored units of dossier countries
                   (run AFTER the scoring hand-off finishes a country)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DOSSIER_ISOS = {"USA", "MEX", "CAN", "GBR", "AUS", "BRA", "IND", "DEU", "ESP",
                "COL", "ARG", "ITA", "POL", "NGA", "IDN", "MYS", "TUR", "RUS",
                "ZAF", "FRA", "PHL", "PER", "CHL", "KOR"}

# (iso3, lowercase substring of unit name) -> (delta, reason)
# First matching entry wins; keep patterns specific enough to avoid collisions.
DELTAS: dict[str, list[tuple[str, float, str]]] = {
    # --- different law / different governance (large) ---
    "YEM": [
        ("sana'a", -0.03, "de facto authority operates a stricter moral-policing regime than the nominal national framework"),
        ("sanaa", -0.03, "de facto authority operates a stricter moral-policing regime than the nominal national framework"),
        ("amanat", -0.03, "capital under de facto authority; stricter moral policing"),
        ("aden", +0.02, "seat of the internationally recognised government; marginally more institutional order"),
        ("hadramawt", +0.01, "south-eastern governorate, more stable security than the west"),
        ("ta'izz", -0.01, "contested; fragmented control"),
        ("hodeidah", -0.01, "front-line governorate; fragmented control"),
        ("al hudaydah", -0.01, "front-line governorate; fragmented control"),
    ],
    "LBY": [
        ("benghazi", -0.03, "eastern command's governance is more arbitrary; detention risk higher"),
        ("derna", -0.04, "history of militia/insurgent control; least institutional order"),
        ("sirt", -0.03, "contested central coast; militia governance"),
        ("misrata", -0.02, "powerful local militias; weak central recourse"),
        ("tripoli", +0.02, "capital: diplomatic presence and the least-bad institutional cover"),
    ],
    "SOM": [
        ("awdal", +0.05, "part of the Somaliland administration: functioning government, no extremist control"),
        ("woqooyi", +0.05, "Somaliland administration (Hargeisa): functioning government"),
        ("toghdeer", +0.05, "Somaliland administration"),
        ("sanaag", +0.04, "largely Somaliland-administered"),
        ("sool", +0.03, "contested Somaliland/Khatumo/Puntland; partial administration"),
        ("bari", +0.02, "Puntland: semi-functional regional government"),
        ("nugaal", +0.02, "Puntland (Garowe): semi-functional regional government"),
        ("mudug", +0.01, "split Puntland/Galmudug; partial administration"),
        ("banadir", +0.01, "Mogadishu: federal government and AMISOM/ATMIS presence, though attacks continue"),
    ],
    "SDN": [
        ("khartoum", -0.03, "active urban warfare and competing security actors"),
        ("west darfur", -0.04, "RSF/Janjaweed-rule atrocities; least protection of anyone"),
        ("south darfur", -0.03, "active conflict zone"),
        ("central darfur", -0.03, "active conflict zone"),
        ("north darfur", -0.03, "active conflict zone"),
        ("east darfur", -0.03, "active conflict zone"),
        ("al jazirah", -0.02, "contested; RSF incursions documented"),
        ("kordofan", -0.02, "contested front regions"),
        ("red sea", +0.02, "Port Sudan: de facto administrative capital, relatively stable"),
    ],
    "SSD": [
        ("juba", +0.02, "capital: the only unit with meaningful institutional presence"),
        ("central equatoria", +0.02, "capital region"),
    ],
    "AFG": [
        ("kabul", +0.01, "capital: foreign presence marginally moderates, but the regime is uniform — near-floor everywhere"),
    ],
    "ARE": [
        ("dubai", +0.02, "most cosmopolitan emirate; largest tourist envelope and most international scrutiny"),
        ("abu dhabi", +0.01, "capital; diplomatic presence"),
        ("sharjah", -0.03, "public-decency enforcement notably stricter than the federal baseline"),
        ("ajman", -0.01, "conservative small emirate"),
        ("umm al", -0.01, "conservative small emirate"),
        ("ras al", -0.01, "conservative small emirate"),
        ("fujairah", -0.01, "conservative small emirate"),
    ],
    "CMR": [
        ("northwest", +0.03, "Anglophone common-law tradition and civil-society culture; but active armed conflict"),
        ("southwest", +0.03, "Anglophone common-law tradition; active armed conflict"),
        ("far north", -0.02, "Boko Haram-affected; security-arbitrary governance"),
        ("north", -0.02, "predominantly Muslim; morality enforcement climate stronger"),
        ("adamawa", -0.01, "predominantly Muslim north"),
        ("littoral", +0.01, "Douala: most cosmopolitan, largest civil-society presence"),
        ("centre", +0.01, "Yaoundé: capital, diplomatic presence"),
    ],
    "COD": [
        ("nord-kivu", -0.03, "active armed conflict; militia governance"),
        ("north kivu", -0.03, "active armed conflict; militia governance"),
        ("sud-kivu", -0.03, "active armed conflict; militia governance"),
        ("south kivu", -0.03, "active armed conflict; militia governance"),
        ("ituri", -0.03, "active armed conflict; militia governance"),
        ("kinshasa", +0.02, "capital: the only unit with organised community life and institutional presence"),
    ],
    "CAF": [
        ("bangui", +0.02, "capital: only unit with meaningful state/UN presence"),
        ("ombella", +0.01, "capital-adjacent"),
    ],
    "MMR": [
        ("nay pyi taw", -0.01, "junta capital; heaviest security presence"),
        ("yangon", +0.01, "largest city; biggest (underground) community and NGO remnants"),
        ("rakhine", -0.02, "active conflict; militia/army rule"),
        ("chin", -0.02, "active conflict zones"),
        ("kayah", -0.02, "active conflict zones"),
        ("shan", -0.01, "large contested areas"),
        ("kachin", -0.01, "large contested areas"),
        ("mon", +0.01, "relatively stable south-east"),
    ],
    "HTI": [
        ("ouest", +0.01, "Port-au-Prince: gang control is severe but international presence concentrates here"),
        ("artibonite", -0.02, "gang territorial control expanding; least state presence"),
        ("centre", -0.01, "weak state presence"),
    ],
    "UKR": [
        ("kyiv", +0.02, "capital: visible community, Pride events under martial-law limits, best services"),
        ("lviv", +0.01, "western city with active civil society"),
        ("odessa", +0.01, "large city with historically visible scene"),
        ("kharkiv", +0.01, "large city, active NGOs"),
        ("crimea", -0.44, "Russian occupation: federal Russian anti-LGBT law and enforcement apply in full (propaganda law, 'extremist movement' designation). De jure Ukraine, but a visitor faces the Russian regime; scored toward RUS national, not UKR national"),
        ("donetsk", -0.40, "occupied/war zones: Russian-appointed authorities apply Russian law plus wartime arbitrariness; scored toward RUS national"),
        ("luhansk", -0.40, "occupied/war zones: Russian-appointed authorities apply Russian law plus wartime arbitrariness; scored toward RUS national"),
        ("zaporizhzhia", -0.01, "front-line region"),
        ("kherson", -0.01, "front-line region"),
    ],
    "ECU": [
        ("guayas", -0.02, "Guayaquil: worst gang-violence concentration; extortion economy"),
        ("esmeraldas", -0.02, "highest violence rates; weak state control"),
        ("manabi", -0.01, "high-violence coastal province"),
        ("los rios", -0.01, "high-violence province"),
        ("pichincha", +0.01, "Quito: capital institutions, organised community"),
        ("azuay", +0.01, "Cuenca: calmer, large expat presence"),
        ("galapagos", +0.01, "tourism-governed islands"),
    ],
    "PAK": [
        ("khyber pakhtunkhwa", -0.03, "most socially conservative province; strong religious-party influence"),
        ("tribal", -0.03, "former FATA: customary/jirga justice"),
        ("balochistan", -0.02, "insurgency and heavy security rule; least recourse"),
        ("sindh", +0.02, "Karachi: largest (underground) scene, more cosmopolitan; interior Sindh is conservative"),
        ("islamabad", +0.02, "capital: diplomatic enclave effect"),
        ("punjab", 0.0, "national baseline; Lahore marginally more cosmopolitan but the province averages out"),
        ("gilgit", -0.01, "conservative mountain region"),
        ("azad jammu", -0.01, "conservative; contested-region administration"),
    ],
    "BGD": [
        ("dhaka", +0.02, "capital: the only unit with an organised (underground) community"),
        ("chittagong", 0.0, "second city; national baseline"),
    ],
    "MRT": [
        ("nouakchott", +0.01, "capital: diplomatic presence marginally moderates; near-floor everywhere"),
    ],
    "DZA": [
        ("algiers", +0.01, "capital: largest (hidden) scene, more anonymity"),
        ("oran", +0.01, "second city, historically more cosmopolitan"),
        ("ghardaia", -0.02, "M'zab valley: Ibadi religious customary governance, notably strict"),
        ("adrar", -0.01, "deep south; conservative"),
        ("tamanrasset", -0.01, "deep south; conservative"),
        ("bechar", -0.01, "deep south; conservative"),
    ],
    "TUN": [
        ("tunis", +0.01, "capital: the only unit with organised community life"),
    ],
    "MAR": [
        ("casablanca", +0.01, "largest city; most anonymity"),
        ("rabat", +0.01, "capital; diplomatic presence"),
        ("marrakech", +0.02, "international tourism infrastructure is a partial envelope"),
        ("tanger", +0.01, "tangier: historically cosmopolitan port"),
        ("tangier", +0.01, "historically cosmopolitan port"),
    ],
    "JOR": [
        ("amman", +0.02, "capital: where essentially all tolerated scene and services exist"),
        ("aqaba", +0.01, "special economic zone; tourism envelope"),
        ("ma'an", -0.02, "most conservative south"),
        ("zarqa", -0.01, "conservative; strong islamist current"),
        ("irbid", -0.01, "conservative north"),
    ],
    "EGY": [
        ("cairo", +0.01, "capital: scene exists underground; entrapment risk concentrates here too, net marginal plus"),
        ("alexandria", 0.0, "second city; national baseline"),
        ("north sinai", -0.02, "active military operation zone"),
        ("south sinai", +0.02, "Sharm el-Sheikh resort envelope"),
        ("red sea", +0.02, "Hurghada resort envelope"),
    ],
    "ETH": [
        ("addis ababa", +0.02, "capital: diplomatic city, only unit with any scene"),
        ("somali", -0.02, "regional customary/religious enforcement stronger than federal baseline"),
        ("afar", -0.01, "conservative; sparse state presence"),
        ("amhara", -0.01, "active conflict zones; church influence strong"),
        ("tigray", -0.01, "post-war reconstruction; weak institutions"),
    ],
    "KEN": [
        ("nairobi", +0.02, "capital: organised community, services, most court-access"),
        ("mombasa", +0.01, "coastal tourism economy; but conservative coastal society — net small plus"),
        ("coast", +0.01, "tourism envelope"),
        ("north eastern", -0.02, "predominantly Somali-Muslim; security-operation governance"),
        ("garissa", -0.02, "predominantly Somali-Muslim; security-operation governance"),
        ("mandera", -0.02, "predominantly Somali-Muslim; security-operation governance"),
    ],
    "NGA": [  # dossier country — deltas only as fallback if Qwen's coverage misses them
        ("kaduna", -0.04, "northern sharia-criminal-law state"),
        ("kano", -0.04, "northern sharia-criminal-law state"),
        ("sokoto", -0.04, "northern sharia-criminal-law state"),
        ("zamfara", -0.04, "northern sharia-criminal-law state; banditry"),
        ("kebbi", -0.04, "northern sharia-criminal-law state"),
        ("katsina", -0.04, "northern sharia-criminal-law state"),
        ("jigawa", -0.04, "northern sharia-criminal-law state"),
        ("bauchi", -0.04, "northern sharia-criminal-law state"),
        ("yobe", -0.04, "sharia state; insurgency-affected"),
        ("borno", -0.04, "sharia state; insurgency epicentre"),
        ("niger", -0.03, "sharia state (NGN Niger State)"),
        ("gombe", -0.03, "sharia state"),
        ("adamawa", -0.03, "sharia state (per dossier correction: criminal provisions apply)"),
        ("taraba", -0.03, "sharia state (per dossier correction: criminal provisions apply)"),
        ("lagos", +0.02, "largest scene, most anonymity; still SSMAA-arrest jurisdiction"),
        ("federal capital", +0.02, "Abuja: diplomatic presence"),
    ],
    "IDN": [
        ("aceh", -0.11, "provincial sharia criminal law with caning for same-sex intimacy (dossier-confirmed; Qwen record takes precedence if present)"),
        ("bali", +0.03, "Hindu-majority; international tourism envelope"),
        ("jakarta", +0.01, "capital: largest scene and services"),
        ("yogyakarta", +0.01, "student city; more tolerant climate"),
    ],
    "MYS": [
        ("kelantan", -0.04, "state sharia enforcement most active (dossier country; Qwen precedence)"),
        ("terengganu", -0.04, "state sharia enforcement active"),
        ("kedah", -0.02, "conservative state"),
        ("pahang", -0.02, "conservative state"),
        ("perak", -0.01, "conservative state"),
        ("kuala lumpur", +0.02, "federal capital: scene concentrates, more anonymity"),
        ("penang", +0.01, "urban, more cosmopolitan"),
        ("selangor", +0.01, "most urbanised state"),
        ("sabah", +0.01, "east Malaysia: less religiously policed"),
        ("sarawak", +0.01, "east Malaysia: less religiously policed"),
    ],
    "TZA": [  # Zanzibar records already exist from the exceptions pass
        ("dar es salaam", +0.01, "largest city; community presence"),
    ],
    "VEN": [
        ("distrito capital", +0.01, "Caracas: the only unit with visible scene"),
        ("miranda", +0.01, "greater Caracas"),
    ],
    "LBN": [
        ("beyrouth", +0.02, "Beirut: nearly all tolerated scene lives here"),
        ("beirut", +0.02, "nearly all tolerated scene lives here"),
        ("mont liban", +0.01, "Mount Lebanon: Beirut orbit"),
        ("nabatiye", -0.01, "south: stronger party/religious governance"),
    ],
    "IRQ": [  # KRG records already exist from the exceptions pass
        ("baghdad", 0.0, "capital; national baseline of severe risk"),
        ("basrah", -0.01, "south: militia/religious governance stronger"),
    ],
    "UZB": [
        ("tashkent", +0.01, "capital: services and anonymity concentrate here"),
    ],
    "KAZ": [
        ("almaty", +0.02, "most liberal city; scene and NGOs concentrate"),
        ("astana", +0.01, "capital; diplomatic presence"),
        ("mangystau", -0.01, "western oil region; more conservative"),
    ],
    "KGZ": [
        ("bishkek", +0.02, "capital: NGOs (Kyrgyz Indigo) operate here; relative anonymity"),
        ("osh", -0.02, "south: markedly more conservative and religious"),
        ("jalal", -0.01, "south: more conservative"),
        ("batken", -0.01, "south: more conservative"),
    ],
    "TJK": [
        ("dushanbe", +0.01, "capital: only place any infrastructure exists"),
        ("gorno", -0.01, "Badakhshan: distinct Ismaili region; state suspicion high after 2022 unrest"),
    ],
    "GEO": [
        ("tbilisi", +0.02, "capital: nearly all community life; still high-risk nationally"),
        ("adjara", -0.01, "Batumi: more religious-conservative region"),
    ],
    "ARM": [
        ("yerevan", +0.02, "capital: essentially all community life (Pink Armenia, Right Side)"),
    ],
    "AZE": [
        ("baku", +0.01, "capital: only place any scene exists (underground)"),
    ],
    "BLR": [
        ("minsk", +0.01, "capital: only place any (exiled-remnant) infrastructure existed"),
    ],
    "CUB": [
        ("la habana", +0.01, "Havana: CENESEX and the visible scene"),
        ("habana", +0.01, "Havana province orbit"),
    ],
    "BOL": [
        ("la paz", +0.01, "seat of government; community organisations"),
        ("cochabamba", +0.01, "strongest trans-organisation base (Famitrans lineage)"),
        ("santa cruz", -0.01, "most socially conservative/religious lowland region"),
    ],
    "PRY": [
        ("asuncion", +0.01, "capital: only organised community"),
        ("alto parana", -0.01, "border region; weaker institutions"),
    ],
    "GUY": [
        ("demerara", +0.01, "Georgetown: SASOD and the whole scene"),
    ],
    "SUR": [
        ("paramaribo", +0.01, "capital: essentially the whole country for a visitor"),
    ],
    "GHA": [
        ("greater accra", +0.01, "capital region: NGOs and anonymity"),
        ("ashanti", -0.01, "Kumasi: socially conservative heartland"),
        ("northern", -0.01, "more conservative north"),
    ],
    "CIV": [
        ("abidjan", +0.01, "economic capital: scene and anonymity; the 2024 hunt-wave violence happened here too — net neutral-plus"),
        ("denguele", -0.01, "conservative north"),
        ("savanes", -0.01, "conservative north"),
    ],
    "SEN": [
        ("dakar", +0.01, "capital: underground scene and anonymity despite arrests"),
    ],
    "MDG": [
        ("ananalanjirofo", 0.0, "national baseline"),
        ("antananarivo", +0.01, "capital: only unit with any scene"),
    ],
    "NPL": [
        ("bagmati", +0.01, "Kathmandu valley: meti/third-gender organising and services"),
    ],
    "LKA": [
        ("western", +0.01, "Colombo: all community infrastructure and relative anonymity"),
        ("northern", -0.01, "post-war militarised; conservative"),
        ("eastern", -0.01, "conservative; heavy security presence"),
    ],
    "VNM": [
        ("ho chi minh", +0.01, "largest city; most visible scene"),
        ("ha noi", +0.01, "capital; Hanoi and HCMC are where NGOs operate"),
    ],
    "KHM": [
        ("phnom penh", +0.01, "capital: NGOs, scene, tourism infrastructure"),
        ("siem reap", +0.01, "tourism economy envelope"),
    ],
    "LAO": [
        ("vientiane", +0.01, "capital: the only expat/tourism envelope"),
    ],
    "PNG": [
        ("national capital", +0.01, "Port Moresby: relative to a near-floor baseline, the only institutional presence"),
    ],
    "FJI": [
        ("rewa", +0.01, "Suva: Haus of Khameleon and the organised community"),
    ],
    "DOM": [
        ("distrito nacional", +0.01, "Santo Domingo: community and anonymity"),
        ("la altagracia", +0.02, "Punta Cana resort envelope"),
        ("puerto plata", +0.01, "resort north coast"),
    ],
    "JAM": [
        ("kingston", 0.0, "capital; national baseline of severe mob risk"),
        ("st. james", +0.01, "Montego Bay tourism envelope"),
        ("saint james", +0.01, "Montego Bay tourism envelope"),
    ],
    "BHS": [
        ("new providence", +0.01, "Nassau: tourism economy"),
    ],
    "MDV": [
        ("male", -0.01, "capital island: local-island norms, no resort envelope"),
        ("alifu", +0.03, "resort atolls: documented de-facto tourist insulation"),
        ("baa", +0.03, "resort atolls"),
        ("dhaalu", +0.03, "resort atolls"),
        ("faafu", +0.03, "resort atolls"),
        ("kaafu", +0.03, "resort atolls (incl. Malé-adjacent resorts)"),
        ("lhaviyani", +0.03, "resort atolls"),
        ("meemu", +0.03, "resort atolls"),
        ("noonu", +0.03, "resort atolls"),
        ("raa", +0.03, "resort atolls"),
        ("seenu", +0.01, "Addu: urban-ish, mixed"),
        ("shaviyani", +0.03, "resort atolls"),
        ("thaa", +0.03, "resort atolls"),
        ("vaavu", +0.03, "resort atolls"),
    ],
    "SYC": [
        ("la digue", +0.01, "tourism islands; national score already tourism-based"),
    ],
    "MUS": [
        ("plaines wilhems", +0.01, "urban centre (Curepipe/Quatre Bornes); most anonymity"),
        ("port louis", +0.01, "capital"),
    ],
    "SWZ": [
        ("hohho", +0.01, "Mbabane: institutions and the Pride-organising base"),
    ],
    "LSO": [
        ("maseru", +0.01, "capital: Rainbow Alliance base"),
    ],
    "BWA": [
        ("south east", +0.01, "Gaborone: courts, LEGABIBO, everything"),
        ("kgatleng", +0.01, "Gaborone orbit"),
    ],
    "NAM": [
        ("khomas", +0.01, "Windhoek: Equal Namibia, courts, everything"),
    ],
    "AGO": [
        ("luanda", +0.01, "capital: the whole organised community"),
        ("cabinda", -0.01, "exclave; separatist tension, heavy security"),
    ],
    "MOZ": [
        ("cidade de maputo", +0.01, "capital: Lambda and the scene"),
        ("maputo", +0.01, "capital province orbit"),
        ("cabo delgado", -0.02, "insurgency zone"),
    ],
    "ZMB": [
        ("lusaka", +0.01, "capital: NGOs and relative anonymity"),
    ],
    "ZWE": [
        ("harare", +0.01, "capital: GALZ base"),
        ("bulawayo", 0.0, "second city; national baseline"),
    ],
    "MWI": [
        ("lilongwe", +0.01, "capital: the case-law and NGO base"),
        ("blantyre", +0.01, "commercial capital; southern region more socially conservative but institutions net plus"),
    ],
    "RWA": [
        ("kigali", 0.0, "capital: sweep operations documented here specifically; scene also here — nets to baseline"),
    ],
    "UGA": [
        ("kampala", +0.01, "capital: underground scene and services despite the Act"),
    ],
    "SGP": [  # city-state: units get baseline
    ],
    "BRN": [
        ("brunei and muara", +0.01, "capital district; diplomatic presence"),
    ],
    "TLS": [
        ("dili", +0.01, "capital: CODIVA, Pride, everything"),
    ],
    "MNG": [
        ("ulaanbaatar", +0.01, "capital: LGBT Centre and essentially all community life"),
    ],
    "BTN": [
        ("thimphu", +0.01, "capital: Pride Bhutan / Rainbow Bhutan base"),
    ],
    "PAN": [
        ("panama", +0.01, "capital province: the organised community"),
        ("colon", -0.01, "higher crime; weaker institutions"),
    ],
    "CRI": [
        ("san jose", +0.01, "capital: institutions and scene"),
        ("guanacaste", +0.01, "tourism coast; international envelope"),
        ("limon", -0.01, "higher crime; weaker institutional reach"),
    ],
    "GTM": [
        ("guatemala", +0.01, "capital: Lambda and the scene"),
    ],
    "SLV": [
        ("san salvador", +0.01, "capital: the whole organised community"),
    ],
    "HND": [
        ("francisco morazan", +0.01, "Tegucigalpa: institutions"),
        ("cortes", +0.01, "San Pedro Sula: Cattrachas-lineage organising"),
    ],
    "NIC": [
        ("managua", +0.01, "capital: the only (exiled-remnant) infrastructure"),
    ],
    "COL": [
        ("bogota", +0.01, "capital: institutions (dossier country; Qwen precedence)"),
    ],
}

FALLBACK_NOTE = ("No sub-national signal was identified; scored at the national level. "
                 "Model estimate (route 3): deviation from the national score is zero "
                 "where no reliable sub-national knowledge exists.")


def reason_note(reason: str, parent_name: str, national: float) -> str:
    return (f"Model estimate (route 3, best-knowledge delta): {reason}. "
            f"Scored relative to the national score ({national:.2f}) for {parent_name}.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dossier-tail", action="store_true",
                    help="also fill unscored units of the 24 dossier countries "
                         "(run only after their scoring hand-off has merged)")
    ap.add_argument("--only", nargs="*", default=None, help="restrict to these ISO3s")
    ap.add_argument("--out", default=None,
                    help="write to this staging file instead of data/admin1.json "
                         "(merge into admin1.json when pairwise runs are idle)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    geo = json.loads((ROOT / "boundaries" / "admin1.geojson").read_text(encoding="utf-8"))
    countries = json.loads((ROOT / "data" / "countries.json").read_text(encoding="utf-8"))
    admin1_path = ROOT / "data" / "admin1.json"
    admin1 = json.loads(admin1_path.read_text(encoding="utf-8")) if admin1_path.exists() else {}
    out_path = Path(args.out) if args.out else admin1_path
    staged = {} if args.out else admin1  # staging file starts empty

    from build_data import band_label  # local import path
    n_new = n_skip = n_delta = 0
    per_country = {}
    for f in geo["features"]:
        p = f["properties"]
        iso, sid, name = p["iso3"], p["shapeID"], p["name"]
        if args.only and iso not in {o.upper() for o in args.only}:
            continue
        if iso in DOSSIER_ISOS and not args.dossier_tail:
            continue
        if sid in admin1:
            n_skip += 1
            continue
        parent = countries.get(iso)
        if parent is None:
            print(f"warn: no country record for {iso}", file=sys.stderr)
            continue
        nat = float(parent["score"])
        delta, reason = 0.0, None
        lname = name.lower()
        for pat, d, r in DELTAS.get(iso, []):
            if pat in lname:
                delta, reason = d, r
                break
        score = round(min(1.0, max(0.0, nat + delta)), 4)
        if abs(score - nat) >= 0.095 and not reason:
            score = nat  # never let rounding drift a band silently
        summary = ("<p>" + reason_note(reason, parent["name"], nat) + "</p>"
                   if reason else "<p>" + FALLBACK_NOTE + "</p>")
        srcs = parent.get("sources", [])
        src_urls = [s["url"] if isinstance(s, dict) else s for s in srcs][:3]
        (staged if args.out else admin1)[sid] = {
            "iso3": iso, "name": name, "score": score,
            "band": band_label(score), "summary": summary,
            "sources": src_urls or ["https://outrightinternational.org/"],
            "researchedAt": "2026-09-21", "estimated": True,
        }
        n_new += 1
        if reason:
            n_delta += 1
        per_country[iso] = per_country.get(iso, 0) + 1

    print(f"new records: {n_new} ({n_delta} with knowledge deltas) · "
          f"skipped existing: {n_skip} · countries touched: {len(per_country)}")
    if args.dry_run:
        print("dry run — nothing written")
        return 0
    target = staged if args.out else admin1
    tmp = out_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(target, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(out_path)
    print(f"wrote {len(target)} records to {out_path}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools"))
    sys.exit(main())
