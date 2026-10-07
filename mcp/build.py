#!/usr/bin/env python3
"""Build the Telemetrio MCP landing page (mcp/index.html).

Content and configuration are kept separate from the components below:

  content/<lang>/copy.json         landing page copy
  content/<lang>/prompts.json      example prompts
  content/<lang>/demo.json         demonstration scenarios (prepared, illustrative data)
  content/<lang>/connections.json  per-assistant connection values and instructions
  content/<lang>/access.json       access terms
  config/features.json             feature availability flags
  config/site.json                 URLs, analytics and experiment settings

Usage:
  python3 build.py                     preview build: writes index.html, marks launch dependencies, noindex
  python3 build.py --mode production   fails and lists every missing launch value until all are verified
"""
import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSISTANTS = ("claude", "chatgpt")


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def esc(value):
    return html.escape(str(value), quote=True)


ICONS = {
    "check": '<svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 5 5L20 7"/></svg>',
    "copy": '<svg class="i-copy" aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>',
    "copied": '<svg class="i-check" aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 5 5L20 7"/></svg>',
    "external": '<svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>',
    "megaphone": '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11v2a1 1 0 0 0 1 1h3l6 4V6L7 10H4a1 1 0 0 0-1 1Z"/><path d="M16.5 8.5a5 5 0 0 1 0 7"/></svg>',
    "compass": '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5z"/></svg>',
    "table": '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M9 10v10"/></svg>',
    "compare": '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 20V10M12 20V4M18 20v-7"/></svg>',
    "search": '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    "mention": '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-4 8"/></svg>',
    "menu": '<svg class="i-open" aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg><svg class="i-close" aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>',
}
TONES = ("tone-a", "tone-b")
AVATAR_COLORS = ("--bg-data-01", "--bg-data-06", "--bg-data-12", "--bg-data-09")


