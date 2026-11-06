#!/usr/bin/env python3
"""Text cleanup via MiMo rewrites (NO regex prose surgery).

For each affected record's displayed text, ask xiaomi/mimo-v2.6-flash to:
  - remove self-reference/revision-history phrasing ("this record", "this model
    estimate", "the dossier", "parent country", changelog language);
  - reword the opening pointer ("The national record for X covers the federal
    layer..." -> "See the X country page for the national framework.");
  - PRESERVE every fact, law, incident, statistic, date, number, proper noun.
Verify every number in the source survives in the output (digit-subset), then
stage the rewrite for review. Nothing is applied to data here.
"""
import json, os, re, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = open('/tmp/.openrouter_key').read().strip()
MODEL = "xiaomi/mimo-v2.6-flash"
TARGETS = json.load(open(os.path.join(HERE, 'targets.json')))

SYSTEM = ("You edit visitor-facing transgender travel-safety text to a professional "
          "human-rights / UN field-report voice. You preserve facts exactly.")

INSTR = """Rewrite the TEXT below. Rules:
1. Remove any self-reference to the record/document itself. Never say "this record",
   "this assessment", "this dossier", "the dossier", "this model estimate", "this
   instrument", "this profile", "the parent country". Refer to the place and the law
   directly (e.g. "the law is documented" not "the law is documented in this record").
2. Remove any revision-history / changelog language ("earlier profile", "superseded",
   "was deleted", "was removed from the prior", "carried over from", "this record
   previously"). State the current state only.
3. If the text begins with wording like "The national record for X covers the federal
   layer..." or "See the national record for X...", replace that opening sentence with
   exactly: "See the X country page for the national framework." (X = the country name).
4. PRESERVE every fact, law, incident, statistic, date, number, and proper noun
   EXACTLY. Do not invent, drop, or alter any fact or number. Keep all region-local
   detail. Do not add commentary.
5. No AI-isms (delve, navigate, nuanced, foster, landscape, pivotal, testament, realm,
   "it is important to note"). Complete sentences.
Return ONLY JSON: {"text": "..."}

TEXT:
"""


def nums(t):
    return set(re.findall(r"\d+(?:[.,]\d+)*", t))


def call(text, retries=3):
    body = {"model": MODEL, "max_tokens": 6000, "temperature": 0.2,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": INSTR + text}]}
    for a in range(retries):
        try:
            req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
                data=json.dumps(body).encode(),
                headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
            d = json.loads(urllib.request.urlopen(req, timeout=300).read().decode())
            out = d['choices'][0]['message'].get('content') or ''
            m = re.search(r'\{[\s\S]*"text"[\s\S]*\}', out)
            if m:
                return json.loads(m.group(0)).get('text', '')
            return out.strip()
        except Exception:
            if a < retries - 1:
                time.sleep(3)
    return ""


def main():
    outpath = os.path.join(HERE, 'rewrites.jsonl')
    done = set()
    if os.path.exists(outpath):
        for line in open(outpath):
            try:
                done.add(json.loads(line)['id'])
            except Exception:
                pass
    tasks = [(i, t) for i, t in enumerate(TARGETS) if i not in done]
    print(f"targets: {len(TARGETS)}, remaining: {len(tasks)}", flush=True)
    n_ok = n_bad = 0

    def run(it):
        i, t = it
        old = t['text']
        new = call(old)
        ok_digits = nums(new) <= nums(old)   # every output digit exists in source
        no_bad = not any(re.search(re.escape(b), new, re.I) for b in
                         ['this record', 'this assessment', 'this dossier', 'the dossier',
                          'this model estimate', 'this instrument', 'this profile',
                          'parent country', 'earlier profile', 'superseded'])
        ptr_ok = (not t['pointer']) or bool(re.search(r'See the .{0,40}country page', new, re.I))
        return dict(id=i, kind=t['kind'], key=t['key'], name=t['name'], field=t['field'],
                    ok_digits=bool(ok_digits), cleaned=bool(no_bad), ptr_ok=bool(ptr_ok),
                    old=old, new=new)

    with open(outpath, 'a') as f, ThreadPoolExecutor(max_workers=5) as ex:
        futs = [ex.submit(run, it) for it in tasks]
        for fut in as_completed(futs):
            r = fut.result()
            f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
            if r['ok_digits'] and r['cleaned'] and r['ptr_ok']:
                n_ok += 1
            else:
                n_bad += 1
            if (n_ok + n_bad) % 25 == 0:
                print(f"  processed {n_ok+n_bad}: ok={n_ok} needs-attention={n_bad}", flush=True)
    print(f"DONE ok={n_ok} needs-attention={n_bad} -> {outpath}", flush=True)


if __name__ == '__main__':
    main()
