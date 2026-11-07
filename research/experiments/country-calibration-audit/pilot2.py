#!/usr/bin/env python3
"""Pre-registered non-publishing country-comparison pilot (pilot 2).

Design fixed in terra-method-review.md section 3. 96 core calls, four balanced
randomisation blocks of 24:

  block b = 18 matrix cells at draw b  (9 pairs x 2 presentation orders)
          +  3 isolated single-dossier draws (USA/GBR/NPL, draw b)
          +  3 identical-copy draws (one orientation per block, see below)

Matrix pairs: USA/GBR/NPL x PRY/FSM plus USA-GBR, USA-NPL, NPL-GBR.
Isolated: one dossier, no comparator, same system prompt and scoring task.
Identical-copy orientation: the two dossier renders are byte-identical for
USA/GBR/NPL (the side label only affects dependent-territory parent sections),
so "A/B formatting reversed" is realised as block-order reversal - normal =
DOS SIER A block first, reversed = DOS SIER B block first; content identical.

Caps: 96 logical calls, one retry max per failed call (both attempts logged),
attempt ceiling 112; aggregate 2,000,000 input / 800,000 output tokens
INCLUDING retries. The run stops and reports rather than exceed a cap.

Model/settings identical to pilot.py: deepseek/deepseek-v4.1-flash via
BP.call_api (openai dialect, call_api_openai: reasoning effort high, no
temperature sent with reasoning on; api_args temperature 0.3), system prompt =
BP.build_system_prompt(research/outing-risk-taxonomy.md), BP.dossier rendering.

Never writes outside research/experiments/country-calibration-audit/; never
touches data/; publishes nothing; no score interpretation (diagnostics only).
"""
import hashlib, json, random, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import blind_pairwise as BP
from encounter_replay import api_args

HERE = Path(__file__).resolve().parent
OUT = HERE / 'pilot2-results.ndjson'
META = HERE / 'pilot2-metadata.json'
PROMPT_DIR = HERE / 'pilot2-prompts'
LOGF = HERE / 'pilot2.log'

C = json.loads((ROOT / 'data/countries.json').read_text())
TAX = (ROOT / 'research/outing-risk-taxonomy.md').read_text()
SYSTEM = BP.build_system_prompt(TAX)
ARGS = api_args()  # openai dialect -> call_api_openai: reasoning effort high

IN_CAP = 2_000_000
OUT_CAP = 800_000
MAX_CALLS = 96
MAX_ATTEMPTS = 112
CONCURRENCY = 4
SEED = 20261107

TARGETS = ('USA', 'GBR', 'NPL')
PARTNERS = ('PRY', 'FSM')
PAIRS = [(t, p) for t in TARGETS for p in PARTNERS]
PAIRS += [('USA', 'GBR'), ('USA', 'NPL'), ('NPL', 'GBR')]
# per block: which identical-copy orientation/draw pairs with that block
COPY_BLOCK = {1: ('afirst', 1), 2: ('bfirst', 1), 3: ('afirst', 2), 4: ('bfirst', 2)}

sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
utcnow = lambda: datetime.now(timezone.utc).isoformat()

LOG_LOCK = threading.Lock()
OUT_LOCK = threading.Lock()
BUDGET_LOCK = threading.Lock()
STOP = threading.Event()
STOP_REASON = ['']
IN_USED = OUT_USED = 0
IN_RES = OUT_RES = 0
MAX_IN_CALL, MAX_OUT_CALL = 60_000, 20_000   # conservative first-call reservation
ATTEMPTS_USED = 0
BLOCK1_REPORTED = [False]


def log(msg):
    with LOG_LOCK:
        with LOGF.open('a') as f:
            f.write(f"[{utcnow()}] {msg}\n")
        print(msg, flush=True)


def budget_snapshot():
    with BUDGET_LOCK:
        return IN_USED, OUT_USED, IN_RES, OUT_RES, ATTEMPTS_USED


def budget_reserve():
    """Reserve worst-case tokens for one attempt. False -> stop and report."""
    global IN_RES, OUT_RES
    with BUDGET_LOCK:
        if IN_USED + IN_RES + MAX_IN_CALL > IN_CAP or OUT_USED + OUT_RES + MAX_OUT_CALL > OUT_CAP:
            return False
        if ATTEMPTS_USED >= MAX_ATTEMPTS:
            return False
        IN_RES += MAX_IN_CALL
        OUT_RES += MAX_OUT_CALL
        return True


