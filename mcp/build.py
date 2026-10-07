#!/usr/bin/env python3
"""Build the Telemetrio MCP landing pages.

  mcp/index.html      main page       (lib/page.py)
  mcp/alt/index.html  alternative     (lib/alt_page.py)

Content and configuration are kept separate from the components:

  content/<lang>/copy.json         main page copy (+ shared strings, setup labels, FAQ)
  content/<lang>/copy-alt.json     alternative page copy
  content/<lang>/prompts.json      example prompts
  content/<lang>/demo.json         main page demonstration scenarios (illustrative)
  content/<lang>/builder.json      alternative page prompt-builder options
  content/<lang>/refine.json       alternative page refinement walkthrough (illustrative)
  content/<lang>/connections.json  per-assistant connection values and instructions (shared)
  content/<lang>/access.json       access terms (shared)
  config/features.json             feature availability flags
  config/site.json                 URLs, analytics and experiment settings

Usage:
  python3 build.py                     preview build of both pages: marks launch dependencies, noindex
  python3 build.py --page alt          build one page (main | alt)
  python3 build.py --mode production   fails and lists every missing launch value until all are verified
"""
import argparse
import sys

from lib.alt_page import AltPage
from lib.page import ROOT, Page

PAGES = {"main": Page, "alt": AltPage}


def build(cls, mode, lang):
    page = cls(mode, lang)
    out = page.render()
    seen = set()
    missing = [m for m in page.missing if not (m in seen or seen.add(m))]
    required = [m for m in missing if not m[1].startswith("Optional")]
    print(f"[{cls.slug}] {len(required)} launch value(s) missing", file=sys.stderr)
    for key, what in missing:
        print(f"  {'~' if (key, what) not in required else '-'} {what}  [{key}]", file=sys.stderr)
    if mode == "production" and required:
        return False
    path = ROOT / cls.out_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(out, encoding="utf-8")
    print(f"[{cls.slug}] wrote {path.relative_to(ROOT.parent)} ({mode})")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=("preview", "production"), default="preview")
    ap.add_argument("--page", choices=tuple(PAGES), help="build only this page")
    ap.add_argument("--lang", default="en")
    args = ap.parse_args()
    pages = [PAGES[args.page]] if args.page else list(PAGES.values())
    ok = all([build(cls, args.mode, args.lang) for cls in pages])
    if not ok:
        print("Production build stopped: fill the values above with verified information.", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
