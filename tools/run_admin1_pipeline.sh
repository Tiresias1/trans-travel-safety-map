#!/usr/bin/env bash
# Per-country admin1 pipeline for the 23 dossier countries:
#   1. tail-fill unscored units (route-3 defaults + fallback deltas)
#   2. blind pairwise refinement with qwen3.8-flash (20 pairs per unit,
#      ramped weighting: diff 0.1->0.02, abs% 0.07->0.01, shift 0.005->0.0009)
#   3. rebuild + commit
# Runs strictly sequentially — one writer to data/admin1.json at a time.
# Usage: bash tools/run_admin1_pipeline.sh [ISO ...]   (default: all pending)
set -uo pipefail
cd "$(dirname "$0")/.."

KEY="$(cat /tmp/.qwen_key)"
ISOS=("$@")
if [ ${#ISOS[@]} -eq 0 ]; then
  ISOS=(MEX CAN GBR AUS BRA IND DEU ESP COL ARG ITA POL NGA IDN MYS TUR RUS ZAF FRA PHL PER CHL KOR)
fi

for ISO in "${ISOS[@]}"; do
  echo "=================== $ISO $(date '+%F %T') ==================="
  python3 tools/fill_admin1_estimates.py --dossier-tail --only "$ISO" || { echo "tail-fill FAILED $ISO"; continue; }
  python3 tools/build_data.py | tail -1
  N=$(python3 -c "
import json
d=json.load(open('data/admin1.json'))
print(sum(1 for r in d.values() if r['iso3']=='$ISO'))")
  PAIRS=$((N * 20))
  echo "$ISO: $N units -> $PAIRS pairs"
  python3 tools/blind_pairwise.py --admin1 --country "$ISO" \
    --api-key "$KEY" \
    --num-pairs "$PAIRS" \
    --differential-weighting-percent 0.1-0.02 \
    --absolute-weighting-percent 0.07-0.01 \
    --absolute-weighting-shift 0.005-0.0009 \
    --workers 4 --seed 7 || { echo "PAIRWISE FAILED $ISO"; continue; }
  python3 tools/build_data.py | tail -1
  git add -A data/ && git commit -qm "ADM1 pipeline $ISO: initial Qwen scores + tail-fill ($N units) + blind pairwise $PAIRS pairs (diff 0.1-0.02, abs 0.07-0.01, shift 0.005-0.0009)" && git push -q
  echo "$ISO done $(date '+%F %T')"
done
echo "ALL COUNTRIES DONE $(date '+%F %T')"
