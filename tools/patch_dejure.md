# De Jure Boundary Policy & Patches

Base data: geoBoundaries gbOpen ADM0 (CC BY 4.0) — per-country files that reflect each
country's OWN official (de jure claim) boundaries. Because claimed lines differ between
neighbours, merging produces overlaps. This table documents every resolved overlap and
the rule applied. Also used: Western Sahara polygon extracted from Natural Earth 10m
admin-0 (public domain) because gbOpen has no ESH unit.

## Automated sliver cleanup
Each country's polygon is clipped by the union of all countries earlier in `ORDER`
(see tools/merge_adm0.py): later country wins any residual overlapping sliver. This
resolves dozens of <5,000 km² mismatch slivers along ordinary uncontested borders.

## Explicit patches (big or policy-sensitive overlaps)
| # | Area | gbOpen state | Decision (most widely recognised de jure) | Implementation |
|---|---|---|---|---|
| 1 | Taiwan | CHN polygon contains TWN; both are separate units | Taiwan rendered as its own unit (PRC claim noted in CHN caveat) | CHN := CHN − TWN |
| 2 | Aksai Chin / Trans-Karakoram | claimed+drawn by both IND and CHN | Chinese-administered; Indian claim noted in IND caveat | IND := IND − CHN (post-patch 3) |
| 3 | Arunachal Pradesh | claimed+drawn by both CHN and IND | Indian; Chinese claim noted in CHN caveat | CHN := CHN − (overlap ∩ Arunachal bbox) |
| 4 | Kashmir west of LoC (Gilgit-Baltistan, Azad Kashmir) | claimed+drawn by both IND and PAK | Pakistani-administered (widely-recognised position); Indian claim noted in IND caveat | IND := IND − PAK |
| 5 | Southern Kurils (Etorofu, Kunashiri, Shikotan, Habomai) | claimed+drawn by both JPN and RUS | Russian-administered (standard depiction; unresolved dispute); Japanese claim noted in JPN caveat | RUS ordered after JPN (RUS wins) |
| 6 | Hala'ib Triangle | claimed+drawn by both SDN and EGY | Egyptian-administered (standard depiction); Sudanese claim noted in SDN caveat | EGY ordered after SDN (EGY wins) |
| 7 | Ilemi Triangle | claimed+drawn by both KEN and SSD | South Sudanese-administered; Kenyan claim noted in KEN caveat | SSD ordered after KEN (SSD wins) |
| 8 | Kosovo | separate XKX unit | Kosovo rendered as its own unit (contested: Serbia claims it; ~100+ UN members recognise). Caveat in both XKX and SRB records. | as-is |
| 9 | Ukraine (Crimea + occupied oblasts) | correctly all UKR in gbOpen | de jure Ukraine ✓ (this is the case the brief called out) | as-is |
| 10 | Abkhazia / S. Ossetia | correctly GEO | de jure Georgia ✓ | as-is |
| 11 | Transnistria | correctly MDA | de jure Moldova ✓ | as-is |
| 12 | Northern Cyprus | correctly CYP (whole island) | de jure Republic of Cyprus ✓; caveat in CYP record re TRNC administration | as-is |
| 13 | Nagorno-Karabakh | correctly AZE (post-2023) | de jure Azerbaijan ✓ | as-is |
| 14 | Western Sahara | not in gbOpen; Morocco polygon excludes it | Rendered as separate ESH unit (UN non-self-governing territory); caveat in ESH + MAR records re Moroccan administration | NE 10m ESH polygon added |
| 15 | West Bank / Gaza | PSE separate; ISR excludes WB | Palestine separate ✓ | as-is |
| 16 | Golan Heights | inside ISR polygon (annexation view) | De jure Syrian per UNSC 497; at map scale (~1,150 km²) not re-cut — documented caveat in ISR and SYR records instead | documented only |
| 17 | East Jerusalem | inside ISR polygon | De jure occupied Palestinian territory per UNGA/UNSC; pixel-scale — documented caveat in ISR and PSE records | documented only |
| 18 | Hong Kong, Macao | not separate ADM0 units in gbOpen; SARs within CHN ADM1 | Rendered as separate country-level units (distinct legal regimes) if found in CHN ADM1 | promoted from CHN ADM1 |
| 19 | Puerto Rico | US territory; in USA ADM1 | Rendered as separate country-level unit if found in USA ADM1 (distinct entry regime from mainland US) | promoted from USA ADM1 |
| 20 | Antarctica | ATA unit in gbOpen | Shown grey, "not assessed" | as-is |

De jure = internationally (broadly UN-membership/ICJ/treaty) recognised. Where two
states each hold a legal claim with no settled position, the rendering follows the most
widely-used depiction and BOTH records carry a caveat sentence. Every patched record's
popup text includes its caveat (enforced in data build).
