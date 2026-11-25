# Scope/scale confusion audit (MiMo sweep, all 3,241 ADM1 records)

Run: runs/scope-confusion-audit-20261124 (one mimo medium call/record, 3,241 judged; $0.24).
Counts: ok 2,886 / scale_error 270 / scope_error 68 / identity_error 1 / billed_unparseable 16.

## Pattern
"Division as city/capital" is systematic: province-level records whose summaries equate the
division with its capital (Kabul, Luanda, Huambo, Herat, Durres, ...), and parent/superordinate-unit
presentations (Zanzibar divisions vs Sultanate/Region; Kurdistan govs vs Region), and one identity error.
Trigger case Yazd ("This division is a desert religious city") is one of the 270, not an outlier.

## Repair scope
338 flagged records (270 scale + 68 scope) + 1 identity error. 16 billed_unparseable kept as gaps.
Repair = MiMo rewrite pass (see scope-repair wave): correct unit/scale, preserve all sourced facts,
no new claims, parent-regime rules unchanged. Structural prevention: consolidation prompt must state
the record's administrative level (province/region/state) and forbid city-scale framing for
province-scale units.
