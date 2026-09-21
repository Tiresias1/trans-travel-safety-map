#!/usr/bin/env python3
"""Seed data/admin1.json: USA (51 units, hand-scored from research/admin1/USA.md)
plus different-legal-system exception records (CHN Xinjiang/Tibet, TZA Zanzibar,
IRQ Kurdistan) as flagged estimates. One-shot script; kept for auditability."""
import json

gj = json.load(open('boundaries/admin1.geojson'))
units = {}  # (iso3, name) -> shapeID
by_iso = {}
for f in gj['features']:
    p = f['properties']
    units[(p['iso3'], p['name'])] = p['shapeID']
    by_iso.setdefault(p['iso3'], []).append(p)

countries = json.load(open('data/countries.json'))
USA_NAT = countries['USA']['score']
DATE = '2026-09-17'

def rec(iso, name, score, summary, sources, estimated=False, oos=None):
    sid = units[(iso, name)]
    r = {
        'iso3': iso, 'name': name, 'score': score,
        'summary': summary, 'sources': sources, 'researchedAt': DATE,
        'estimated': estimated,
    }
    if oos:
        r['outOfScopeNotes'] = oos
    return sid, r

out = {}

def add(iso, name, score, summary, sources, **kw):
    sid, r = rec(iso, name, score, summary, sources, **kw)
    assert sid not in out, f"duplicate {name}"
    out[sid] = r

S = {}  # shorthand source sets
S['map'] = 'https://mapresearch.org/equality-map/bans-on-transgender-people-using-public-bathroom-and-facilities-according-to-their-gender-identity/'
S['stone'] = 'https://www.stonewallnews.net/anti-trans-national-legal-risk-assessment-map-july-2026/'
S['needle'] = 'https://theneedlenews.com/2026/07/safe-states-dont-make-safer-people/'
S['erin5d'] = 'https://www.erininthemorning.com/p/anti-trans-national-legal-risk-assessment-a5d'
S['glaad'] = 'https://glaad.org/releases/glaad-alert-desk-documents-more-than-1000-anti-lgbtq-incidents-nationwide-in-2025/'

nat = f"national score {USA_NAT:.2f}"

# ---- worst tier: criminal exposure, enforcement, violence ----
add('USA', 'Idaho', 0.24,
 f"<p>The strictest criminal facility ban in the country: HB 752 (effective 1 July 2026) makes it a crime — misdemeanour up to 1 year, felony up to 5 years on a second offence within five years — for a trans person to use a restroom or changing room matching their gender identity in government buildings <em>and all private businesses open to the public</em> (gas stations, restaurants, hospitals). A federal court partially blocked it, but it remains in effect wherever no gender-neutral option exists. Four successive legislative rounds (2023–2026) plus a pride-flag ban; rated \u201cDo Not Travel\u201d in the July 2026 legal-risk assessment. Well below the {nat}.</p>",
 ['https://www.acluidaho.org/legislation/2026-hb-752-criminalizing-bathroom-use-for-trans-people/',
  'https://apnews.com/article/idaho-legislature-transgender-bathroom-ban-jail-ee10cda1df43979e0cf92cb73352187e',
  'https://19thnews.org/2026/04/idaho-transgender-bathroom-ban-lawsuit/', S['stone']])
add('USA', 'Louisiana', 0.24,
 f"<p>The highest measured killing rate in the country (24.7 per 100k trans women/yr) and a damning institutional response: after a mob of ~10 beat a trans couple outside a women's restroom in Benton (May 2026), no alleged attacker was arrested and <em>both victims were criminally charged</em>, one booked into a men's facility. The same parish municipality moved to criminalise trans restroom use by local ordinance — the sharpest instrument in a state with no statewide adult ban. A trans inmate was killed at Angola state prison (2024); killings continue into 2026. Well below the {nat}.</p>",
 [S['needle'], 'https://www.metroweekly.com/2026/08/louisiana-trans-couple-charged-mob-attack/',
  'https://www.erininthemorning.com/p/trans-couple-brutalized-at-louisiana',
  'https://www.hrc.org/news/honoring-yella-robert-clark-jr-transgender-inmate-killed-in-louisiana'])