def budget_commit(inp, outp):
    global IN_USED, OUT_USED, IN_RES, OUT_RES, MAX_IN_CALL, MAX_OUT_CALL
    with BUDGET_LOCK:
        IN_RES -= MAX_IN_CALL
        OUT_RES -= MAX_OUT_CALL
        IN_USED += inp
        OUT_USED += outp
        MAX_IN_CALL = max(MAX_IN_CALL, inp)
        MAX_OUT_CALL = max(MAX_OUT_CALL, outp)


def attempt_counted():
    global ATTEMPTS_USED
    with BUDGET_LOCK:
        if ATTEMPTS_USED >= MAX_ATTEMPTS:
            return False
        ATTEMPTS_USED += 1
        return True


def request_stop(reason):
    if not STOP.is_set():
        STOP_REASON[0] = reason
        STOP.set()
        log(f"STOP: {reason}")


# --------------------------------------------------------------------------- #
# Prompt construction
# --------------------------------------------------------------------------- #

def user_prompt(job):
    kind = job['condition']
    if kind == 'matrix':
        left, right = job['order']
        return BP.build_user_prompt(C[left], C[right], left, right)
    if kind == 'isolated':
        iso = job['target']
        return (f"Rate the dossier below.\n\n## DOSSIER A\n\n"
                f"{BP.dossier(C[iso], iso, 'A')}\n\n"
                "Reply with only the JSON object described in the output format.")
    # identical-copy: two byte-identical copies, block order per orientation
    t = job['target']
    block_a = f"## DOSSIER A\n\n{BP.dossier(C[t], t, 'A')}"
    block_b = f"## DOSSIER B\n\n{BP.dossier(C[t], t, 'B')}"
    first, second = (block_a, block_b) if job['orientation'] == 'afirst' else (block_b, block_a)
    return ("Rate the two dossiers below.\n\n" + first + "\n\n" + second +
            "\n\nReply with only the JSON object described in the output format.")


def save_prompt(usha, text):
    p = PROMPT_DIR / f"{usha}.txt"
    if not p.exists():
        tmp = p.with_suffix('.tmp')
        tmp.write_text(text)
        tmp.replace(p)
    return f"pilot2-prompts/{p.name}"


def parse_isolated(resp):
    """Single-dossier parse: score_a is the assessment; score_b (if emitted
    anyway) is recorded but not part of this condition."""
    ch = (resp.get('choices') or [{}])[0]
    msg = ch.get('message') or {}
    text = str(msg.get('content') or "")
    if isinstance(text, list):
        text = "".join(b.get('text', "") for b in text if isinstance(b, dict))
    stop = ch.get('finish_reason') or ch.get('stop_reason')
    m = None
    for cand in BP.JSON_RE.finditer(text):
        m = cand
    sb = None
    if m:
        obj = json.loads(m.group(0))
        sa = float(obj["score_a"])
        why = str(obj.get("why", ""))[:400]
        if obj.get("score_b") is not None:
            try:
                v = float(obj["score_b"])
                sb = v if 0.0 <= v <= 1.0 else None
            except (TypeError, ValueError):
                sb = None
    else:
        ma = BP.SCORE_A_RE.search(text)
        if not ma:
            raise ValueError(f"no score_a in response (stop_reason={stop}): {text[:200]!r}")
        sa = float(ma.group(1))
        why = "[truncated] " + (text[ma.end():ma.end() + 200])
    if not (0.0 <= sa <= 1.0):
        raise ValueError(f"score out of range: {sa}")
    return sa, sb, why


# --------------------------------------------------------------------------- #
# Schedule: four balanced blocks of 24
# --------------------------------------------------------------------------- #

