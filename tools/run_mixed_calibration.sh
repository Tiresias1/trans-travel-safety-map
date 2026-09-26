#!/usr/bin/env bash
# Full mixed-mode calibration: every dossier country's blindV2 regions paired
# against the frozen 232-country pool. 12 encounters per region, region-only
# updates, build+commit+push per country, final per-country drift report.
set -uo pipefail
cd "$(dirname "$0")/.."
KEY="$(cat /tmp/.qwen_key)"
# small/care-first countries early; the two giants last
ORDER=(GBR USA ITA AUS ZAF CAN FRA CHL POL DEU KOR PHL ESP ARG PER MEX MYS IDN COL IND NGA TUR RUS)
for ISO in "${ORDER[@]}"; do
  echo "=================== mixed $ISO $(date '+%F %T') ==================="
  N=$(python3 - "$ISO" << 'PY'
import json, sys
a = json.load(open('data/admin1.json'))
iso = sys.argv[1]
print(sum(1 for r in a.values() if r.get('iso3') == iso and r.get('dossier')
          and r.get('blindV2')))
PY
)
  if [ "$N" -eq 0 ]; then echo "$ISO: no blindV2 regions — SKIPPED"; continue; fi
  PAIRS=$((N * 12))
  echo "$ISO: $N regions -> $PAIRS pairs"
  python3 tools/blind_pairwise.py --regions-vs-countries --regions-parent "$ISO" \
    --api-key "$KEY" --num-pairs "$PAIRS" --workers 8 --seed 7 \
    --differential-weighting-percent 0.1-0.02 \
    --absolute-weighting-percent 0.07-0.01 \
    --absolute-weighting-shift 0.005-0.0009 || { echo "MIXED FAILED $ISO"; continue; }
  python3 tools/build_data.py | tail -1
  git add -A data/ && git commit -qm "mixed calibration $ISO: $N regions x 12 country comparisons (no scores shown; parent score removed; region-only updates)" && git push -q
  echo "$ISO done $(date '+%F %T')"
done
python3 - << 'EOF'
import json, statistics as st
a=json.load(open('data/admin1.json')); c=json.load(open('data/countries.json'))
print("\n=== drift report: mean(region scores) vs parent national score ===")
print(f"{'ISO':4} {'parent':>6} {'regMean':>7} {'drift':>7} {'min':>5} {'max':>5}  n")
for iso in sorted({r['iso3'] for r in a.values() if r.get('dossier')}):
    sc=[r['score'] for r in a.values() if r.get('iso3')==iso and r.get('dossier')]
    if not sc: continue
    nat=c[iso]['score']
    print(f"{iso:4} {nat:6.2f} {st.mean(sc):7.3f} {st.mean(sc)-nat:+7.3f} {min(sc):5.2f} {max(sc):5.2f}  {len(sc)}")
EOF
echo "ALL MIXED CALIBRATION DONE $(date '+%F %T')"