class Page:
    def __init__(self, mode, lang):
        self.mode = mode
        content = f"content/{lang}"
        self.copy = load(f"{content}/copy.json")
        self.prompts = {p["id"]: p for p in load(f"{content}/prompts.json")["prompts"]}
        self.demo = load(f"{content}/demo.json")
        self.conn = load(f"{content}/connections.json")["assistants"]
        self.access = load(f"{content}/access.json")
        self.features = load("config/features.json")
        self.site = load("config/site.json")
        self.missing = []

    # ---------- helpers ----------
    @property
    def preview(self):
        return self.mode == "preview"

    def dep(self, key, what):
        """Record a missing launch value; in preview, render a visible note."""
        self.missing.append((key, what))
        if not self.preview:
            return ""
        return f'<p class="dep" role="note"><b>Launch dependency:</b> {esc(what)} <code>{esc(key)}</code></p>'

    def enabled(self, item):
        feature = item.get("feature")
        return not feature or self.features.get(feature, False)

    def name(self, a):
        return self.copy["assistants"][a]["name"]

    def logo(self, a):
        return f'<svg class="logo-{a}" aria-hidden="true" viewBox="0 0 24 24"><use href="#logo-{a}"/></svg>'

    def logo_symbol(self, a):
        """Inline the assistant logo once as a <symbol>; buttons reference it with <use>."""
        svg = (ROOT / f"src/icons/{a}.svg").read_text(encoding="utf-8")
        inner = svg.split(">", 1)[1].rsplit("</svg>", 1)[0]
        inner = inner.replace("<title>Claude</title>", "").replace("<title>OpenAI</title>", "")
        fill = ' fill="currentColor"' if a == "chatgpt" else ""
        return f'<symbol id="logo-{a}" viewBox="0 0 24 24"{fill}>{inner}</symbol>'

    def cta(self, a, location, size="m", style="primary", scenario=None):
        """Assistant-specific connect button. Opens the setup card, or the verified connection URL directly."""
        c = self.conn[a]
        direct = c.get("heroCtaTarget") == "connection" and c.get("connectionUrl")
        href = c["connectionUrl"] if direct else f"#setup-{a}"
        attrs = f'href="{esc(href)}" data-assistant="{a}" data-location="{esc(location)}"'
        if scenario:
            attrs += f' data-scenario="{esc(scenario)}"'
        if direct:
            attrs += ' target="_blank" rel="noopener"'
        label = esc(self.copy["assistants"][a]["connect"])
        extra = f'<span class="sr-only"> {esc(self.copy["common"]["opensNewTab"])}</span>' if direct else ""
        return (f'<a class="btn btn-{size} btn-{style} btn-connect" {attrs}>'
                f'<span class="logo-chip">{self.logo(a)}</span><span>{label}</span>{extra}</a>')

    def cta_pair(self, location, size="m", style="primary", scenario=None, label=None):
        group = f' role="group" aria-label="{esc(label)}"' if label else ""
        return (f'<div class="cta-pair"{group}>'
                + "".join(self.cta(a, location, size, style, scenario) for a in ASSISTANTS) + "</div>")

    def copy_btn(self, target_id, prompt_id, location, size="s"):
        label = esc(self.copy["common"]["copyPrompt"])
        return (f'<button type="button" class="btn btn-{size} btn-secondary copy-btn" data-copy="{target_id}" '
                f'data-prompt-id="{esc(prompt_id)}" data-location="{esc(location)}" data-label="{label}">'
                f'{ICONS["copy"]}{ICONS["copied"]}<span class="copy-label">{label}</span></button>')

    def section_head(self, eyebrow, heading, hid, lead=None):
        lead_html = f'<p class="section-lead">{esc(lead)}</p>' if lead else ""
        return (f'<div class="section-head"><p class="eyebrow">{esc(eyebrow)}</p>'
                f'<h2 id="{hid}">{esc(heading)}</h2>{lead_html}</div>')

    # ---------- components ----------
    def header(self):
        n = self.copy["nav"]
        links = "".join(f'<li><a href="{esc(l["href"])}">{esc(l["label"])}</a></li>' for l in n["links"])
        return f'''<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="#main" aria-label="{esc(n["homeLabel"])}"><img src="../assets/logo-full.svg" alt="" width="144" height="28" /><span class="badge-mcp">{esc(n["badge"])}</span></a>
    <nav class="header-nav" id="site-menu" aria-label="{esc(n["label"])}">
      <ul class="nav-links">{links}</ul>
      <div class="nav-ctas">{"".join(self.cta(a, "header", size="s") for a in ASSISTANTS)}</div>
    </nav>
    <button type="button" class="menu-btn" aria-expanded="false" aria-controls="site-menu"><span class="sr-only">{esc(self.copy["common"]["menuOpen"])}</span>{ICONS["menu"]}</button>
  </div>
</header>'''

    def hero(self):
        h = self.copy["hero"]
        heads = h["headline"]
        exp = self.site["experiments"]["headline"]
        caps = "".join(f'<li>{ICONS["check"]}{esc(c)}</li>' for c in h["capabilities"])
        return f'''<section class="hero" aria-labelledby="hero-title">
  <div class="container hero-grid">
    <div class="hero-copy">
      <p class="eyebrow">{esc(h["eyebrow"])}</p>
      <h1 id="hero-title" data-variant-b="{esc(heads["b"])}">{esc(heads[exp["default"]])}</h1>
      <script>(function(){{var v=new URLSearchParams(location.search).get({json.dumps(exp["param"])});if(v==="b"){{var h=document.getElementById("hero-title");h.textContent=h.dataset.variantB;document.documentElement.dataset.variant="b";}}}})();</script>
      <p class="lead">{esc(h["lead"])}</p>
      {self.cta_pair("hero", label=h["ctaGroupLabel"])}
      <div class="hero-secondary">
        <a class="text-link" href="#demo">{esc(h["exampleLink"])} <span aria-hidden="true">↓</span></a>
        <p class="microcopy">{esc(h["microcopy"])}</p>
      </div>
      <ul class="capabilities">{caps}</ul>
    </div>
    <div class="hero-demo" id="demo">
      {self.product_demo()}
    </div>
  </div>
</section>'''

    def results_table(self, rows, caption, categories):
        c = self.copy["demo"]
        cols = c["columns"]
        body = []
        for i, r in enumerate(rows):
            initial = r["name"].replace("Demo:", "").strip()[:1]
            tone = TONES[categories.index(r["category"]) % len(TONES)]
            body.append(
                f'<tr><td data-label="{esc(cols["channel"])}"><span class="ch"><span class="ch-ava" aria-hidden="true" style="--c:var({AVATAR_COLORS[i % len(AVATAR_COLORS)]})">{esc(initial)}</span>{esc(r["name"])}</span></td>'
                f'<td data-label="{esc(cols["country"])}">{esc(r["country"])}</td>'
                f'<td data-label="{esc(cols["category"])}"><span class="chip {tone}">{esc(r["category"])}</span></td>'
                f'<td data-label="{esc(cols["link"])}"><span class="link-ph">{esc(c["linkPlaceholder"])}<span class="sr-only"> ({esc(c["linkNote"])})</span></span></td></tr>')
        head = "".join(f'<th scope="col">{esc(cols[k])}</th>' for k in ("channel", "country", "category", "link"))
        return (f'<div class="results-wrap"><table class="results"><caption class="sr-only">{esc(caption)}</caption>'
                f'<thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')

    def message(self, who, text, extra="", source=False):
        c = self.copy["demo"]
        if who == "user":
            return f'<div class="msg msg-user"><p class="msg-who">{esc(c["you"])}</p><p class="msg-text">{esc(text)}</p></div>'
        chip = (f'<span class="source-chip"><img src="../assets/logo-icon.svg" alt="" width="14" height="14" />{esc(c["source"])}</span>'
                if source else "")
        return f'<div class="msg msg-assistant"><p class="msg-who">{esc(c["assistant"])}{chip}</p><p>{esc(text)}</p>{extra}</div>'

    def product_demo(self):
        c = self.copy["demo"]
        scenarios = self.demo["scenarios"]
        if not self.demo.get("verified"):
            self.missing.append(("demo.json → verified, retrievedAt",
                                 "Optional: replace mock rows with a verified example and its retrieval date; confirm demo countries and categories exist in the catalog."))
        tabs, panels = [], []
        for i, s in enumerate(scenarios):
            sel = i == 0
            tabs.append(f'<button type="button" role="tab" class="demo-tab" id="tab-{s["id"]}" aria-controls="panel-{s["id"]}" '
                        f'aria-selected="{str(sel).lower()}" tabindex="{0 if sel else -1}" data-scenario="{s["id"]}">{esc(s["label"])}</button>')
            categories = list(dict.fromkeys(r["category"] for r in s["rows"]))
            narrowed = [r for r in s["rows"] if r["category"] == s["keepCategory"]]
            hidden = "" if sel else " hidden"
            panels.append(
                f'<div class="demo-panel" role="tabpanel" id="panel-{s["id"]}" aria-labelledby="tab-{s["id"]}" tabindex="0"{hidden}>'
                + self.message("user", s["prompt"])
                + self.message("assistant", s["response"], self.results_table(s["rows"], s["prompt"], categories), source=True)
                + self.message("user", s["followup"])
                + self.message("assistant", s["followupResponse"], self.results_table(narrowed, s["followup"], categories), source=True)
                + "</div>")
        return f'''<div class="demo" aria-labelledby="demo-title">
        <div class="demo-head"><h2 class="demo-title" id="demo-title">{esc(c["title"])}</h2><span class="badge-illustrative">{esc(c["badge"])}</span></div>
        <div class="demo-tabs" role="tablist" aria-label="{esc(c["selectorLabel"])}">{"".join(tabs)}</div>
        {"".join(panels)}
        <p class="demo-foot">{esc(c["footnote"])}</p>
      </div>
      <div class="demo-cta">
        <p class="demo-cta-title">{esc(c["ctaHeading"])}</p>
        {self.cta_pair("demo", scenario=scenarios[0]["id"])}
      </div>'''

    def how_it_works(self):
        h = self.copy["how"]
        steps = "".join(f'<li class="card step"><span class="step-num" aria-hidden="true">{i}</span><h3>{esc(s["title"])}</h3><p>{esc(s["text"])}</p></li>'
                        for i, s in enumerate(h["steps"], 1))
        return f'''<section class="section" id="how" aria-labelledby="how-title">
  <div class="container">
    {self.section_head(h["eyebrow"], h["heading"], "how-title", h["body"])}
    <ol class="steps">{steps}</ol>
    <p class="closing"><img src="../assets/logo-icon.svg" alt="" width="32" height="32" />{esc(h["closing"])}</p>
  </div>
</section>'''

    def use_cases(self):
        u = self.copy["useCases"]
        cards = []
        for item in u["items"]:
            if not self.enabled(item):
                continue
            pid = item["promptId"]
            tid = f"prompt-{pid}"
            cards.append(f'''<article class="card usecase">
        <span class="usecase-ico">{ICONS[item["icon"]]}</span>
        <h3>{esc(item["title"])}</h3>
        <p>{esc(item["text"])}</p>
        <div class="prompt-box"><p class="prompt-label">{esc(u["promptLabel"])}</p><p class="prompt-text" id="{tid}">{esc(self.prompts[pid]["text"])}</p></div>
        {self.copy_btn(tid, pid, "use_cases")}
      </article>''')
        return f'''<section class="section section-alt" id="use-cases" aria-labelledby="use-cases-title">
  <div class="container">
    {self.section_head(u["eyebrow"], u["heading"], "use-cases-title")}
    <div class="usecases">{"".join(cards)}</div>
  </div>
</section>'''

    def prompt_library(self):
        p = self.copy["promptLibrary"]
        items = [x for x in self.prompts.values() if x["group"] == "library" and self.enabled(x)]
        lis = "".join(f'''<li class="card prompt-item"><span class="prompt-num" aria-hidden="true">{i:02d}</span>
        <p class="prompt-text" id="prompt-{x["id"]}">{esc(x["text"])}</p>{self.copy_btn(f'prompt-{x["id"]}', x["id"], "prompt_library")}</li>'''
                      for i, x in enumerate(items, 1))
        links = "".join(f'<a class="text-link" href="#setup-{a}" data-assistant="{a}" data-location="prompt_library">{esc(self.copy["assistants"][a]["connect"])}</a>'
                        for a in ASSISTANTS)
        return f'''<section class="section" id="prompts" aria-labelledby="prompts-title">
  <div class="container">
    {self.section_head(p["eyebrow"], p["heading"], "prompts-title", p["lead"])}
    <ol class="prompt-list">{lis}</ol>
    <p class="prompt-connect"><span>{esc(p["connectLead"])}</span>{links}</p>
  </div>
</section>'''

    def setup_card(self, a):
        c = self.conn[a]
        L = self.copy["connect"]["labels"]
        status = c.get("status")
        status_html = (f'<span class="status status-{esc(status)}">{esc(self.copy["connect"]["status"].get(status, status))}</span>'
                       if status else self.dep(f"connections.json → {a}.status", f"{self.name(a)} availability status"))

        def fact(label, value, key, what):
            body = esc(value) if value else self.dep(key, what)
            return f"<div><dt>{esc(label)}</dt><dd>{body}</dd></div>"

        steps = ("<ol>" + "".join(f"<li>{esc(s)}</li>" for s in c["steps"]) + "</ol>" if c.get("steps")
                 else self.dep(f"connections.json → {a}.steps", f"Verified setup steps for {self.name(a)}"))
        server = ""
        if c.get("serverUrl"):
            sid = f"setup-{a}-server"
            server = (f'<div><dt>{esc(L["serverUrl"])}</dt><dd class="server-url"><code id="{sid}">{esc(c["serverUrl"])}</code>'
                      f'<button type="button" class="btn btn-s btn-secondary copy-btn" data-copy="{sid}" data-location="setup_{a}" '
                      f'data-label="{esc(L["copyAddress"])}" data-copied-label="{esc(L["addressCopied"])}">{ICONS["copy"]}{ICONS["copied"]}'
                      f'<span class="copy-label">{esc(L["copyAddress"])}</span></button></dd></div>')
        if c.get("connectionUrl"):
            action = (f'<a class="btn btn-m btn-primary btn-connect" href="{esc(c["connectionUrl"])}" target="_blank" rel="noopener" '
                      f'data-assistant="{a}" data-location="setup_{a}"><span class="logo-chip">{self.logo(a)}</span>'
                      f'<span>{esc(self.copy["assistants"][a]["connect"])}</span><span class="sr-only"> {esc(self.copy["common"]["opensNewTab"])}</span></a>')
        else:
            action = (f'<span class="btn btn-m btn-primary btn-connect" aria-disabled="true"><span class="logo-chip">{self.logo(a)}</span>'
                      f'<span>{esc(self.copy["assistants"][a]["connect"])}</span></span>'
                      + self.dep(f"connections.json → {a}.connectionUrl", f"{self.name(a)} connection URL (direct install or connector page)"))
        docs = (f'<a class="text-link" href="{esc(c["docsUrl"])}" target="_blank" rel="noopener">{esc(L["docs"])} {ICONS["external"]}'
                f'<span class="sr-only"> {esc(self.copy["common"]["opensNewTab"])}</span></a>'
                if c.get("docsUrl") else self.dep(f"connections.json → {a}.docsUrl", f"{self.name(a)} setup documentation URL"))
        pid = c["firstPromptId"]
        tid = f"setup-{a}-prompt"
        return f'''<article class="card setup-card" id="setup-{a}" data-assistant="{a}" aria-labelledby="setup-{a}-title">
        <div class="setup-head"><span class="setup-logo">{self.logo(a)}</span><h3 id="setup-{a}-title" tabindex="-1">{esc(self.name(a))}</h3>{status_html}</div>
        <dl class="facts">
          <div><dt>{esc(L["steps"])}</dt><dd>{steps}</dd></div>
          {server}
          {fact(L["auth"], c.get("authMethod"), f"connections.json → {a}.authMethod", f"{self.name(a)} authentication method")}
          {fact(L["account"], c.get("accountRequirements"), f"connections.json → {a}.accountRequirements", f"{self.name(a)} account requirements")}
          {fact(L["restrictions"], c.get("restrictions"), f"connections.json → {a}.restrictions", f"Known {self.name(a)} restrictions (or 'None known')")}
        </dl>
        <div class="first-prompt">
          <h4>{esc(L["firstPrompt"])}</h4>
          <p class="status-msg" aria-live="polite">{esc(self.copy["connect"]["afterConnect"])}</p>
          <div class="prompt-box"><p class="prompt-text" id="{tid}">{esc(self.prompts[pid]["text"])}</p>{self.copy_btn(tid, pid, f"setup_{a}")}</div>
        </div>
        <div class="setup-actions">{action}{docs}</div>
      </article>'''

    def connect_section(self):
        c = self.copy["connect"]
        return f'''<section class="section section-alt" id="connect" aria-labelledby="connect-title">
  <div class="container">
    {self.section_head(c["eyebrow"], c["heading"], "connect-title", c["lead"])}
    <div class="setup-grid">{"".join(self.setup_card(a) for a in ASSISTANTS)}</div>
  </div>
</section>'''

    def access_section(self):
        A = self.copy["access"]
        L = A["labels"]

        def row(label, value, key, what):
            return f'<div><dt>{esc(label)}</dt><dd>{esc(value) if value else self.dep(key, what)}</dd></div>'

        rows = [
            row(L["plan"], self.access.get("plan"), "access.json → plan", "Required Telemetrio plan"),
            row(L["usageLimits"], self.access.get("usageLimits"), "access.json → usageLimits", "Applicable usage limits"),
            row(L["trial"], self.access.get("trial"), "access.json → trial", "Trial availability (state 'No trial' if none)"),
        ]
        # Assistant account requirements repeat the setup-card values, so they are not recorded twice.
        for a in ASSISTANTS:
            value = self.conn[a].get("accountRequirements")
            if value:
                body = esc(value)
            elif self.preview:
                body = f'<p class="dep" role="note"><b>Launch dependency:</b> see {esc(self.name(a))} account requirements in the setup card.</p>'
            else:
                body = ""
            rows.append(f"<div><dt>{esc(L[a])}</dt><dd>{body}</dd></div>")
        return f'''<section class="section" id="access" aria-labelledby="access-title">
  <div class="container access-grid">
    <div class="access-intro"><p class="eyebrow">{esc(A["eyebrow"])}</p><h2 id="access-title">{esc(A["heading"])}</h2><p>{esc(A["compatibility"])}</p></div>
    <dl class="card access-list">{"".join(rows)}</dl>
  </div>
</section>'''

    def faq_answer(self, item):
        if item.get("a"):
            # A "verify" key means the copy is approved in principle but must be checked; remove it once verified.
            note = self.dep(f"copy.json → faq.{item['id']}.verify", item["verify"]) if item.get("verify") else ""
            return f'<p>{esc(item["a"])}</p>{note}'
        if item["id"] == "cost" and self.access.get("faqCost"):
            return f'<p>{esc(self.access["faqCost"])}</p>'
        if item["id"] == "disconnect" and all(self.conn[a].get("disconnectSteps") for a in ASSISTANTS):
            return "".join(f'<h4>{esc(self.name(a))}</h4><ol>' + "".join(f"<li>{esc(s)}</li>" for s in self.conn[a]["disconnectSteps"]) + "</ol>"
                           for a in ASSISTANTS)
        return self.dep(f"FAQ · {item['q']}", item["pending"])

    def faq(self):
        f = self.copy["faq"]
        items = "".join(f'<details><summary>{esc(i["q"])}</summary><div class="answer">{self.faq_answer(i)}</div></details>' for i in f["items"])
        return f'''<section class="section section-alt" id="faq" aria-labelledby="faq-title">
  <div class="container">
    {self.section_head(f["eyebrow"], f["heading"], "faq-title")}
    <div class="faq">{items}</div>
  </div>
</section>'''

    def final_cta(self):
        f = self.copy["final"]
        summary = (f'<p class="access-summary">{esc(self.access["summary"])}</p>' if self.access.get("summary")
                   else self.dep("access.json → summary", "Concise, verified access requirements shown under the final buttons"))
        return f'''<section class="section" aria-labelledby="final-title">
  <div class="container">
    <div class="final">
      <h2 id="final-title">{esc(f["heading"])}</h2>
      <p>{esc(f["text"])}</p>
      {self.cta_pair("final", style="secondary")}
      {summary}
    </div>
  </div>
</section>'''

    def footer(self):
        f = self.copy["footer"]
        links = [f'<a href="{esc(self.site["telemetrioUrl"])}">{esc(f["telemetrioLink"])}</a>']
        for key, label in (("privacyUrl", f["privacy"]), ("termsUrl", f["terms"])):
            if self.site.get(key):
                links.append(f'<a href="{esc(self.site[key])}">{esc(label)}</a>')
            else:
                self.missing.append((f"site.json → {key}", f"{label} URL"))
        return f'''<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div><a class="brand" href="#main" aria-label="{esc(self.copy["nav"]["homeLabel"])}"><img src="../assets/logo-full.svg" alt="" width="123" height="24" style="height:24px" /><span class="badge-mcp">{esc(self.copy["nav"]["badge"])}</span></a><p>{esc(f["positioning"])}</p></div>
      <nav class="footer-links" aria-label="Footer">{"".join(links)}</nav>
    </div>
    <p class="footer-legal">{esc(f["copyright"])} · {esc(f["trademarks"])}</p>
  </div>
</footer>'''

    # ---------- document ----------
    def render(self):
        m = self.copy["meta"]
        url = self.site.get("productionUrl") if not self.preview else self.site["previewUrl"]
        if not self.site.get("productionUrl"):
            self.missing.append(("site.json → productionUrl", "Production URL (canonical), e.g. https://telemetr.io/mcp"))
            url = url or self.site["previewUrl"]
        if not self.site.get("ogImage"):
            self.missing.append(("site.json → ogImage", "Optional: social sharing image (1200×630)"))
        icons = "".join(self.logo_symbol(a) for a in ASSISTANTS)
        body = "\n".join([
            self.header(),
            '<main id="main">',
            self.hero(), self.how_it_works(), self.use_cases(), self.prompt_library(),
            self.connect_section(), self.access_section(), self.faq(), self.final_cta(),
            "</main>",
            self.footer(),
        ])
        runtime = {
            "statusEndpoint": self.site.get("connectionStatusEndpoint"),
            "analytics": self.site["analytics"],
            "experiment": self.site["experiments"]["headline"],
            "strings": {k: self.copy["common"][k] for k in ("copied", "copyFailed", "menuOpen", "menuClose")}
                       | {"connected": self.copy["connect"]["connected"]},
            "scenarios": {s["id"]: s["prompt"] for s in self.demo["scenarios"]},
        }
        ld = {
            "@context": "https://schema.org", "@type": "WebPage", "name": m["title"], "description": m["description"],
            "url": url, "inLanguage": self.copy["lang"],
            "publisher": {"@type": "Organization", "name": "Telemetrio", "url": self.site["telemetrioUrl"]},
        }
        og_image = (f'<meta property="og:image" content="{esc(self.site["ogImage"])}" />\n'
                    '<meta name="twitter:card" content="summary_large_image" />') if self.site.get("ogImage") else '<meta name="twitter:card" content="summary" />'
        robots = '<meta name="robots" content="noindex" />\n' if self.preview else ""
        preview_bar = (f'<div class="preview-bar" role="note"><div class="container">{esc(self.copy["common"]["previewBar"])}</div></div>'
                       if self.preview else "")
        css = (ROOT.parent / "assets/tokens.css").read_text(encoding="utf-8") + (ROOT / "src/mcp.css").read_text(encoding="utf-8")
        js = (ROOT / "src/mcp.js").read_text(encoding="utf-8")
        exp = self.site["experiments"]["headline"]
        return f'''<!doctype html>
<html lang="{esc(self.copy["lang"])}" data-variant="{esc(exp["default"])}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(m["title"])}</title>
<meta name="description" content="{esc(m["description"])}" />
{robots}<link rel="canonical" href="{esc(url)}" />
<meta property="og:type" content="website" />
<meta property="og:url" content="{esc(url)}" />
<meta property="og:title" content="{esc(m["title"])}" />
<meta property="og:description" content="{esc(m["description"])}" />
<meta property="og:site_name" content="Telemetrio" />
<meta property="og:locale" content="en_US" />
{og_image}
<meta name="theme-color" content="#006dda" />
<link rel="icon" type="image/svg+xml" href="../assets/logo-icon.svg" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap" rel="stylesheet" />
<style>
{css}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">{esc(self.copy["common"]["skip"])}</a>
<svg width="0" height="0" style="position:absolute" aria-hidden="true">{icons}</svg>
{preview_bar}
{body}
<p class="sr-only" aria-live="polite" id="live"></p>
<script type="application/json" id="mcp-config">{json.dumps(runtime, ensure_ascii=False)}</script>
<script>
{js}</script>
</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=("preview", "production"), default="preview")
    ap.add_argument("--lang", default="en")
    args = ap.parse_args()
    page = Page(args.mode, args.lang)
    out = page.render()
    required = [m for m in page.missing if not m[1].startswith("Optional")]
    optional = [m for m in page.missing if m[1].startswith("Optional")]
    if required:
        print(f"{len(required)} launch value(s) missing:", file=sys.stderr)
        for key, what in required:
            print(f"  - {what}  [{key}]", file=sys.stderr)
    for key, what in optional:
        print(f"  ~ {what}  [{key}]", file=sys.stderr)
    if args.mode == "production" and required:
        print("Production build stopped: fill the values above with verified information.", file=sys.stderr)
        return 1
    (ROOT / "index.html").write_text(out, encoding="utf-8")
    print(f"Wrote {ROOT / 'index.html'} ({args.mode})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