def schedule():
    blocks = {}
    for b in range(1, 5):
        jobs = []
        for pair in PAIRS:
            for order in (pair, pair[::-1]):
                jobs.append({
                    'key': f"m-{order[0]}-{order[1]}-d{b}",
                    'condition': 'matrix', 'pair': list(pair),
                    'order': list(order), 'draw_index': b, 'block': b,
                    'orientation': None,
                    'focus': [x for x in order if x in TARGETS],
                })
        for iso in TARGETS:
            jobs.append({
                'key': f"i-{iso}-d{b}",
                'condition': 'isolated', 'pair': None,
                'order': [iso], 'draw_index': b, 'block': b,
                'orientation': None, 'target': iso, 'focus': [iso],
            })
        orient, cdraw = COPY_BLOCK[b]
        for iso in TARGETS:
            jobs.append({
                'key': f"c-{iso}-{orient}-d{cdraw}",
                'condition': 'copy', 'pair': [iso, iso],
                'order': [iso, iso], 'draw_index': cdraw, 'block': b,
                'orientation': orient, 'target': iso, 'focus': [iso],
            })
        assert len(jobs) == 24, len(jobs)
        random.Random(SEED + b).shuffle(jobs)
        for pos, j in enumerate(jobs):
            j['shuffle_position'] = pos
        blocks[b] = jobs
    allkeys = [j['key'] for b in blocks for j in blocks[b]]
    assert len(allkeys) == MAX_CALLS == len(set(allkeys))
    return blocks


# --------------------------------------------------------------------------- #
# Attempt execution
# --------------------------------------------------------------------------- #

def base_row(job, attempt, retry_of):
    return {
        'row_id': f"{job['key']}#a{attempt}",
        'key': job['key'],
        'condition': job['condition'],
        'pair': job['pair'],
        'order': job['order'],
        'focus': job['focus'],
        'target': job.get('target'),
        'draw_index': job['draw_index'],
        'block': job['block'],
        'shuffle_position': job['shuffle_position'],
        'orientation': job['orientation'],
        'attempt': attempt,
        'retry_of': retry_of,
        'model': ARGS.model,
        'api_dialect': 'openai',
        'endpoint': ARGS.baseurl.rstrip('/') + ARGS.endpoint_suffix,
        'temperature_setting': ARGS.temperature,
        'temperature_sent': False,
        'reasoning': {'effort': 'high'},
        'max_tokens': ARGS.reasoning_tokens + ARGS.max_output_tokens,
        'rubric_version': BP.RUBRIC_VERSION,
        'timestamp': utcnow(),
    }


def attempt_call(job, attempt, retry_of):
    row = base_row(job, attempt, retry_of)
    prompt = user_prompt(job)
    usha, ssha = sha(prompt), sha(SYSTEM)
    row['system_sha256'] = ssha
    row['user_sha256'] = usha
    row['prompt_sha256'] = sha(SYSTEM + prompt)   # concatenated system+user
    row['prompt_file'] = save_prompt(usha, prompt)
    row['system_file'] = 'pilot2-prompts/system.txt'

    if not budget_reserve():
        if not STOP.is_set():
            request_stop("token budget or attempt ceiling reached; remaining "
                         "calls not attempted")
        row.update(status='cancelled', error='not attempted: stop condition',
                   raw_response=None, raw_content=None, parsed_scores=None,
                   scores=None, why=None, usage=None, api_model=None)
        return row
    if not attempt_counted():
        row.update(status='cancelled', error='not attempted: attempt ceiling',
                   raw_response=None, raw_content=None, parsed_scores=None,
                   scores=None, why=None, usage=None, api_model=None)
        return row

    resp = None
    inp = outp = 0
    try:
        resp = BP.call_api(ARGS, SYSTEM, prompt)
        u = resp.get('usage') or {}
        inp = int(u.get('prompt_tokens') or 0)
        outp = int(u.get('completion_tokens') or 0)
        if job['condition'] == 'isolated':
            sa, sb, why = parse_isolated(resp)
            parsed = {'score_a': sa, 'score_b': sb}
            scores = {job['target']: sa}
        else:
            sa, sb, why, pu = BP.parse_scores(resp, 'openai')
            parsed = {'score_a': sa, 'score_b': sb}
            scores = {job['order'][0]: sa, job['order'][1]: sb}
        row.update(status='ok', error=None,
                   raw_response=resp,
                   raw_content=(resp.get('choices') or [{}])[0].get('message', {}).get('content'),
                   api_model=resp.get('model'),
                   parsed_scores=parsed, scores=scores, why=why,
                   usage={'input_tokens': inp, 'output_tokens': outp,
                          'stop_reason': (resp.get('choices') or [{}])[0].get('finish_reason')})
    except Exception as e:
        row.update(status='failed', error=f'{type(e).__name__}: {str(e)[:500]}',
                   raw_response=resp,
                   raw_content=((resp.get('choices') or [{}])[0].get('message', {}).get('content')
                                if resp else None),
                   api_model=(resp or {}).get('model'),
                   parsed_scores=None, scores=None, why=None,
                   usage={'input_tokens': inp, 'output_tokens': outp} if resp else None)
    finally:
        budget_commit(inp, outp)
    return row


