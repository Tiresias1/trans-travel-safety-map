#!/usr/bin/env python3
"""Nepal vs UK trans-safety rating battery.

Runs a matrix of model x condition calls, each returning a 0-1 rating + reasoning.
Design (user-specified):
  Individual (rate one country) and Pairwise (rate both at once), each in
  knowledge-only / +article-summaries / +full-instructions flavours, with the
  evidence-based flavours also run BLINDED (country name removed, anonymised
  source summaries). Knowledge-only cannot be blinded.
All models run at thinking:medium. No Grok/Muse. Cheap->midrange, <= Sonnet/Terra.
Output: results.jsonl (one row per call).
"""
import json, os, re, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = open('/tmp/.openrouter_key').read().strip()
MAT = json.load(open(os.path.join(HERE, 'materials.json')))

MODELS = [
    "deepseek/deepseek-v4.1-flash",
    "xiaomi/mimo-v2.6-flash",
    "z-ai/glm-5.3",
    "openai/gpt-6.1-terra:floor",
    "anthropic/claude-sonnet-5.5",
]

ENDPOINTS = MAT['_endpoints']
RULES = MAT['_rules']
SCOPE = ("Consider ONLY risks specific to being trans: criminalisation and its "
         "enforcement; documents and border/screening; facilities (restrooms, changing "
         "rooms); custody/prison; access to trans health care; trans-specific violence and "
         "how authorities respond to it; and official hostility or protection. Do NOT "
         "consider general travel safety (crime, war, economy, scams) or LGBQ issues except "
         "where they specifically affect trans people.")


def individual_prompt(iso, cond, blind):
    name = MAT[iso]['name']
    who = "this jurisdiction" if blind else name
    art = MAT[iso]['blind_article_summaries'] if blind else MAT[iso]['article_summaries']
    lines = [
        f"You are rating travel safety for a TRANSGENDER VISITOR — someone who is, or is discovered to be, trans — visiting {who}.",
        f"Rate on a 0.00-1.00 scale: {ENDPOINTS}",
        SCOPE,
    ]
    if cond == 'knowledge':
        lines.append(f"Base this on your own knowledge of {who}. Use no external research.")
    elif cond == 'articles':
        lines.append(f"Here are summaries of researched source articles about {who}:\n{art}")
    elif cond == 'instructions':
        lines.append(f"Here are summaries of researched source articles about {who}:\n{art}")
        lines.append(f"Use the following rating instructions in forming your judgment:\n{RULES}")
    lines.append("Respond with a line 'RATING: <number 0.00-1.00>' then SEVERAL PARAGRAPHS "
                 "explaining exactly how you reached your decision — what drove it up or down "
                 "and how you weighed the factors.")
    return "\n\n".join(lines)


def pairwise_prompt(cond, blind):
    na, nb = MAT['NPL']['name'], MAT['GBR']['name']
    a = "Country A" if blind else na
    b = "Country B" if blind else nb
    art_a = MAT['NPL']['blind_article_summaries'] if blind else MAT['NPL']['article_summaries']
    art_b = MAT['GBR']['blind_article_summaries'] if blind else MAT['GBR']['article_summaries']
    lines = [
        f"You are rating travel safety for a TRANSGENDER VISITOR — someone who is, or is discovered to be, trans — visiting EACH of two jurisdictions: {a} and {b}.",
        f"Rate each on a 0.00-1.00 scale: {ENDPOINTS}",
        SCOPE,
    ]
    if cond == 'knowledge':
        lines.append(f"Base this on your own knowledge of {a} and {b}. Use no external research.")
    elif cond == 'articles':
        lines.append(f"Source article summaries for {a}:\n{art_a}\n\nSource article summaries for {b}:\n{art_b}")
    elif cond == 'instructions':
        lines.append(f"Source article summaries for {a}:\n{art_a}\n\nSource article summaries for {b}:\n{art_b}")
        lines.append(f"Use the following rating instructions in forming your judgment:\n{RULES}")
    lines.append("Respond with two lines 'RATING_A: <number 0.00-1.00>' and 'RATING_B: <number 0.00-1.00>' "
                 "then SEVERAL PARAGRAPHS explaining how you reached each decision and how the two compare.")
    return "\n\n".join(lines)