add('USA', 'Texas', 0.25,
 f"<p>The facility ban (SB 8, effective Dec 2025) is <em>actually enforced</em>: within 48 hours, state troopers checked IDs at women's restrooms in the Capitol and issued criminal-trespass warnings to four trans women with one-year Capitol bans; the AG has since opened enforcement inquiries against a school district (escalated April 2026) and a university student was formally investigated. Highest absolute toll of killings of trans women in the country (44 recorded 2008–2025; 7.6 per 100k/yr); 66 anti-LGBTQ incidents in 2025 (3rd-highest). Rated \u201cDo Not Travel.\u201d Well below the {nat}.</p>",
 ['https://www.texastribune.com/2025-12-12/texas-bathroom-bill-implementation-policy-capitol/',
  'https://www.kxan.com/lgbtq/dps-gives-1-year-ban-to-4-transgender-women-after-capitol-rally-against-restroom-law/',
  'https://austincurrent.org/2026-04-27/austin-aisd-bathroom-law-texas-investigation/', S['needle'], S['stone']])
add('USA', 'Tennessee', 0.26,
 f"<p>The only state with a standing <em>criminal ban on gender-expressive performance</em>: the Adult Entertainment Act (2023) criminalises \u201cmale or female impersonation\u201d in public or where a child might be present — settled law after the 6th Circuit reversed the invalidating ruling (July 2024) and SCOTUS denied review (Feb 2025), so it is enforceable against a visitor presenting in drag. A 2019 amendment widened the indecent-exposure statute; 7.8 killings per 100k trans women/yr, above the general US homicide rate. Below the {nat}.</p>",
 ['https://legalclarity.org/tennessee-drag-ban-rules-penalties-and-legal-status/',
  'https://apnews.com/article/tennessee-drag-ban-1bd25d455d13f81c0cab43674a054dd9',
  'https://www.advocate.com/news/tennessee-drag-ban-supreme-court', S['needle']])
add('USA', 'Kansas', 0.26,
 f"<p>SB 244 (enacted Feb 2026 over the governor's veto) confines trans people to birth-sex facilities in government buildings and creates a private right of action letting anyone sue a person they suspect of violating it for ~$1,000 — a bounty-hunter mechanism that exposes visitors directly. It also invalidates Kansas-issued IDs with corrected markers. First state designated \u201cDo Not Travel\u201d in the current assessment cycle; two trans men sued within days citing fear of violence. Below the {nat}.</p>",
 ['https://www.aclukansas.org/publications/sb244faq/', S['stone'], S['erin5d'],
  'https://kansasreflector.com/2026-02-27/trans-men-file-lawsuit-over-kansas-law-that-restricts-bathroom-use-and-invalidates-drivers-licenses/'])
add('USA', 'Mississippi', 0.27,
 f"<p>Facility bans enacted 2024 and 2025 and a statutory birth-sex definition place it in the worst-law group. One important counterweight: the justice system does prosecute — the killer of a trans woman in Lucedale received 49 years in federal prison for a bias-motivated murder, positive evidence about institutional response rather than about risk level. Below the {nat}.</p>",
 [S['map'], S['stone'], 'https://www.justice.gov/usao-sdms/pr/mississippi-man-sentenced-49-years-prison-bias-motivated-murder-transgender-woman'])
add('USA', 'Oklahoma', 0.27,
 f"<p>Facility bans 2022 and 2025 plus a statutory birth-sex definition of \u201csex.\u201d Large parts of the state are Public Law 280 tribal jurisdiction, where gender-recognition law varies by nation and cannot be scored at this level. Below the {nat}.</p>",
 [S['map'], 'https://lgbtmap.medium.com/lgbtq-equality-maps-updates-april-2025-692ce11cd61f', S['stone']])
add('USA', 'Alabama', 0.27,
 f"<p>Facility bans 2022 and 2024, with the \u201cDon't Say Gay\u201d law extending bathroom restrictions to college campuses; 3.8 killings per 100k trans women/yr. Below the {nat}.</p>",
 [S['map'], S['stone'], S['needle']])
