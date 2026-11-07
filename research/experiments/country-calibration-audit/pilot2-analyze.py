#!/usr/bin/env python3
"""Analysis for pilot2 (diagnostics only; never a score, never published).

Reads pilot2-results.ndjson, writes pilot2-analysis.json and prints a condensed
summary. Per pair and per target: means, within-cell sd, distributions
(min/q1/median/q3/max), order contrasts (target rating when presented first vs
second), identical-copy asymmetry, isolated-vs-pair differences; flags
same-direction order contrasts larger than typical within-cell variation;
reports failures and missingness.
"""
import json, math, statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWS = [json.loads(l) for l in (HERE / 'pilot2-results.ndjson').read_text().splitlines() if l.strip()]
OUTF = HERE / 'pilot2-analysis.json'
TARGETS = ('USA', 'GBR', 'NPL')
PARTNERS = ('PRY', 'FSM')
PAIRS = [(t, p) for t in TARGETS for p in PARTNERS]
PAIRS += [('USA', 'GBR'), ('USA', 'NPL'), ('NPL', 'GBR')]


def dist(xs):
    """Distribution summary; xs must be non-empty."""
    xs = sorted(xs)
    n = len(xs)
    q = st.quantiles(xs, n=4, method='inclusive') if n >= 2 else [xs[0]] * 3
    return {'n': n, 'mean': round(st.mean(xs), 4),
            'sd': round(st.stdev(xs), 4) if n >= 2 else None,
            'min': round(xs[0], 4), 'q1': round(q[0], 4),
            'median': round(q[1], 4), 'q3': round(q[2], 4),
            'max': round(xs[-1], 4),
            'values': [round(x, 4) for x in xs]}


def cell_key(row):
    return (row['condition'], tuple(row['pair']) if row['pair'] else None,
            tuple(row['order']), row['orientation'])


ok = [r for r in ROWS if r['status'] == 'ok']
failed = [r for r in ROWS if r['status'] == 'failed']
cancelled = [r for r in ROWS if r['status'] == 'cancelled']

# --------------------------------------------------------------------------- #
# Completeness / failures
# --------------------------------------------------------------------------- #
logical = {}
for r in ROWS:
    logical.setdefault(r['key'], []).append(r)
missing = []
for k, rs in sorted(logical.items()):
    if not any(r['status'] == 'ok' for r in rs):
        missing.append({'key': k, 'attempts': [(r['row_id'], r['status'], r['error'])
                                                for r in rs]})
# expected cells: (condition, pair, order[, orientation]) x 4 draws (copy: x2 per orientation)
expected = []
for pair in PAIRS:
    for order in (pair, pair[::-1]):
        for d in range(1, 5):
            expected.append(('matrix', pair, order, None, d))
for iso in TARGETS:
    for d in range(1, 5):
        expected.append(('isolated', None, (iso,), None, d))
for iso in TARGETS:
    for orient in ('afirst', 'bfirst'):
        for d in range(1, 3):
            expected.append(('copy', (iso, iso), (iso, iso), orient, d))
have = {}
for r in ok:
    have[(r['condition'], tuple(r['pair']) if r['pair'] else None,
          tuple(r['order']), r['orientation'], r['draw_index'])] = r
missing_cells = [e for e in expected if e not in have]

failures = [{'row_id': r['row_id'], 'block': r['block'], 'attempt': r['attempt'],
             'retry_of': r['retry_of'], 'error': r['error'],
             'usage': r['usage']} for r in failed]

in_tot = sum((r.get('usage') or {}).get('input_tokens') or 0 for r in ROWS)
out_tot = sum((r.get('usage') or {}).get('output_tokens') or 0 for r in ROWS)

