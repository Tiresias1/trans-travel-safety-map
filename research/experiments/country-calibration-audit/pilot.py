#!/usr/bin/env python3
"""Small, non-publishing country-pair diagnostic. Outputs data only, never scores.

Six target/reference pairs and three target/target pairs, each in both orders.
PRY and FSM were chosen before the run because they appear among archived shared
partners (USA/NPL and USA/GBR respectively); neither is representative by itself.
One judgment per order. Current production-style country dossier and system prompt;
not an exact historical replay. Country identities can still be inferable from facts.
"""
import hashlib, json, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import blind_pairwise as BP
from encounter_replay import api_args

OUT = Path(__file__).with_name('pilot-results.jsonl')
META = Path(__file__).with_name('pilot-metadata.json')
C = json.loads((ROOT / 'data/countries.json').read_text())
TAX = (ROOT / 'research/outing-risk-taxonomy.md').read_text()
SYSTEM = BP.build_system_prompt(TAX)
PAIRS = [(t,p) for t in ('USA','GBR','NPL') for p in ('PRY','FSM')]
PAIRS += [('USA','GBR'),('USA','NPL'),('NPL','GBR')]
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()

def task(pair, reverse):
    left, right = pair if not reverse else pair[::-1]
    prompt = BP.build_user_prompt(C[left], C[right], left, right)
    meta = {'pair': pair, 'order': [left,right], 'system_sha256': sha(SYSTEM),
            'user_sha256': sha(prompt), 'timestamp': datetime.now(timezone.utc).isoformat()}
    try:
        resp = BP.call_api(api_args(), SYSTEM, prompt)
        a,b,why,usage = BP.parse_scores(resp,'openai')
        meta.update(scores={left:a,right:b}, why=why, usage=usage,
                    raw_content=(resp.get('choices') or [{}])[0].get('message',{}).get('content'),
                    api_model=resp.get('model'), error=None)
    except Exception as e:
        meta.update(scores=None, error=f'{type(e).__name__}: {str(e)[:500]}')
    return meta

def main():
    if OUT.exists():
        raise SystemExit(f'{OUT} already exists; refusing to mix runs')
    metadata={'purpose':'Non-publishing paired-order diagnostic; not a new score or exact archived replay',
              'model':'deepseek/deepseek-v4.1-flash','rubric_version':BP.RUBRIC_VERSION,
              'system_sha256':sha(SYSTEM),'pairs':PAIRS,'calls_planned':2*len(PAIRS),
              'randomisation':'Both orders once; output order is completion order',
              'sources':'current data/countries.json and research/outing-risk-taxonomy.md',
              'limitations':'small purposive sample; A/B order confounded with call randomness; labels can be inferable'}
    META.write_text(json.dumps(metadata,indent=2))
    jobs=[(pair,reverse) for pair in PAIRS for reverse in (False,True)]
    with OUT.open('x') as f, ThreadPoolExecutor(max_workers=3) as ex:
        futures=[ex.submit(task,*x) for x in jobs]
        for i,fut in enumerate(as_completed(futures),1):
            row=fut.result(); f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush()
            print(f"{i}/{len(jobs)} {row['order']} scores={row['scores']} error={row['error']}",flush=True)
    print('DONE',flush=True)
if __name__=='__main__': main()