add('USA', 'Indiana', 0.27,
 f"<p>2026 criminal-penalty and ID laws placed it \u201camong the harshest anti-trans states\u201d in the February 2026 assessment; criminal-charge exposure for bathroom use has been flagged since 2023, and it appears on the 2026 enacted-lists (flagged: that tracker renders client-side and could not be re-verified at the URL). Below the {nat}.</p>",
 [S['erin5d'], 'https://www.findlaw.com/lgbtq-law/transgender-people-and-bathroom-access-laws.html'])
add('USA', 'Utah', 0.28,
 f"<p>First state to criminalise adult restroom use (HB 257, 2024) — not just school facilities — and first to explicitly prohibit LGBTQ flags at government buildings and schools (May 2025, fines up to $500/day). Below the {nat}.</p>",
 ['https://www.nytimes.com/2024-01-31/us/utah-bathroom-ban-transgender.html',
  'https://www.theguardian.com/us-news/2025/may/29/pride-month-trump'])
for st, sc, extra in [
    ('North Dakota', 0.28, 'HB 1259 (2025) facility ban; birth-sex definition in statute.'),
    ('South Dakota', 0.28, '2025 facility ban; birth-sex definition in statute.'),
    ('Wyoming', 0.28, 'Two facility bills signed March 2025; birth-sex definition in statute.'),
    ('West Virginia', 0.28, 'March 2025 facility ban with unusually wide reach: K-12, higher education, corrections and domestic-violence shelters.'),
    ('Arkansas', 0.29, 'HB 1156 (2023, K-12 facilities) extended 2025. School-focused, so traveler exposure is narrower than in adult-reaching bans.'),
    ('Ohio', 0.29, '2024 facility ban.'),
    ('Iowa', 0.29, 'Facility ban enacted; appears on 2026 enacted-lists (flagged: client-side tracker, not re-verifiable at URL).'),
]:
    add('USA', st, sc, f"<p>{extra} In the worst-law group per the July 2026 legal-risk assessment. Below the {nat}.</p>",
        [S['map'], S['stone']] + ([S['needle']] if st == 'Iowa' else []))
add('USA', 'South Carolina', 0.30,
 f"<p>2024 facility ban expanded in 2026 to colleges and universities, raising its tier to \u201cWorst Laws Passed\u201d in the July 2026 assessment; part of the 18-state birth-sex-definition group. Below the {nat}.</p>",
 [S['stone'], 'https://www.aclusc.org/press-releases/aclu-sc-responds-to-governor-signing-anti-trans-bathroom-bill/'])
add('USA', 'Florida', 0.31,
 f"<p>§ 553.865 (2023) makes refusing to leave a facility not matching sex assigned at birth — after being told by a government employee — criminal trespass in state-owned buildings. Produced what is believed to be the first arrest under a state trans bathroom law (March 2025, Capitol, held ~24h; charges later dismissed on a technicality — a mixed-leaning-positive institutional response). The state stopped issuing corrected-marker licences and treats \u201cmisrepresentation\u201d as potential fraud; Equality Florida and HRC issued named travel advisories. Physical safety is comparatively better than the law suggests: 3.7 killings per 100k trans women/yr, below the worst-law average. Below the {nat}.</p>",
 ['https://www.aclufl.org/know-your-rights/know-your-rights-floridas-public-restroom-changing-facility-ban/',
  'https://www.nbcnews.com/nbc-out/out-news/trans-students-arrest-violating-florida-bathroom-law-thought-first-rcna199697',
  'https://www.metroweekly.com/2025/07/judge-drops-trans-bathroom-case/',
  'https://www.eqfl.org/florida-travel-advisory', S['needle']])
add('USA', 'Nebraska', 0.32,
 f"<p>Gubernatorial executive order narrowing \u201cmale\u201d/\u201cfemale\u201d and ending state recognition of trans people — mostly resident-facing, but it signals an administration willing to use state machinery against gender identity. Below the {nat}.</p>",
 ['https://thehill.com/homenews/lgbtq/4181212-nebraska-governor-signs-executive-order-narrowing-definition-of-male-and-female'])