def build_jobs():
    jobs = []
    # individual
    for iso in ('NPL', 'GBR'):
        for cond in ('knowledge', 'articles', 'instructions'):
            jobs.append(dict(kind='individual', iso=iso, cond=cond, blind=False,
                             prompt=individual_prompt(iso, cond, False)))
        for cond in ('articles', 'instructions'):
            jobs.append(dict(kind='individual', iso=iso, cond=cond, blind=True,
                             prompt=individual_prompt(iso, cond, True)))
    # pairwise
    for cond in ('knowledge', 'articles', 'instructions'):
        jobs.append(dict(kind='pairwise', cond=cond, blind=False, prompt=pairwise_prompt(cond, False)))
    for cond in ('articles', 'instructions'):
        jobs.append(dict(kind='pairwise', cond=cond, blind=True, prompt=pairwise_prompt(cond, True)))
    return jobs


def call_model(model, prompt, retries=3):
    body = {"model": model, "max_tokens": 8000, "temperature": 0.2,
            "reasoning": {"effort": "medium"},
            "messages": [{"role": "user", "content": prompt}]}
    for attempt in range(retries):
        try:
            req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
                data=json.dumps(body).encode(),
                headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
            d = json.loads(urllib.request.urlopen(req, timeout=600).read().decode())
            ch = d['choices'][0]
            txt = (ch['message'].get('content') or '')
            u = d.get('usage', {})
            return txt, ch.get('finish_reason'), u.get('completion_tokens_details', {}).get('reasoning_tokens'), u.get('cost')
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(5 * (attempt + 1)); continue
            # retry without reasoning param (some models reject it)
            if 'reasoning' in body:
                body.pop('reasoning', None)
                if attempt < retries - 1: continue
            return f"__ERR__ {e.code} {e.read().decode()[:200]}", None, None, None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(4); continue
            return f"__ERR__ {type(e).__name__} {str(e)[:150]}", None, None, None
    return "__ERR__ exhausted", None, None, None


def parse_rating(txt, kind):
    if kind == 'pairwise':
        a = re.search(r'RATING_A[:\s]*([01](?:\.\d+)?)', txt, re.I)
        b = re.search(r'RATING_B[:\s]*([01](?:\.\d+)?)', txt, re.I)
        return (float(a.group(1)) if a else None, float(b.group(1)) if b else None)
    m = re.search(r'RATING[:\s]*([01](?:\.\d+)?)', txt, re.I)
    return float(m.group(1)) if m else None


def main():
    jobs = build_jobs()
    print(f"jobs per model: {len(jobs)}; models: {len(MODELS)}; total calls: {len(jobs)*len(MODELS)}", flush=True)
    outpath = os.path.join(HERE, 'results.jsonl')
    done = set()
    if os.path.exists(outpath):
        for line in open(outpath):
            try:
                r = json.loads(line); done.add((r['model'], r['jobid']))
            except Exception: pass
    tasks = []
    for model in MODELS:
        for i, job in enumerate(jobs):
            jobid = f"{job['kind']}|{job.get('iso','')}|{job['cond']}|{'blind' if job['blind'] else 'clear'}"
            if (model, jobid) in done: continue
            tasks.append((model, jobid, job))
    print(f"remaining calls: {len(tasks)}", flush=True)
    def run(t):
        model, jobid, job = t
        txt, finish, reasoning_tok, cost = call_model(model, job['prompt'])
        rating = parse_rating(txt, job['kind']) if not txt.startswith('__ERR__') else None
        return dict(model=model, jobid=jobid, kind=job['kind'], iso=job.get('iso'),
                    cond=job['cond'], blind=job['blind'], rating=rating,
                    finish=finish, reasoning_tokens=reasoning_tok, cost=cost,
                    output=txt[:6000], ts=time.time())
    n = 0
    with open(outpath, 'a') as f, ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(run, t) for t in tasks]
        for fut in as_completed(futs):
            r = fut.result()
            f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
            n += 1
            print(f"  [{n}/{len(tasks)}] {r['model'].split('/')[-1]:24} {r['jobid']:34} rating={r['rating']} err={str(r['output'])[:20] if str(r['output']).startswith('__ERR__') else ''}", flush=True)
    print("DONE ->", outpath, flush=True)


if __name__ == '__main__':
    main()
