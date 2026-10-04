#!/usr/bin/env python3
"""Prison-housing findings merge: for each prison_out record, emit one apply_sources_fix
bundle and apply via its merge logic. Usage: python3 tools/apply_prison.py"""
import json, glob
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT/'tools'))
from apply_sources_fix import merge_bundle  # assume tool exposes it; else inline
import importlib.util
spec = importlib.util.spec_from_file_location('asf', ROOT/'tools/apply_sources_fix.py')
asf = importlib.util.module_from_spec(spec); spec.loader.exec_module(asf)
n = 0
for f in sorted(glob.glob(str(ROOT/'data/prison_out/*.json'))):
    for u in json.load(open(f)).get('records', []):
        adds = [a for a in (u.get('adds') or []) if a.get('verified') and a.get('url')]
        if not adds: continue
        asf.merge_bundle({"who": u['who'], "add": adds})
        n += 1
print(f"prison merges applied: {n} records")