add('USA', 'Kentucky', 0.32,
 f"<p>2023 K-12 facility ban; school-focused, so direct traveler exposure is limited, but it places the state in the banning group. Below the {nat}.</p>",
 [S['map'], 'https://www.findlaw.com/lgbtq-law/transgender-people-and-bathroom-access-laws.html'])
add('USA', 'North Carolina', 0.32,
 f"<p>The archetype of this tier's instability: HB 2 (2016) restricted bathrooms to birth-certificate sex and was repealed in 2017 after mass backlash, but a binary-\u201csex\u201d statute remains and 12 killings are recorded (6.4 per 100k trans women/yr, above the general homicide rate). Below the {nat}.</p>",
 ['https://www.findlaw.com/lgbtq-law/transgender-people-and-bathroom-access-laws.html', S['needle']])
add('USA', 'Montana', 0.33,
 f"<p>HB 121 (2025) facility ban plus a pride-flag ban — <em>but</em> laws that would normally place it among the worst states have repeatedly been blocked in court, and it was the one state improving in the February 2026 assessment. Statutory risk is high; enforcement risk is genuinely mixed. Slightly below the {nat}.</p>",
 [S['stone'], S['erin5d']])
add('USA', 'Missouri', 0.33,
 f"<p>Bans gender-affirming care for incarcerated adults as well as minors (resident-facing, but signals institutional posture); no adult facility ban recorded. Slightly below the {nat}.</p>",
 ['https://www.pbs.org/newshour/politics/judge-denies-request-to-halt-missouris-gender-affirming-medical-care-ban'])
add('USA', 'Alaska', 0.33,
 f"<p>Moderate tier in the July 2026 assessment: no adult facility ban recorded, no protective statute. Slightly below the {nat}.</p>",
 [S['stone']])
add('USA', 'Georgia', 0.34,
 f"<p>No state facility ban, but Atlanta is a long-run concentration point for killings of trans people (≥15 fatal cases 1990–2014, 16 more 2015–2023; 4.8 per 100k trans women/yr), and Columbus Pride cancelled its 2026 Diversity Saturday because it could not secure off-duty officers — security forces unwilling to be visibly associated. Slightly below the {nat}.</p>",
 ['https://digitalcommons.law.uga.edu/cgi/viewcontent.cgi?article=1049&context=gclr', S['needle'],
  'https://www.ledger-enquirer.com/news/politics-government/article315548301.html'])
add('USA', 'New Hampshire', 0.34,
 f"<p>Highest per-capita incident load in the country: 72 recorded anti-LGBTQ incidents in 2025 in a state of ~1.4m. Counterweight: in July 2026 a county court found an attacker violated the NH Civil Rights Act after striking a trans gas-station employee, using his pronoun refusal as bias evidence, with bodycam showing officers correcting his pronoun use — institutions working. Slightly below the {nat}.</p>",
 [S['glaad'], 'https://www.nhpr.org/nh-news/2026-07-17/court-concord-man-violated-civil-rights-act-striking-transgender-woman'])

# ---- middle: low-risk tier, no specialisation ----
add('USA', 'Arizona', 0.38,
 f"<p>\u201cLow Risk\u201d tier in the July 2026 assessment — largely refrains from targeting trans adults without specialising in protection; Tucson cancelled its 2026 Pride citing the political and financial climate. Appears on 2026 enacted-lists (flagged: client-side tracker). Around the {nat}.</p>",
 [S['stone'], 'https://prismreports.org/2026/06/03/where-pride-wont-be-happening-this-year/'])
add('USA', 'Virginia', 0.37,
 f"<p>\u201cLow Risk\u201d tier, but enacted a K-12 facility ban in 2023 (school-focused; limited traveler exposure). Around the {nat}.</p>",
 [S['stone'], S['map']])
add('USA', 'District of Columbia', 0.38,
 f"<p>Downgraded from \u201cmost protective\u201d: as a federal district, Congress and the executive reach it directly — Congress attached a bathroom ban for DC, and activists protesting it at the Capitol were arrested (Dec 2024). Its protective local law layer persists but is overridable. Around the {nat}.</p>",
 ['https://www.axios.com/2024-12-05/transgender-rights-activists-arrested-capitol-bathroom-ban-protest', S['stone']])