report = {
    'completeness': {
        'logical_calls_planned': 96,
        'logical_calls_attempted': len(logical),
        'logical_calls_ok': sum(1 for k, rs in logical.items()
                                if any(r['status'] == 'ok' for r in rs)),
        'attempt_rows': len(ROWS),
        'ok_rows': len(ok), 'failed_rows': len(failed),
        'cancelled_rows': len(cancelled),
        'attempts_used': len(ok) + len(failed),
        'attempt_ceiling': 112,
        'failed_attempts': failures,
        'fully_missing_calls': missing,
        'missing_cells': [dict(zip(('condition', 'pair', 'order', 'orientation', 'draw'), e))
                          for e in missing_cells],
    },
    'budget': {
        'input_tokens': in_tot, 'input_cap': 2_000_000,
        'output_tokens': out_tot, 'output_cap': 800_000,
        'input_pct': round(100.0 * in_tot / 2_000_000, 1),
        'output_pct': round(100.0 * out_tot / 800_000, 1),
        'block1_consumed': {'input': 317466, 'output': 93644, 'attempts': 24},
    },
}

# --------------------------------------------------------------------------- #
# Matrix: ratings per cell, per pair, order contrasts
# --------------------------------------------------------------------------- #
def rating(row, country):
    """country's rating in this row (0/None if not in the row)."""
    if country not in row['order']:
        return None
    ps = row['parsed_scores']
    return ps['score_a'] if row['order'][0] == country else ps['score_b']

cells = {}   # (pair, order, country) -> [ratings]
for r in ok:
    if r['condition'] != 'matrix':
        continue
    for c in r['pair']:   # every country in the pair, targets and partners
        cells.setdefault((tuple(r['pair']), tuple(r['order']), c), []).append(rating(r, c))
cells = {k: v for k, v in cells.items() if v and all(x is not None for x in v)}

cell_stats = []
for (pair, order, c), vals in sorted(cells.items()):
    cell_stats.append({'pair': list(pair), 'order': list(order), 'country': c,
                       'draws': len(vals), **dist(vals)})

pair_pooled = []
for pair in PAIRS:
    for c in pair:
        vals = []
        for order in (pair, pair[::-1]):
            vals += cells.get((pair, order, c), [])
        pair_pooled.append({'pair': list(pair), 'country': c, **dist(vals)})

order_contrasts = []
for pair in PAIRS:
    for c in pair:
        first = cells.get((pair, pair, c), [])          # c presented first (A)
        second = cells.get((pair, pair[::-1], c), [])   # c presented second (B)
        if not first or not second:
            continue
        contrast = st.mean(first) - st.mean(second)
        sd_f = st.stdev(first) if len(first) >= 2 else None
        sd_s = st.stdev(second) if len(second) >= 2 else None
        sds = [s for s in (sd_f, sd_s) if s is not None]
        typical = st.mean(sds) if sds else None
        order_contrasts.append({
            'pair': list(pair), 'country': c,
            'n_first': len(first), 'n_second': len(second),
            'mean_first': round(st.mean(first), 4),
            'mean_second': round(st.mean(second), 4),
            'contrast_first_minus_second': round(contrast, 4),
            'sd_first': round(sd_f, 4) if sd_f is not None else None,
            'sd_second': round(sd_s, 4) if sd_s is not None else None,
            'typical_within_cell_sd': round(typical, 4) if typical is not None else None,
            'contrast_exceeds_typical_within_cell': bool(typical is not None
                                                         and abs(contrast) > typical),
        })

# repeated same-direction order contrast per target across its 4 pairs
target_flags = []
for c in TARGETS:
    cs = [o for o in order_contrasts if o['country'] == c]
    signs = [1 if o['contrast_first_minus_second'] > 0 else
             (-1 if o['contrast_first_minus_second'] < 0 else 0) for o in cs]
    pos = signs.count(1); neg = signs.count(-1)
    all_cell_sds = [cell['sd'] for cell in cell_stats
                    if cell['country'] == c and cell['sd'] is not None]
    typical_all = st.mean(all_cell_sds) if all_cell_sds else None
    n_large_same_dir = sum(
        1 for o in cs
        if o['contrast_exceeds_typical_within_cell']
        and ((pos >= 3 and o['contrast_first_minus_second'] > 0) or
             (neg >= 3 and o['contrast_first_minus_second'] < 0)))
    target_flags.append({
        'target': c,
        'contrasts_by_pair': {','.join(o['pair']): o['contrast_first_minus_second'] for o in cs},
        'n_positive': pos, 'n_negative': neg,
        'same_direction': 'positive' if pos >= 3 else ('negative' if neg >= 3 else 'mixed'),
        'mean_within_cell_sd_all_cells': round(typical_all, 4) if typical_all else None,
        'n_pairs_where_contrast_exceeds_typical_within_cell_and_direction_repeats':
            n_large_same_dir,
        'flag_repeated_same_direction_larger_than_within_cell_variation':
            bool(n_large_same_dir >= 3),
    })

