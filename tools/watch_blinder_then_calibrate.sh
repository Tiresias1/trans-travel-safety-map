#!/usr/bin/env bash
# Guardian: wait for the blinding fleet to FULLY finish, then run the mixed
# calibration. Never starts while blinding may still write admin1.json.
# Conditions (all required before launch):
#   1. hard minimum wait: 2h from watcher start (user instruction)
#   2. coverage: blindV2 count == dossier count (633) per check_adm1_blind.py
#   3. quiet: last commit >90min old AND admin1.json mtime >60min old
# Polls every 10 min. If not complete by 12h+, keeps waiting (user: "make sure
# it's fully done"; "if unsure wait a full half day" — coverage must say done).
set -uo pipefail
cd "$(dirname "$0")/.."
LOG=data/mixed_watcher.log
say(){ echo "$(date '+%F %T') $*" >> "$LOG"; }
say "watcher armed (min-wait 2h; needs blindV2==dossier count + quiet repo)"
sleep 7200
while true; do
  CNT=$(python3 - << 'PY' 2>/dev/null
import json
a=json.load(open('data/admin1.json'))
d=[r for r in a.values() if r.get('dossier')]
print(len(d), sum(1 for r in d if r.get('blindV2')))
PY
) || { say "count failed (file busy?)"; sleep 600; continue; }
  TOT=${CNT% *}; DONE=${CNT#* }
  LASTC=$(python3 -c "import subprocess,time;print(int(time.time())-int(subprocess.run(['git','log','-1','--format=%ct'],capture_output=True,text=True).stdout))")
  LASTF=$(python3 -c "import os,time;print(int(time.time()-os.path.getmtime('data/admin1.json')))")
  say "coverage $DONE/$TOT | quiet: commit ${LASTC}s ago, file ${LASTF}s ago"
  if [ "$TOT" -gt 0 ] && [ "$DONE" = "$TOT" ] && [ "$LASTC" -gt 5400 ] && [ "$LASTF" -gt 3600 ]; then
    say "blinder complete + quiet — launching mixed calibration"
    bash tools/run_mixed_calibration.sh >> data/mixed_calibration.log 2>&1
    say "calibration script exited"
    exit 0
  fi
  sleep 600
done
