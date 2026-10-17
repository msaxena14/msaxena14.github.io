#!/usr/bin/env python3
"""Regenerate the Investigations content from Investigations/*.md.

Each file is one case. The filename (minus .md) is the headline; the file body is the write-up.
Optional front-matter between '---' lines: severity, tags (comma separated), date (YYYY-MM-DD), summary,
featured (true = show as a teaser on the homepage; if no case is featured, the newest one is shown).
Sections named Symptom / Investigation / Fix / Impact fill the four-step layout; any other
section is shown full-width below them.

Run from the repo root:  python3 scripts/build_investigations.py
Rewrites the regions between the INVESTIGATIONS:START / INVESTIGATIONS:END markers in
investigations.html and index.html. Standard library only.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Investigations"
STEPS = ["Symptom", "Investigation", "Fix", "Impact"]
CHEV = ('<svg class="case-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>')
GO = ('<svg class="case-go" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" '
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>')


def esc(s):
    return html.escape(s, quote=True)


def slugify(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def inline(text):
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            out.append("<code>%s</code>" % esc(p[1:-1]))
            continue
        p = esc(p)
        p = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", p)
        p = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', p)
        out.append(p)
    return "".join(out)


def markdown(block):
    """Tiny markdown subset: paragraphs, bullet/numbered lists, fenced code, inline code/bold/links."""
    out, para, items, kind, code = [], [], [], None, None

    def flush_para():
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para.clear()

    def flush_list():
        nonlocal kind
        if items:
            tag = "ol" if kind == "ol" else "ul"
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(i) for i in items), tag))
            items.clear()
        kind = None

    for line in block.split("\n"):
        if code is not None:
            if line.strip().startswith("```"):
                out.append("<pre><code>%s</code></pre>" % esc("\n".join(code)))
                code = None
            else:
                code.append(line)
            continue
        if line.strip().startswith("```"):
            flush_para(); flush_list(); code = []
            continue
        m = re.match(r"^\s*([-*]|\d+\.)\s+(.*)$", line)
        if m:
            flush_para()
            k = "ol" if m.group(1)[0].isdigit() else "ul"
            if kind and kind != k:
                flush_list()
            kind = k
            items.append(m.group(2))
        elif not line.strip():
            flush_para(); flush_list()
        else:
            flush_list()
            para.append(line.strip())
    if code is not None:
        out.append("<pre><code>%s</code></pre>" % esc("\n".join(code)))
    flush_para(); flush_list()
    return "\n".join(out)


def parse(path):
    raw = path.read_text(encoding="utf-8")
    meta, body = {}, raw
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", raw, re.S)
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip()
        body = m.group(2)
    sections, current, buf = {}, None, []
    order = []
    for line in body.split("\n"):
        h = re.match(r"^##\s+(.*?)\s*$", line)
        if h:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current, buf = h.group(1), []
            order.append(current)
        else:
            buf.append(line)
    if current is None:
        sections[""] = body.strip()
        order = [""]
    else:
        sections[current] = "\n".join(buf).strip()
    title = path.stem
    summary = meta.get("summary")
    if not summary:
        first = sections.get("Symptom") or next(iter(sections.values()), "")
        first = re.sub(r"\s+", " ", first.split("\n\n")[0])
        summary = first if len(first) <= 170 else first[:167].rsplit(" ", 1)[0] + "…"
    tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    return {
        "title": title, "slug": slugify(title), "severity": meta.get("severity", ""),
        "tags": tags, "date": meta.get("date", ""), "summary": summary,
        "featured": meta.get("featured", "").lower() in ("true", "yes", "1"),
        "sections": sections, "order": order,
    }


def tags_html(tags):
    if not tags:
        return ""
    return '<ul class="tags" aria-label="Technologies">%s</ul>' % "".join('<li class="tag">%s</li>' % esc(t) for t in tags)


def case_html(c, is_open):
    steps = []
    for name in STEPS:
        if c["sections"].get(name):
            cls = "step impact" if name == "Impact" else "step"
            steps.append('<div class="%s"><h4>%s</h4>%s</div>' % (cls, name, markdown(c["sections"][name])))
    for name in c["order"]:
        if name not in STEPS and c["sections"].get(name):
            head = "<h4>%s</h4>" % esc(name) if name else ""
            steps.append('<div class="step extra">%s%s</div>' % (head, markdown(c["sections"][name])))
    sev = '<span class="case-sev">%s</span>' % esc(c["severity"]) if c["severity"] else ""
    return (
        '<details class="case" id="%s"%s>\n'
        '  <summary>\n'
        '    <span class="case-title"><h3>%s</h3><p>%s</p></span>\n'
        '    %s\n    %s\n'
        '  </summary>\n'
        '  <div class="case-body">\n    %s\n    %s\n  </div>\n'
        '</details>'
    ) % (c["slug"], " open" if is_open else "", esc(c["title"]), esc(c["summary"]), sev, CHEV,
         "\n    ".join(steps), tags_html(c["tags"]))


def card_html(c):
    sev = '<span class="case-sev">%s</span>' % esc(c["severity"]) if c["severity"] else ""
    return (
        '<a class="case-card" href="investigations.html#%s">\n'
        '  <span class="case-title">\n    <h3>%s</h3>\n    <p>%s</p>\n    %s\n  </span>\n'
        '  %s\n  %s\n</a>'
    ) % (c["slug"], esc(c["title"]), esc(c["summary"]), tags_html(c["tags"][:4]), sev, GO)


def replace_region(path, new, indent):
    text = path.read_text(encoding="utf-8")
    pat = re.compile(r"(<!-- INVESTIGATIONS:START -->).*?(\n\s*<!-- INVESTIGATIONS:END -->)", re.S)
    if not pat.search(text):
        sys.exit("Markers not found in %s" % path.name)
    pad = " " * indent
    body = "\n".join(pad + l if l else l for l in new.split("\n"))
    path.write_text(pat.sub(lambda m: m.group(1) + "\n" + body + m.group(2), text), encoding="utf-8")


def main():
    files = sorted(SRC.glob("*.md"))
    if not files:
        sys.exit("No .md files in %s" % SRC)
    cases = [parse(f) for f in files]
    cases.sort(key=lambda c: (c["date"], c["title"]), reverse=True)

    replace_region(ROOT / "investigations.html",
                   "\n".join(case_html(c, i == 0) for i, c in enumerate(cases)), 8)
    shown = [c for c in cases if c["featured"]] or cases[:1]
    replace_region(ROOT / "index.html", "\n".join(card_html(c) for c in shown), 8)

    index = (ROOT / "index.html").read_text(encoding="utf-8")
    label = "All investigations (%d) →" % len(cases)
    index = re.sub(r'(<a class="btn btn-ghost" href="investigations.html">)[^<]*(</a>)',
                   lambda m: m.group(1) + label + m.group(2), index)
    (ROOT / "index.html").write_text(index, encoding="utf-8")
    print("Built %d case(s); %d featured on the homepage." % (len(cases), len(shown)))
    for c in cases:
        print(" -", c["date"] or "no date", "|", c["title"])


if __name__ == "__main__":
    main()