def emit(row):
    with OUT_LOCK:
        with OUT.open('a') as f:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
            f.flush()
    st = row['status']
    if st == 'cancelled':
        log(f"CALL {row['row_id']} CANCELLED ({row['error']})")
        return
    u = row.get('usage') or {}
    log(f"CALL {row['row_id']} {st.upper()} order={row['order']} "
        f"scores={row.get('scores')} err={row.get('error')} "
        f"in={u.get('input_tokens')} out={u.get('output_tokens')} "
        f"totals_in={IN_USED} totals_out={OUT_USED} attempts={ATTEMPTS_USED}")


def run_job(job):
    retry_of = job.get('_resume_retry_of')
    start = 2 if retry_of else 1
    for attempt in (start, 2):
        if STOP.is_set():
            row = base_row(job, attempt, retry_of)
            row.update(status='cancelled',
                       error=f"not attempted: {STOP_REASON[0]}",
                       system_sha256=sha(SYSTEM), user_sha256=None,
                       prompt_sha256=None, prompt_file=None,
                       system_file='pilot2-prompts/system.txt',
                       raw_response=None, raw_content=None, parsed_scores=None,
                       scores=None, why=None, usage=None, api_model=None)
            emit(row)
            return
        row = attempt_call(job, attempt, retry_of)
        emit(row)
        if row['status'] == 'ok':
            return
        if row['status'] == 'cancelled':
            return
        retry_of = row['row_id']   # failed -> at most one retry (attempt 2)


def budget_report(tag):
    i, o, res_i, res_o, att = budget_snapshot()
    log(f"{tag}: input={i}/{IN_CAP} ({100.0*i/IN_CAP:.1f}%) "
        f"output={o}/{OUT_CAP} ({100.0*o/OUT_CAP:.1f}%) "
        f"attempts={att}/{MAX_ATTEMPTS} reserved_in={res_i} reserved_out={res_o}")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def load_done():
    """row_ids already attempted; settled keys; failed-attempt-1 keys that
    still owe one retry."""
    attempted, settled, pending = set(), set(), {}
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            attempted.add(d['row_id'])
            if d['status'] == 'ok':
                settled.add(d['key'])
                pending.pop(d['key'], None)
            elif d['status'] == 'failed':
                if d['attempt'] == 2:
                    settled.add(d['key'])   # both attempts burned; report missingness
                else:
                    pending[d['key']] = d['row_id']
    return attempted, settled, pending


def seed_budget_from_rows():
    global IN_USED, OUT_USED, ATTEMPTS_USED
    if not OUT.exists():
        return
    for line in OUT.read_text().splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if d['status'] in ('ok', 'failed'):
            ATTEMPTS_USED += 1
            u = d.get('usage') or {}
            IN_USED += int(u.get('input_tokens') or 0)
            OUT_USED += int(u.get('output_tokens') or 0)


