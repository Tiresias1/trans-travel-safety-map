# Scope/scale repair report (339 repair wave, MiMo medium)

Run: runs/scope-repair-20261125 (one attempt/record, no retries; MAX_USD $10).
Scope: 339 audit-flagged records (270 scale_error + 68 scope_error +
1 identity_error). 16 billed_unparseable audit gaps left untouched.

## Counts
repairs_applied=283 (records) | status={"rejected": 44, "repaired": 283, "billed_unparseable": 12} |
by_verdict={"scope_error": {"rejected": 9, "repaired": 58, "billed_unparseable": 1}, "scale_error": {"repaired": 224, "rejected": 35, "billed_unparseable": 11}, "identity_error": {"repaired": 1}} | halted=None
cost_total_usd=0.0820310348 (MAX_USD $10) | records_done=339

## Gaps (transport_failure / billed_unparseable)
12 gap(s): 35879248B2594883865860(billed_unparseable), 35879248B5815864302343(billed_unparseable), 46179711B99776351599397(billed_unparseable), 63095687B63570319440385(billed_unparseable), 25212430B31479954216778(billed_unparseable), 25212430B70495112373630(billed_unparseable), 83640313B20015641298084(billed_unparseable), 59799669B20319020653405(billed_unparseable), 24955722B70468072404853(billed_unparseable), 36821470B82174860486434(billed_unparseable), 58719522B57750794760959(billed_unparseable), 14850775B41808765507575(billed_unparseable)

## Leak gate (rendered dossiers of repaired+blinded records)
offenders: none
re-blind attempts: none


## Prevention
Consolidation prompt (summaries' authoring lane) updated in
tools/consolidate_record.py SYSTEM — new 'ADMINISTRATIVE LEVEL' rule at
lines 121-131 of tools/consolidate_record.py (verified with grep -n
'ADMINISTRATIVE LEVEL'): requires the record's administrative level and
forbids city/capital framing for province-scale units and
parent/superordinate-as-division presentations.

## Samples (before -> after, incl. Yazd)
### Yazd (scale_error) sid=17685810B18940918043543
BEFORE (summary): <p>This division is a desert religious city. Assessed relative to the national picture in Iran, it presents a distinct regional character shaped by its desert setting and religious identity.</p>
AFTER (summary): <p>This division is a desert province with a distinctive religious identity. Within Iran as a whole, it presents a distinct regional character shaped by its arid desert setting and its religious heritage.</p>

### Dohuk (scope_error) sid=90741666B81100048725045
BEFORE (summary): <p>The Kurdistan Region is relatively more open than federal Iraq — a tolerated (underground) scene in Erbil, fewer militia abductions — but raids on gatherings and “cross-dressing” directives have been documented, and the national legal climate (Art. 8 of the 2024 anti-prostitution amendments criminalising “sodomy” broadly) applies. Estimated above the national level (0.04) but still dangerous.</p>
AFTER (summary): <p>Dohuk Province, in the Kurdistan Region of northern Iraq, sits in a territory relatively more open than federal Iraq — a tolerated (underground) scene in the regional capital Erbil, fewer militia abductions — but raids on gatherings and “cross-dressing” directives have been documented, and the national legal climate (Art. 8 of the 2024 anti-prostitution amendments criminalising “sodomy” broadly) applies. Still dangerous.</p>

### Niger (identity_error) sid=27671186B79778155682183
BEFORE: <p>Niger is an independent country with its own criminal law; the
assessment below is national.</p><p>Article 25 of the Refoundation Charter,
adopted in March 2025, criminalises all lesbian, gay, bisexual,
transgender, queer, intersex and asexual acts or practices, expressly
including transgender acts or practices. The February 2026 penal code
punishes LGBTQIA+ acts or practices with 5 to 10 years' imprisonment and a
fine of up to 100 million CFA francs, ...
AFTER: <p>Niger State is a province-scale territory of Nigeria in the
country's North Central region, a large inland state through which the
Niger River runs, with its own criminal law; the assessment below concerns
conditions recorded across the state.</p><p>Article 25 of the Refoundation
Charter, adopted in March 2025, criminalises all lesbian, gay, bisexual,
transgender, queer, intersex and asexual acts or practices, expressly
including transgender acts or practices. The February 2026 penal code
punishes LGBTQIA+ acts or practices with 5 to 10 years' imprisonment and a
fine of up to 100 million CFA francs, ...

(identity fix: facts preserved verbatim; only the country-vs-state framing
was corrected)

### Zanzibar Urban/West (scope_error) sid=36957248B66874645654546
BEFORE (summary): <p>Zanzibar's autonomous government operates under a markedly more conservative religious governance than the mainland; LGBT prosecutions and social hostility are documented as more intense there. Estimated below the national level (0.10).</p>
AFTER (summary): <p>Zanzibar Urban/West is a region of the Zanzibar archipelago lying off the mainland Tanzanian coast, where the archipelago's autonomous government operates under a markedly more conservative religious governance than the mainland; LGBT prosecutions and social hostility are documented as more intense there.</p>

#### Rejected examples (one attempt kept original)
### Zanzibar South & Central (scope_error) sid=36957248B39816127207897
BEFORE (summary): <p>Zanzibar's autonomous government operates under a markedly more conservative religious governance than the mainland; LGBT prosecutions and social hostility are documented as more intense there. Estimated below the national level (0.10).</p>
AFTER (summary): n/a
### Zanzibar North (scope_error) sid=36957248B81638677744414
BEFORE (summary): <p>Zanzibar's autonomous government operates under a markedly more conservative religious governance than the mainland; LGBT prosecutions and social hostility are documented as more intense there. Estimated below the national level (0.10).</p>
AFTER (summary): n/a
