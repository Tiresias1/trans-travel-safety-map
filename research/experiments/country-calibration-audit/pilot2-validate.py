#!/usr/bin/env python3
"""Validation for pilot2 results (checks only; writes nothing).

Verifies: every ndjson row carries the required audit fields; saved prompt files
hash-match their rows (user sha, system sha, concatenated prompt sha); parsed
scores are in range with rationale and usage present; retry linkage is correct;
96 logical calls / attempt ceiling / token caps respected; balanced block
composition (18 matrix + 3 isolated + 3 copy attempt-1 rows per block).
Exit 0 = all checks pass.
"""
import collections, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = [json.loads(l) for l in (HERE / 'pilot2-results.ndjson').read_text().splitlines() if l.strip()]
fail = []

REQ = {'key', 'pair', 'order', 'focus', 'draw_index', 'block', 'shuffle_position',
       'orientation', 'attempt', 'retry_of', 'model', 'api_dialect', 'endpoint',
       'temperature_setting', 'temperature_sent', 'reasoning', 'max_tokens',
       'rubric_version', 'timestamp', 'status', 'system_sha256', 'user_sha256',
       'prompt_sha256', 'prompt_file', 'system_file', 'raw_response', 'raw_content',
       'api_model', 'parsed_scores', 'scores', 'why', 'usage', 'error'}
for r in rows:
    if not REQ <= set(r):
        fail.append(f"{r.get('row_id')}: missing {sorted(REQ - set(r))}")

sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
sys_txt = (HERE / 'pilot2-prompts' / 'system.txt').read_text()
for r in rows:
    if r['status'] != 'ok':
        continue
    rid = r['row_id']
    if sha(sys_txt) != r['system_sha256']:
        fail.append(f"{rid}: system sha mismatch")
    pt = (HERE / r['prompt_file']).read_text()
    if sha(pt) != r['user_sha256']:
        fail.append(f"{rid}: saved prompt file sha mismatch")
    if sha(sys_txt + pt) != r['prompt_sha256']:
        fail.append(f"{rid}: combined prompt sha mismatch")
    ps = r['parsed_scores']
    if not (0 <= ps['score_a'] <= 1):
        fail.append(f"{rid}: score_a out of range {ps['score_a']}")
    if ps['score_b'] is not None and not (0 <= ps['score_b'] <= 1):
        fail.append(f"{rid}: score_b out of range {ps['score_b']}")
    if not r['why']:
        fail.append(f"{rid}: empty rationale")
    u = r['usage'] or {}
    if not (u.get('input_tokens') and u.get('output_tokens')):
        fail.append(f"{rid}: missing usage {u}")
    if r['raw_response'] is None:
        fail.append(f"{rid}: missing raw response")

fails = {r['row_id']: r for r in rows if r['status'] == 'failed'}
for r in rows:
    if r['attempt'] == 2:
        src = r.get('retry_of')
        if src not in fails or fails[src]['attempt'] != 1:
            fail.append(f"{r['row_id']}: bad retry linkage {src}")

keys = collections.defaultdict(list)
for r in rows:
    keys[r['key']].append(r)
if len(keys) != 96:
    fail.append(f"logical calls {len(keys)} != 96")
if len(rows) > 112:
    fail.append(f"attempts {len(rows)} > 112")
inT = sum((r.get('usage') or {}).get('input_tokens') or 0 for r in rows)
outT = sum((r.get('usage') or {}).get('output_tokens') or 0 for r in rows)
if inT > 2_000_000:
    fail.append(f"input tokens {inT} > 2,000,000")
if outT > 800_000:
    fail.append(f"output tokens {outT} > 800,000")

sched = collections.Counter((r['block'], r['condition']) for r in rows if r['attempt'] == 1)
for b in (1, 2, 3, 4):
    for cond, want in (('matrix', 18), ('isolated', 3), ('copy', 3)):
        if sched[(b, cond)] != want:
            fail.append(f"block {b} {cond}: {sched[(b, cond)]} != {want}")

ok_rows = sum(1 for r in rows if r['status'] == 'ok')
print(f"rows={len(rows)} ok={ok_rows} failed={len(fails)} "
      f"logical_calls={len(keys)} attempts={len(rows)}/112 "
      f"input={inT}/2000000 output={outT}/800000")
# Verify each analysis contrast against raw presentation order, not the
# arbitrary ordering of names in the pair key. Both participants matter.
analysis = json.loads((HERE / 'pilot2-analysis.json').read_text())
contrasts = analysis['matrix']['order_contrasts']
expected_contrasts = {(tuple(row['pair']), country)
                      for row in rows if row['status'] == 'ok' and row['condition'] == 'matrix'
                      for country in row['pair']}
actual_contrasts = [(tuple(item['pair']), item['country']) for item in contrasts]
if set(actual_contrasts) != expected_contrasts or len(actual_contrasts) != len(set(actual_contrasts)):
    fail.append('matrix order contrasts missing, duplicated, or unexpected')
for item in contrasts:
    pair = item['pair']
    country = item['country']
    first, second = [], []
    for row in rows:
        if row['status'] != 'ok' or row['condition'] != 'matrix' or row['pair'] != pair:
            continue
        order = row['order']
        if order[0] == country:
            first.append(row['parsed_scores']['score_a'])
        elif order[1] == country:
            second.append(row['parsed_scores']['score_b'])
    if not first or not second:
        fail.append(f"{pair}/{country}: missing order group")
        continue
    expected = round(sum(first) / len(first) - sum(second) / len(second), 4)
    if (item['n_first'], item['n_second']) != (len(first), len(second)) or abs(
        item['contrast_first_minus_second'] - expected
    ) > 1e-4:
        fail.append(f"{pair}/{country}: first/second contrast differs from raw order")

if fail:
    print("VALIDATION FAILED:")
    for f in fail:
        print(" -", f)
    sys.exit(1)
print("VALIDATION PASS: schema, prompt hashes, scores, usage, retry linkage, "
      "caps, block composition, first/second contrasts")