add('USA', 'Maine', 0.39,
 f"<p>\u201cLow Risk\u201d tier, but <em>rose</em> in risk after the University of Maine system capitulated to federal pressure on trans sports participation — an institution folding rather than defending. Around the {nat}.</p>",
 [S['stone'], 'https://www.nbcnews.com/nbc-out/out-politics-and-policy/university-maine-complies-policies-restricting-trans-sports-participat-rcna197536'])
for st, sc in [('Delaware', 0.40), ('Pennsylvania', 0.40), ('Wisconsin', 0.40)]:
    add('USA', st, sc,
     f"<p>\u201cLow Risk\u201d tier in the July 2026 assessment: largely refrains from targeting trans adults but does not specialise in protection; no state-specific finding beyond the shared tier evidence. Marginally above the {nat}.</p>",
     [S['stone'], S['map']])

# ---- protective bloc ----
add('USA', 'Michigan', 0.44,
 f"<p>Mixed: robust anti-discrimination protections codified (2023 bipartisan expansion), but the state is not protecting incarcerated trans people. Direction genuinely two-sided. Above the {nat}.</p>",
 [S['stone'], 'https://www.pbs.org/newshour/politics/judge-denies-request-to-halt-missouris-gender-affirming-medical-care-ban'])
add('USA', 'Nevada', 0.44,
 f"<p>Mixed-leaning-protective: gender identity added to the state constitution by 2022 ballot; \u201cMost Protective\u201d-adjacent tier. Above the {nat}.</p>",
 [S['stone'], S['map']])
add('USA', 'Maryland', 0.42,
 f"<p>The clearest law-violence divergence in the country: Trans Health Equity Act and refuge/shield protections (Most Protective tier), <em>and</em> the second-highest killing rate (11.1 per 100k trans women/yr), including two Black trans women shot dead in Baltimore ten weeks apart in 2026. Protective law does not by itself make people safer. Above the {nat}, capped by the violence data.</p>",
 [S['needle'], 'https://www.pghlesbian.com/2026/09/two-black-trans-women-shot-to-death-in-baltimore-just-ten-weeks-apart-sophie-lee-is-the-most-recent-victim/',
  'https://www.marylandlawyerblog.com/trans-health-equity-act-maryland/'])
add('USA', 'California', 0.48,
 f"<p>Highest legal floor in the country: first sanctuary-state law (SB 107, 2023) and shield protections against out-of-state enforcement. But also the most incidents of any state in 2025 (198, GLAAD ALERT) with a \u201cdramatic increase\u201d in LA hate crime, and 34 recorded killings 2008–2025 (4.1 per 100k). Above the {nat}; law and street volume pull opposite ways.</p>",
 [S['glaad'], 'https://www.advocate.com/news/anti-lgbtq-hate-crimes-2025', S['needle'],
  'https://www.kqed.org/news/11929233/california-becomes-first-sanctuary-state-for-transgender-youth-seeking-medical-care'])
add('USA', 'Colorado', 0.50,
 f"<p>CADA expressly covers gender identity <em>and expression</em> in employment, housing and public accommodation — the last is directly traveler-relevant (hotels, restaurants, venues) — expanded again in 2025. Most Protective tier. Clearly above the {nat}.</p>",
 ['https://content.leg.colorado.gov/sites/default/files/r25-595-gender-affirming-care-and-transgender-legislation-accessible.pdf', S['stone']])
add('USA', 'Minnesota', 0.52,
 f"<p>Went furthest on non-cooperation: HF 146 (2023) declares out-of-state anti-trans law \u201cagainst the public policy of this state\u201d and blocks out-of-state warrants, arrests and extradition related to gender-affirming care — a state refusing to enforce other states' hostility. Most Protective tier; among the safest legal environments for a trans visitor in the US. Clearly above the {nat}.</p>",
 ['https://www.revisor.mn.gov/laws/2023/0/Session+Law/Chapter/29/', S['stone']])
add('USA', 'New Jersey', 0.52,
 f"<p>The safest measured jurisdiction in the country: lowest per-capita killing rate in the state-by-state dataset (3.4 per 100k trans women/yr; 4 recorded deaths 2008–2025) — half the general US homicide rate — inside the Most Protective legal tier. Clearly above the {nat}.</p>",
 [S['needle'], S['stone']])
