#!/usr/bin/env bash
# Re-pair pass PHASE 1: countries with changed blind text vs full country pool.
# --focus restricts one side of every pair to the changed records; the partner is
# drawn from all 232 blind-complete countries (re-anchors against the full map).
# Rule-8 ramped weighting (W4b-r2 pattern) + seed 51 (rule-8 era).
set -uo pipefail
cd "$(dirname "$0")/.."
KEY="${OPENROUTER_KEY:-$(cat /tmp/.openrouter_key 2>/dev/null)}"
FOCUS="ABW AFG AGO AIA ATG AUS BES BLM BLZ BMU BRA CAN CHE CIV COK CRI CUW CYM ECU ESH FLK FRO GGY GHA GIB GLP GRC GRL GTM GUF GUM HKG HND IMN ISR JAM JPN KHM KOR LKA LUX MAC MDA MEX MLT MNP MSR MTQ MYT NCL NGA NIU NLD OMN PCN PHL PRI PYF REU SHN SLV TCA THA TTO TUR URY VAT VGB VIR VNM WLF"

N=$(python3 -c "print(71 * 16)")   # ~16 encounters per focus record
echo "focus countries: 71 -> pairs: $N  $(date '+%F %T')"
python3 tools/blind_pairwise.py --api openai \
  --baseurl "https://openrouter.ai/api/v1" \
  --endpoint-suffix "/chat/completions" \
  --auth-style bearer --api-key "$KEY" \
   --model "${LANE_MODEL:-meta/muse-spark-1.3-contributor}" \
  --focus $FOCUS \
  --num-pairs "$N" \
  --differential-weighting-percent 0.1-0.02 \
  --absolute-weighting-percent 0.07-0.01 \
  --absolute-weighting-shift 0.005-0.0009 \
  --workers 4 --seed 51
RC=$?
echo "PAIRWISE RC=$RC $(date '+%F %T')"
exit $RC