report['matrix'] = {'cell_stats': cell_stats, 'pair_pooled': pair_pooled,
                    'order_contrasts': order_contrasts, 'target_order_flags': target_flags}

# --------------------------------------------------------------------------- #
# Isolated vs pair
# --------------------------------------------------------------------------- #
iso_stats, iso_vs_pair = [], []
for c in TARGETS:
    iso_vals = [r['parsed_scores']['score_a'] for r in ok
                if r['condition'] == 'isolated' and r['target'] == c]
    pair_vals = [rating(r, c) for r in ok if r['condition'] == 'matrix' and c in r['focus']]
    pair_vals = [v for v in pair_vals if v is not None]
    d = st.mean(iso_vals) - st.mean(pair_vals)
    iso_stats.append({'target': c, **dist(iso_vals)})
    per_pair = {}
    for pair in PAIRS:
        if c not in pair:
            continue
        vals = []
        for order in (pair, pair[::-1]):
            vals += cells.get((pair, order, c), [])
        per_pair[','.join(pair)] = {'pair_mean': round(st.mean(vals), 4),
                                    'isolated_minus_pair': round(st.mean(iso_vals) - st.mean(vals), 4)}
    iso_vs_pair.append({
        'target': c,
        'isolated_mean': round(st.mean(iso_vals), 4),
        'pair_pooled_mean': round(st.mean(pair_vals), 4),
        'isolated_minus_pair_pooled': round(d, 4),
        'isolated_sd': round(st.stdev(iso_vals), 4),
        'pair_pooled_sd': round(st.stdev(pair_vals), 4),
        'per_pair': per_pair,
    })
report['isolated'] = {'isolated_stats': iso_stats, 'isolated_vs_pair': iso_vs_pair}

# --------------------------------------------------------------------------- #
# Identical-copy asymmetry
# --------------------------------------------------------------------------- #
copy_stats, copy_calls = [], []
for c in TARGETS:
    rows_c = [r for r in ok if r['condition'] == 'copy' and r['target'] == c]
    by_orient = {}
    for orient in ('afirst', 'bfirst'):
        rs = [r for r in rows_c if r['orientation'] == orient]
        by_orient[orient] = {
            'score_a': dist([r['parsed_scores']['score_a'] for r in rs]) if rs else None,
            'score_b': dist([r['parsed_scores']['score_b'] for r in rs]) if rs else None,
        }
    asym = [round(r['parsed_scores']['score_a'] - r['parsed_scores']['score_b'], 4)
            for r in rows_c]
    a_first = [r['parsed_scores']['score_a'] for r in rows_c if r['orientation'] == 'afirst']
    b_first = [r['parsed_scores']['score_a'] for r in rows_c if r['orientation'] == 'bfirst']
    copy_stats.append({
        'target': c,
        'by_orientation': by_orient,
        'asymmetry_a_minus_b': {'values': asym,
                                'mean': round(st.mean(asym), 4) if asym else None,
                                'mean_abs': round(st.mean([abs(x) for x in asym]), 4) if asym else None,
                                'max_abs': round(max(abs(x) for x in asym), 4) if asym else None},
        'mean_score_a_afirst': round(st.mean(a_first), 4) if a_first else None,
        'mean_score_a_bfirst': round(st.mean(b_first), 4) if b_first else None,
        'orientation_shift_a_minus_b_on_score_a':
            round(st.mean(a_first) - st.mean(b_first), 4) if a_first and b_first else None,
    })
    for r in rows_c:
        copy_calls.append({'key': r['key'], 'orientation': r['orientation'],
                           'score_a': r['parsed_scores']['score_a'],
                           'score_b': r['parsed_scores']['score_b'],
                           'asymmetry': round(r['parsed_scores']['score_a']
                                              - r['parsed_scores']['score_b'], 4)})
