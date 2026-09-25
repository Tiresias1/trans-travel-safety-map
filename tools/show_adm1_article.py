#!/usr/bin/env python3
"""Print the cached fetched text for one source URL (read-only worker helper)."""
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "research" / "fetched"

def main():
    if len(sys.argv) < 2:
        print("usage: show_adm1_article.py <url> [max_chars]", file=sys.stderr); return 2
    url = sys.argv[1]
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
    key = hashlib.sha1(url.encode()).hexdigest()[:16]
    meta_p, txt_p = CACHE / f"{key}.meta", CACHE / f"{key}.txt"
    status = "missing"
    http = None
    if meta_p.exists():
        try:
            m = json.loads(meta_p.read_text())
            status = m.get("status", "?"); http = m.get("http")
        except Exception:
            pass
    t = ""
    if txt_p.exists():
        t = txt_p.read_text(errors="replace").strip()
    if status != "ok" or len(t) < 200:
        print(f"FETCH-FAILED url={url} status={status} http={http} chars={len(t)}")
        print("Write a NOTE summary from the research dossier line for this URL "
              "(what the source WAS FOR), like countries.json does.")
        return 0
    if len(t) > cap:
        t = t[:cap] + f"\n[... truncated {len(t) - cap} more chars]"
    print(f"FETCH-OK url={url} chars={len(t)}\n{t}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
