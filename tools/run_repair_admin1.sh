#!/usr/bin/env bash
# Re-pair pass PHASE 2: admin1 regions with changed blind text, per-parent
# mixed calibration (regions vs frozen country pool; only the region moves).
# Same rule-8 weighted ramp as W4b-r2, seed 51.
set -uo pipefail
cd "$(dirname "$0")/.."
KEY="${OPENROUTER_KEY:-$(cat /tmp/.openrouter_key 2>/dev/null)}"

# parent: "unit name" pairs — only the changed units per parent
declare -a PARENTS=(KOR MYS NGA PER RUS TUR USA IDN IND)
declare -a UNITS=(
  "KOR:Seoul"
  "MYS:Sabah" "MYS:Sarawak" "MYS:Putrajaya" "MYS:Pahang" "MYS:Perlis" "MYS:Perak"
  "MYS:Penang" "MYS:Labuan" "MYS:Selangor" "MYS:Johor" "MYS:Malacca"
  "NGA:Ogun" "NGA:Oyo" "NGA:Lagos" "NGA:Bayelsa" "NGA:Ondo" "NGA:Delta"
  "NGA:Rivers" "NGA:Anambra" "NGA:Abia" "NGA:Ekiti" "NGA:Enugu" "NGA:Taraba" "NGA:Ebonyi"
  "PER:Lima"
  "RUS:Adygea" "RUS:Tatarstan" "RUS:Buryatia"
  "TUR:Ankara" "TUR:Gaziantep"
  "USA:Texas" "USA:Tennessee" "USA:South Carolina" "USA:Nebraska"
  "IDN:Banten" "IDN:Bengkulu" "IDN:Gorontalo" "IDN:Jambi" "IDN:Maluku" "IDN:Riau"
  "IND:Delhi"
)

for P in "${PARENTS[@]}"; do
  NAMES=""
  for U in "${UNITS[@]}"; do
    par="${U%%:*}"
    [ "$par" = "$P" ] && NAMES="$NAMES ${U#*:}"
  done
  N=$(python3 -c "print(len('''$NAMES'''.split()))")
  if [ "$N" -eq 0 ]; then echo "$P: no changed units — SKIPPED"; continue; fi
  PAIRS=$((N * 16))
  echo "=========== mixed $P: $N units -> $PAIRS pairs $(date '+%F %T') ==========="
  # shellcheck disable=SC2086
  python3 tools/blind_pairwise.py --regions-vs-countries --regions-parent "$P" \
    --regions-unit $NAMES --regions-unit-exact \
    --api openai \
    --baseurl "https://openrouter.ai/api/v1" \
    --endpoint-suffix "/chat/completions" \
    --auth-style bearer --api-key "$KEY" \
    --model "xiaomi/mimo-v2.6-flash" \
    --num-pairs "$PAIRS" \
    --differential-weighting-percent 0.1-0.02 \
    --absolute-weighting-percent 0.07-0.01 \
    --absolute-weighting-shift 0.005-0.0009 \
    --workers 4 --seed 51 || { echo "MIXED FAILED $P"; continue; }
  echo "$P done $(date '+%F %T')"
done
echo "ALL ADMIN1 REPAIR DONE $(date '+%F %T')"