PROT = ['Connecticut', 'Hawaii', 'Illinois', 'Massachusetts', 'New Mexico', 'New York',
        'Oregon', 'Rhode Island', 'Vermont', 'Washington']
for st in PROT:
    add('USA', st, 0.49 if st in ('Illinois', 'Oregon', 'Rhode Island', 'Washington') else 0.48,
     f"<p>\u201cMost Protective\u201d tier in the July 2026 assessment: regional non-discrimination covering gender identity and shield/refuge protections enforceable against out-of-state actions; no state-specific negative finding beyond the shared federal layer (passport/API policy, priced into the national score). {'No country-unique finding beyond insurance-coverage details a visitor never encounters.' if st in ('Delaware','Hawaii','Illinois','Massachusetts','New Mexico','Oregon','Pennsylvania','Rhode Island','Vermont','Wisconsin') else ''} Clearly above the {nat}.</p>".replace('  ', ' '),
     [S['stone'], 'https://mapresearch.org/equality-map/transgender-healthcare-shield-laws/'])

# ---- different-legal-system exceptions (estimated; no dedicated dossier) ----
chn = countries['CHN']
add('CHN', 'Xinjiang Uyghur Autonomous Region', 0.32,
 f"<p>Model estimate (no dedicated dossier). The mass-surveillance and arbitrary-detention apparatus documented for minority populations raises every axis of traveler risk — checkpoint document scrutiny, device searches, detention without clear recourse — on top of the national picture ({chn['score']:.2f}). No trans-specific regional data exists; the estimate reflects the general security regime's severity differential versus the national score.</p>",
 ['https://www.hrw.org/china-and-tibet'], estimated=True)
add('CHN', 'Tibet Autonomous Region', 0.36,
 f"<p>Model estimate (no dedicated dossier). Heavy security presence and permit requirements for foreigners raise document-check and scrutiny probability relative to the national score ({chn['score']:.2f}); no trans-specific regional data found.</p>",
 ['https://www.hrw.org/china-and-tibet'], estimated=True)
tza = countries['TZA']
zanz = [p for p in by_iso.get('TZA', []) if 'zanzibar' in p['name'].lower()]
for p in zanz:
    add('TZA', p['name'], 0.15,
     f"<p>Model estimate (no dedicated dossier). Zanzibar's autonomous government operates under a markedly more conservative religious governance than the mainland; LGBT prosecutions and social hostility are documented as more intense there. Estimated below the national score ({tza['score']:.2f}).</p>",
     tza['sources'][:2] if isinstance(tza['sources'][0], str) else [s['url'] for s in tza['sources'][:2]],
     estimated=True)
irq = countries['IRQ']
krg_names = ['Erbil', 'Dohuk', 'Duhok', 'Al-Sulaimaniyah', 'Sulaymaniyah', 'Halabja']
krg = [p for p in by_iso.get('IRQ', []) if any(k.lower() in p['name'].lower() for k in krg_names)]
for p in krg:
    add('IRQ', p['name'], 0.12,
     f"<p>Model estimate (no dedicated dossier). The Kurdistan Region is relatively more open than federal Iraq — a tolerated (underground) scene in Erbil, fewer militia abductions — but raids on gatherings and \u201ccross-dressing\u201d directives have been documented, and the national legal climate (Art. 8 of the 2024 anti-prostitution amendments criminalising \u201csodomy\u201d broadly) applies. Estimated above the national score ({irq['score']:.2f}) but still Do Not Travel.</p>",
     irq['sources'][:2] if isinstance(irq['sources'][0], str) else [s['url'] for s in irq['sources'][:2]],
     estimated=True)

json.dump(out, open('data/admin1.json', 'w'), indent=1, ensure_ascii=False)
n_usa = sum(1 for r in out.values() if r['iso3'] == 'USA')
print(f"wrote data/admin1.json: {len(out)} records ({n_usa} USA, "
      f"{len(out)-n_usa} exceptions: CHN 2, TZA {len(zanz)}, IRQ {len(krg)})")