report['identical_copy'] = {'copy_stats': copy_stats, 'all_copy_calls': copy_calls}

# --------------------------------------------------------------------------- #
# Partner contrasts vs observed within-cell variation
# --------------------------------------------------------------------------- #
def cell_sds(country):
    return [c['sd'] for c in cell_stats if c['country'] == country and c['sd'] is not None]

def pooled_mean(country, pair):
    vals = []
    for order in (pair, pair[::-1]):
        vals += cells.get((tuple(pair), tuple(order), country), [])
    return st.mean(vals)

partner_contrasts = []
for c in TARGETS:
    pair_means = {','.join(p): round(pooled_mean(c, p), 4) for p in PAIRS if c in p}
    pry = st.mean([pooled_mean(c, p) for p in PAIRS if c in p and 'PRY' in p])
    fsm = st.mean([pooled_mean(c, p) for p in PAIRS if c in p and 'FSM' in p])
    typ = st.mean(cell_sds(c)) if cell_sds(c) else None
    contrast = pry - fsm
    partner_contrasts.append({
        'target': c, 'pair_pooled_means': pair_means,
        'mean_vs_PRY_partners': round(pry, 4), 'mean_vs_FSM_partners': round(fsm, 4),
        'partner_contrast_PRY_minus_FSM': round(contrast, 4),
        'typical_within_cell_sd': round(typ, 4) if typ else None,
        'contrast_exceeds_typical_within_cell': bool(typ and abs(contrast) > typ),
    })

pair_gaps = []
for pair in [('USA', 'GBR'), ('USA', 'NPL'), ('NPL', 'GBR')]:
    m1, m2 = pooled_mean(pair[0], pair), pooled_mean(pair[1], pair)
    typ = st.mean([s for c in pair for s in cell_sds(c)])
    pair_gaps.append({
        'pair': list(pair),
        f'mean_{pair[0]}': round(m1, 4), f'mean_{pair[1]}': round(m2, 4),
        'gap_first_minus_second': round(m1 - m2, 4),
        'typical_within_cell_sd': round(typ, 4),
        'gap_exceeds_typical_within_cell': abs(m1 - m2) > typ,
    })
report['partner_contrasts'] = {'by_target': partner_contrasts, 'direct_pair_gaps': pair_gaps}

# --------------------------------------------------------------------------- #
# Rationale (why) availability diagnostics - no interpretation
# --------------------------------------------------------------------------- #
whys = [r['why'] for r in ok]
report['rationale_diagnostics'] = {
    'n_ok': len(ok),
    'n_with_why': sum(1 for w in whys if w),
    'n_truncated': sum(1 for w in whys if w and w.startswith('[truncated]')),
    'why_len_chars': dist([len(w) for w in whys if w]),
}

# partner (PRY/FSM) pooled distributions per pair already in pair_pooled
report['notes'] = [
    'Diagnostics only: no score interpretation, no published value changed.',
    'Four draws per cell is a feasibility choice, not a power guarantee.',
    'Isolated condition uses the fixed two-dossier system prompt (pre-registered '
    'settings), so pair-vs-isolated differences confound condition and comparator.',
    'Identical-copy orientation = block-order reversal (A block first vs B block '
    'first); dossier content byte-identical.',
]

OUTF.write_text(json.dumps(report, indent=2))
print(json.dumps({'completeness': report['completeness'],
                  'budget': report['budget'],
                  'target_order_flags': target_flags,
                  'isolated_vs_pair': iso_vs_pair,
                  'copy_asymmetry': [{k: v for k, v in cs.items() if k != 'by_orientation'}
                                     for cs in copy_stats],
                  'partner_contrasts': report['partner_contrasts'],
                  'rationale_diagnostics': report['rationale_diagnostics']}, indent=2))
print('wrote', OUTF)