"""Alternative Telemetrio MCP landing page (mcp/alt/index.html).

Concept: the visitor writes their first search on the page (prompt builder), then steps
through a refinement walkthrough. Setup cards, access terms, FAQ and footer are shared
with the main page, so verified launch values only need to be entered once.
"""
from .page import ASSISTANTS, AVATAR_COLORS, ICONS, Page, esc, load

X_ICON = '<svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>'
ARROW = '<svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
CRITERIA_KEYS = ("countries", "categories", "format")


class AltPage(Page):
    slug = "alt"
    out_path = "alt/index.html"
    asset = "../../assets/"
    extra_css = ("src/alt.css",)
    extra_js = ("src/alt.js",)

    def __init__(self, mode, lang):
        super().__init__(mode, lang)
        content = f"content/{lang}"
        self.alt = load(f"{content}/copy-alt.json")
        self.builder_opts = load(f"{content}/builder.json")
        self.refine_data = load(f"{content}/refine.json")

    def meta(self):
        return self.alt["meta"]

    def nav_links(self):
        return self.alt["nav"]

    # ---------- prompt builder ----------
    def compose(self, sel):
        """Same composition rule as src/alt.js; keep the two in sync."""
        s = self.alt["builder"]["sentence"]
        o = {k: next(x for x in self.builder_opts[k] if x["id"] == sel[k]) for k in ("category", "country", "goal", "format")}
        return f'{s["start"]} {o["category"]["label"]} {s["in"]} {o["country"]["label"]}{o["goal"]["phrase"]}{s["end"]} {o["format"]["phrase"]}'

    def builder_prompt_id(self, sel):
        return "builder:" + "-".join(sel[k] for k in ("category", "country", "goal", "format"))

    def builder_preview(self, sel):
        cat = next(x for x in self.builder_opts["category"] if x["id"] == sel["category"])
        country = next(x for x in self.builder_opts["country"] if x["id"] == sel["country"])
        rows = [{"name": n.replace("{name}", cat["name"]), "country": country["name"], "category": cat["name"]}
                for n in self.builder_opts["previewNames"]]
        return self.results_table(rows, self.compose(sel), [cat["name"]])

    def builder(self):
        b = self.alt["builder"]
        if not self.builder_opts.get("verified"):
            self.dep("builder.json → verified", "Prompt builder countries and categories must exist in the Telemetrio catalog")
        sel = {k: self.builder_opts[k][0]["id"] for k in ("category", "country", "goal", "format")}

        def pick(field):
            opts = "".join(f'<option value="{esc(o["id"])}">{esc(o["label"])}</option>' for o in self.builder_opts[field])
            return (f'<label class="pick"><span class="sr-only">{esc(b["labels"][field])}</span>'
                    f'<select data-field="{field}">{opts}</select></label>')

        s = b["sentence"]
        pid = self.builder_prompt_id(sel)
        links = "".join(
            f'<a class="text-link" href="#setup-{a}" data-assistant="{a}" data-location="builder" data-prompt-from="builder-prompt">'
            f'{esc(self.copy["assistants"][a]["connect"])}</a>' for a in ASSISTANTS)
        return f'''<div class="card builder" id="builder" aria-labelledby="builder-title">
      <div class="builder-compose">
        <h2 class="builder-title" id="builder-title">{esc(b["title"])}</h2>
        <p class="builder-intro">{esc(b["intro"])}</p>
        <p class="sentence">{esc(s["start"])} {pick("category")} {esc(s["in"])} {pick("country")} {pick("goal")} {pick("format")}<span aria-hidden="true">{esc(s["end"])}</span></p>
        <div class="prompt-box builder-output">
          <p class="prompt-label" id="builder-prompt-label">{esc(b["promptLabel"])}</p>
          <p class="prompt-text" id="builder-prompt" data-prompt-id="{esc(pid)}" aria-live="polite" aria-labelledby="builder-prompt-label">{esc(self.compose(sel))}</p>
        </div>
        <div class="builder-actions">{self.copy_btn("builder-prompt", pid, "builder", size="m")}</div>
        <p class="builder-connect"><span>{esc(b["connectLead"])}</span>{links}</p>
      </div>
      <div class="builder-preview" aria-labelledby="builder-preview-title">
        <div class="preview-head"><h3 id="builder-preview-title">{esc(b["previewLabel"])}</h3><span class="badge-illustrative">{esc(b["previewBadge"])}</span></div>
        <div id="builder-preview-body">{self.builder_preview(sel)}</div>
        <p class="preview-note">{esc(b["previewNote"])}</p>
      </div>
    </div>'''

    def hero(self):
        h = self.alt["hero"]
        return f'''<section class="alt-hero" aria-labelledby="hero-title">
  <div class="container alt-hero-head">
    <p class="eyebrow">{esc(h["eyebrow"])}</p>
    <h1 id="hero-title">{esc(h["headline"])}</h1>
    <p class="lead">{esc(h["lead"])}</p>
    {self.cta_pair("hero", label=self.copy["hero"]["ctaGroupLabel"])}
    <p class="microcopy">{esc(h["microcopy"])}</p>
  </div>
  <div class="container">
    {self.builder()}
  </div>
</section>'''

    # ---------- refinement walkthrough ----------
    def refine(self):
        R = self.alt["refine"]
        steps = self.refine_data["steps"]
        if not self.refine_data.get("verified"):
            self.dep("refine.json → verified", "Confirm conversational refinement and table output work in both assistants")
        categories = list(dict.fromkeys(r["category"] for st in steps for r in st["rows"]))
        tabs, panels = [], []
        prev = None
        for i, st in enumerate(steps):
            sel = i == 0
            tabs.append(
                f'<li role="presentation"><button type="button" role="tab" class="refine-step" id="rstep-{st["id"]}" '
                f'aria-controls="rpanel-{st["id"]}" aria-selected="{str(sel).lower()}" tabindex="{0 if sel else -1}" data-step="{st["id"]}">'
                f'<span class="refine-num" aria-hidden="true">{i + 1}</span><span class="refine-prompt">{esc(st["prompt"])}</span></button></li>')
            crit = []
            for key in CRITERIA_KEYS:
                cur = st["criteria"][key]
                before = prev["criteria"][key] if prev else cur
                chips = [f'<span class="crit{" is-added" if prev and v not in before else ""}">{esc(v)}'
                         f'{"<span class=sr-only> (" + esc(R["added"]) + ")</span>" if prev and v not in before else ""}</span>' for v in cur]
                chips += [f'<span class="crit is-removed">{esc(v)}<span class="sr-only"> ({esc(R["removed"])})</span></span>'
                          for v in before if v not in cur]
                crit.append(f'<div><dt>{esc(R["criteria"][key])}</dt><dd>{"".join(chips)}</dd></div>')
            count = R["channelsCount"].replace("{n}", str(len(st["rows"])))
            panels.append(
                f'<div class="refine-panel" role="tabpanel" id="rpanel-{st["id"]}" aria-labelledby="rstep-{st["id"]}" tabindex="0"{"" if sel else " hidden"}>'
                f'<p class="refine-reply"><img src="{self.asset}logo-icon.svg" alt="" width="20" height="20" />{esc(st["reply"])}</p>'
                f'<div class="criteria"><p class="criteria-label">{esc(R["criteriaLabel"])}</p><dl>{"".join(crit)}</dl></div>'
                f'<div class="refine-results-head"><span>{esc(R["resultsLabel"])}</span><span>{esc(count)}</span></div>'
                f'{self.results_table(st["rows"], st["prompt"], categories, group_by=st.get("groupBy"))}'
                f'</div>')
            prev = st
        return f'''<section class="section section-alt" id="refine" aria-labelledby="refine-title">
  <div class="container">
    <div class="section-head"><p class="eyebrow">{esc(R["eyebrow"])}</p><h2 id="refine-title">{esc(R["heading"])}</h2><p class="section-lead">{esc(R["lead"])}</p></div>
    <div class="card refine">
      <div class="refine-side">
        <div class="refine-side-head"><p class="refine-side-title" id="refine-steps-label">{esc(R["stepsLabel"])}</p><span class="badge-illustrative">{esc(R["badge"])}</span></div>
        <ol class="refine-steps" role="tablist" aria-orientation="vertical" aria-labelledby="refine-steps-label">{"".join(tabs)}</ol>
        <button type="button" class="btn btn-s btn-secondary refine-next" data-next="{esc(R["next"])}" data-restart="{esc(R["restart"])}"><span class="refine-next-label">{esc(R["next"])}</span>{ARROW}</button>
      </div>
      <div class="refine-main">{"".join(panels)}</div>
    </div>
  </div>
</section>'''

    # ---------- prompt anatomy ----------
    def anatomy(self):
        A = self.alt["anatomy"]
        parts = "".join(f'<mark class="tag tag-{p["tag"]}">{esc(p["text"])}</mark>' if p.get("tag") else esc(p["text"])
                        for p in A["parts"])
        text = "".join(p["text"] for p in A["parts"])
        legend = "".join(f'<div><dt><span class="swatch tag-{k}" aria-hidden="true"></span>{esc(v["label"])}</dt><dd>{esc(v["text"])}</dd></div>'
                         for k, v in A["tags"].items())
        return f'''<section class="section" id="anatomy" aria-labelledby="anatomy-title">
  <div class="container anatomy-grid">
    <div class="section-head"><p class="eyebrow">{esc(A["eyebrow"])}</p><h2 id="anatomy-title">{esc(A["heading"])}</h2><p class="section-lead">{esc(A["lead"])}</p></div>
    <div class="card anatomy">
      <p class="anatomy-prompt">{parts}</p>
      <p class="sr-only" id="prompt-anatomy">{esc(text)}</p>
      {self.copy_btn("prompt-anatomy", "anatomy", "anatomy")}
      <dl class="anatomy-legend">{legend}</dl>
    </div>
  </div>
</section>'''

    # ---------- audiences ----------
    def audiences(self):
        A = self.alt["audiences"]
        cards = "".join(f'''<article class="card audience">
        <h3>{esc(it["title"])}</h3><p>{esc(it["text"])}</p>
        <div class="prompt-box"><p class="prompt-label">{esc(self.copy["useCases"]["promptLabel"])}</p><p class="prompt-text" id="prompt-aud-{it["id"]}">{esc(self.prompts[it["promptId"]]["text"])}</p></div>
        {self.copy_btn(f'prompt-aud-{it["id"]}', it["promptId"], "audiences")}
      </article>''' for it in A["items"])
        return f'''<section class="section section-alt" id="audiences" aria-labelledby="audiences-title">
  <div class="container">
    {self.section_head(A["eyebrow"], A["heading"], "audiences-title")}
    <div class="audiences">{cards}</div>
  </div>
</section>'''

    # ---------- scope ----------
    def scope(self):
        S = self.alt["scope"]
        does = "".join(f'<li>{ICONS["check"]}<span>{esc(x)}</span></li>' for x in S["does"])
        doesnt = "".join(f'<li>{X_ICON}<span>{esc(x)}</span></li>' for x in S["doesnt"])
        return f'''<section class="section" id="scope" aria-labelledby="scope-title">
  <div class="container">
    {self.section_head(S["eyebrow"], S["heading"], "scope-title")}
    <div class="scope">
      <div class="card scope-col scope-does"><h3>{esc(S["doesLabel"])}</h3><ul>{does}</ul></div>
      <div class="card scope-col scope-doesnt"><h3>{esc(S["doesntLabel"])}</h3><ul>{doesnt}</ul></div>
    </div>
  </div>
</section>'''

    # ---------- connection + access ----------
    def connect_section(self):
        C = self.alt["connect"]
        return f'''<section class="section section-alt" id="connect" aria-labelledby="connect-title">
  <div class="container">
    {self.section_head(C["eyebrow"], C["heading"], "connect-title", C["lead"])}
    <div class="setup-grid">{"".join(self.setup_card(a) for a in ASSISTANTS)}</div>
    <div class="card access-inline" id="access" aria-labelledby="access-title">
      <div class="access-inline-head"><h3 id="access-title">{esc(C["accessHeading"])}</h3><p>{esc(self.copy["access"]["compatibility"])}</p></div>
      <dl class="access-list">{self.access_rows()}</dl>
    </div>
  </div>
</section>'''

    def final_cta(self):
        f = self.alt["final"]
        summary = (f'<p class="access-summary">{esc(self.access["summary"])}</p>' if self.access.get("summary")
                   else self.dep("access.json → summary", "Concise, verified access requirements shown under the final buttons"))
        return f'''<section class="section" aria-labelledby="final-title">
  <div class="container">
    <div class="final final-dark">
      <h2 id="final-title">{esc(f["heading"])}</h2>
      <p>{esc(f["text"])}</p>
      {self.cta_pair("final", style="secondary")}
      {summary}
    </div>
  </div>
</section>'''

    def sections(self):
        return [self.hero(), self.refine(), self.anatomy(), self.audiences(), self.scope(),
                self.connect_section(), self.faq(alt=False), self.final_cta()]

    def extra_runtime(self):
        b = self.alt["builder"]
        d = self.copy["demo"]
        return {"builder": {
            "options": {k: self.builder_opts[k] for k in ("category", "country", "goal", "format")},
            "sentence": b["sentence"],
            "previewNames": self.builder_opts["previewNames"],
            "columns": d["columns"],
            "linkPlaceholder": d["linkPlaceholder"],
            "linkNote": d["linkNote"],
            "avatarColors": AVATAR_COLORS,
        }}