def write_metadata(n_blocks_done):
    meta = {
        'purpose': 'Pre-registered non-publishing country-comparison pilot '
                   '(terra-method-review.md section 3); diagnostics only, '
                   'never a score, never published',
        'model': ARGS.model,
        'endpoint': ARGS.baseurl.rstrip('/') + ARGS.endpoint_suffix,
        'api_dialect': 'openai (BP.call_api -> call_api_openai)',
        'settings': {'temperature_setting': ARGS.temperature,
                     'temperature_sent': False,
                     'reasoning': {'effort': 'high'},
                     'max_tokens': ARGS.reasoning_tokens + ARGS.max_output_tokens},
        'rubric_version': BP.RUBRIC_VERSION,
        'system_sha256': sha(SYSTEM),
        'system_file': 'pilot2-prompts/system.txt',
        'prompt_hash_def': 'prompt_sha256 = sha256(system_text + user_text)',
        'design': '9 pairs x 2 orders x 4 draws (72) + 3 isolated x 4 draws (12) '
                  '+ 3 targets x 2 orientations x 2 draws (12) = 96 calls',
        'blocks': '4 balanced blocks of 24, shuffled within block '
                  f'(seed {SEED}); block1 = matrix draw1 + isolated draw1 + '
                  'copy afirst draw1; block2 = matrix draw2 + isolated draw2 + '
                  'copy bfirst draw1; block3 = matrix draw3 + isolated draw3 + '
                  'copy afirst draw2; block4 = matrix draw4 + isolated draw4 + '
                  'copy bfirst draw2',
        'pairs': PAIRS,
        'isolated_realization': 'single DOS SIER A block, no comparator; same '
                                'system prompt and scoring task; score_a is the '
                                'assessment, any emitted score_b recorded but '
                                'ignored',
        'copy_orientation_realization': 'dossier renders are byte-identical for '
                                        'these targets, so "A/B formatting '
                                        'reversed" = block-order reversal: '
                                        'afirst = DOS SIER A block first, '
                                        'bfirst = DOS SIER B block first',
        'caps': {'logical_calls': MAX_CALLS, 'attempt_ceiling': MAX_ATTEMPTS,
                 'input_tokens': IN_CAP, 'output_tokens': OUT_CAP,
                 'retry_policy': 'max one retry per failed call, both attempts logged'},
        'optional_evidence_contrast': 'NOT RUN (out of scope for this pilot)',
        'limitations': ['small purposive pilot', 'PRY/FSM purposive not representative',
                        'four draws = feasibility choice, not power',
                        'isolated condition uses a two-dossier system prompt '
                        '(pre-registered fixed settings), so pair-vs-isolated '
                        'differs in prompt condition as well as comparator',
                        'labels can be inferable from facts'],
    }
    META.write_text(json.dumps(meta, indent=2))


def main():
    PROMPT_DIR.mkdir(exist_ok=True)
    (PROMPT_DIR / 'system.txt').write_text(SYSTEM)

    resuming = OUT.exists()
    attempted, settled, pending = load_done()
    if not resuming:
        OUT.touch()
    seed_budget_from_rows()
    write_metadata(0)
    log(f"PILOT2 START resume={resuming} model={ARGS.model} "
        f"system_sha256={sha(SYSTEM)[:16]} caps_in={IN_CAP} caps_out={OUT_CAP} "
        f"max_calls={MAX_CALLS} max_attempts={MAX_ATTEMPTS} concurrency={CONCURRENCY}")

    blocks = schedule()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        for b in range(1, 5):
            jobs = []
            for j in blocks[b]:
                if j['key'] in settled:
                    continue
                if j['key'] in pending:
                    j['_resume_retry_of'] = pending[j['key']]
                jobs.append(j)
            futures = [ex.submit(run_job, j) for j in jobs]
            for fut in as_completed(futures):
                fut.result()
            budget_report(f"BLOCK {b} done")
            if b == 1 and not BLOCK1_REPORTED[0]:
                BLOCK1_REPORTED[0] = True
                i, o, _, _, att = budget_snapshot()
                log(f"BLOCK 1 BUDGET REPORT (first 24 calls): consumed "
                    f"{i} input tokens ({100.0*i/IN_CAP:.1f}% of {IN_CAP}) and "
                    f"{o} output tokens ({100.0*o/OUT_CAP:.1f}% of {OUT_CAP}) "
                    f"over {att} attempts; block-1 projection to 96 calls: "
                    f"in~{4*i} out~{4*o}")
            if STOP.is_set():
                log(f"RUN HALTED after block {b}: {STOP_REASON[0]}")
                break

    i, o, _, _, att = budget_snapshot()
    statuses = {}
    for line in OUT.read_text().splitlines():
        if line.strip():
            d = json.loads(line)
            statuses[d['status']] = statuses.get(d['status'], 0) + 1
    log(f"PILOT2 END statuses={statuses} attempts={att}/{MAX_ATTEMPTS} "
        f"input={i}/{IN_CAP} output={o}/{OUT_CAP} stop={STOP_REASON[0] or 'none'}")
    if STOP.is_set():
        log(f"PILOT2 INCOMPLETE: {STOP_REASON[0]}")


if __name__ == '__main__':
    main()