#!/usr/bin/env python3
"""The Capital Suite editorial style: a stat card, a daily chart and three badges.

charts/brand/card.svg           30-day hero number, source split, stat band
charts/brand/daily.svg          daily tokens, stacked by source
charts/badge/brand-tokens-30d.svg
charts/badge/brand-api-30d.svg
charts/badge/brand-streak.svg

Visual language (palette locked 2026-07-12): light editorial base, ONE accent
(amber), no gradients, no shadows, hairline rules. Newsreader sets numbers and
titles, Inter sets labels. Both are outlined glyphs from scripts/brandfont.py,
because an <img>-embedded SVG on GitHub cannot load a webfont.

Two series, one accent: Claude Code wears the amber, Codex wears ink. They differ
in hue AND lightness, are always stacked in the same order, and are named
directly, so identity never rests on colour alone.

Dark mode follows prefers-color-scheme (the OS/browser setting; an <img> SVG
cannot see GitHub's own theme toggle). The dark palette is the brand's reserved
dark-editorial alternate; its body, muted, border and Codex values are derived,
not locked, so check them before treating them as brand-final.

Deterministic: same data -> same bytes (the `generated` stamp is the only
varying text). Python 3.9, standard library only. `import render` and
`import brandfont` work because scripts/ is on sys.path.
"""

import datetime as dt

import brandfont as bf
import render

# ----------------------------------------------------------------- brand knobs

BRAND_TAG = "THECAPITALSUITE.CO"     # small right-hand tag; "" to drop it
# Which brand amber paints the Claude Code marks. "amber" is the locked FILL
# colour. "amberdeep" is the locked ACCENT-TEXT colour: darker, so it clears the
# 3:1 non-text contrast bar on Paper that plain amber misses, at the cost of
# bending the "amber for fills" rule. Default stays on the brand rule.
MARK = "amber"

LIGHT = {
    "paper": "#F6F1E7", "paper2": "#EFE8D9", "surface": "#FFFDF8",
    "ink": "#1B1712", "body": "#3A342C", "muted": "#6E655A", "border": "#E4DBC9",
    "amber": "#C98F2A", "amberdeep": "#B26D12",
    "codex": "#3A342C",
}
DARK = {
    "paper": "#0E0D0B", "paper2": "#16140F", "surface": "#16140F",
    "ink": "#ECE7DB", "body": "#CFC8B8", "muted": "#9A9282", "border": "#2B2720",
    "amber": "#E5A93C", "amberdeep": "#E5A93C",
    "codex": "#645F54",
}

W = 880
FACE_ID = {"serif": "a", "serif_i": "b", "sans": "c"}


# ------------------------------------------------------------------ svg canvas


def _n(v):
    s = "{:.2f}".format(v).rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def _css():
    def block(t):
        d = dict(t)
        d["claude"] = d[MARK]
        return "".join("--{}:{};".format(k, v) for k, v in d.items())
    return (
        "svg{{{}}}@media (prefers-color-scheme:dark){{svg{{{}}}}}"
        ".bg{{fill:var(--paper)}}.plate{{fill:var(--paper2)}}"
        ".ink{{fill:var(--ink)}}.body{{fill:var(--body)}}.mut{{fill:var(--muted)}}"
        ".brd{{fill:var(--border)}}.amb{{fill:var(--amber)}}"
        ".claude{{fill:var(--claude)}}.codex{{fill:var(--codex)}}"
        ".frame{{fill:none;stroke:var(--border);stroke-width:1;shape-rendering:crispEdges}}"
        ".hl{{stroke:var(--border);stroke-width:1;shape-rendering:crispEdges}}"
        ".bar{{shape-rendering:crispEdges}}.wip{{opacity:.55}}"
    ).format(block(LIGHT), block(DARK))


class Canvas(object):
    """Collects shapes and outlined text; emits each used glyph once in <defs>."""

    def __init__(self, w, h, label):
        self.w, self.h, self.label = w, h, label
        self.body = []
        self.used = set()

    def add(self, s):
        self.body.append(s)

    def rect(self, x, y, w, h, cls, extra=""):
        self.add('<rect class="{}" x="{}" y="{}" width="{}" height="{}"{}/>'.format(
            cls, _n(x), _n(y), _n(w), _n(h), extra))

    def line(self, x1, y1, x2, y2):
        self.add('<line class="hl" x1="{}" y1="{}" x2="{}" y2="{}"/>'.format(
            _n(x1), _n(y1), _n(x2), _n(y2)))

    def text(self, face, s, x, y, size, cls, anchor="start", tracking=0.0):
        """Baseline-anchored outlined text. Returns its width in px."""
        s = str(s)
        width = bf.measure(face, s, size, tracking)
        if anchor == "middle":
            x -= width / 2.0
        elif anchor == "end":
            x -= width
        k = size / float(bf.UPM)
        scale = "{:.5f}".format(k).rstrip("0")
        adv = bf.FACES[face]["adv"]
        glyphs = bf.FACES[face]["d"]
        parts = ['<g class="{}">'.format(cls)]
        cx = x
        for ch in s:
            if ch in glyphs:
                self.used.add((face, ch))
                parts.append('<use xlink:href="#{}{:x}" transform="translate({} {}) scale({})"/>'.format(
                    FACE_ID[face], ord(ch), _n(cx), _n(y), scale))
            cx += adv.get(ch, adv["?"]) * k + tracking
        parts.append("</g>")
        self.add("".join(parts))
        return width

    def finish(self):
        defs = "".join('<path id="{}{:x}" d="{}"/>'.format(FACE_ID[f], ord(c), bf.FACES[f]["d"][c])
                       for f, c in sorted(self.used))
        head = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{a}">'
                '<title>{a}</title><style>{css}</style><defs>{defs}</defs>'
                '<rect class="bg" width="{w}" height="{h}"/>').format(
                    w=self.w, h=self.h, a=render.esc(self.label), css=_css(), defs=defs)
        return head + "\n".join(self.body) + "</svg>"


# ------------------------------------------------------------------- the stats


def _stats(days):
    rows = render.bucket(days, render.DAYS)
    tokens = [sum(r[s]["total"] for s, _ in render.SERIES) for r in rows]
    total = sum(tokens)
    cost = sum(sum(r[s]["costUSD"] for s, _ in render.SERIES) for r in rows)
    ct = sum(r["claude"]["total"] for r in rows)
    xt = sum(r["codex"]["total"] for r in rows)
    active = sum(1 for t in tokens if t > 0)
    peak = max(tokens + [0])
    streak = 0
    if days:
        cur = max(dt.date.fromisoformat(d) for d in days)
        while cur.isoformat() in days and render.day_total(days[cur.isoformat()]) > 0:
            streak += 1
            cur -= dt.timedelta(days=1)
    return {
        "rows": rows, "tokens": tokens, "total": total, "cost": cost, "ct": ct, "xt": xt,
        "active": active, "peak": peak,
        "peak_day": rows[tokens.index(peak)]["start"] if peak else None,
        "avg": total / float(active) if active else 0, "streak": streak,
    }


def _pct(part, whole):
    return int(round(100.0 * part / whole)) if whole else 0


def _day_label(d):
    return d.strftime("%b %d").upper().replace(" 0", " ")


# ------------------------------------------------------------------- the card

CARD_H = 324
PAD = 40


def build_card(st, generated):
    rows = st["rows"]
    n = len(rows)
    label = ("AI coding usage over the last {} days: {} tokens, {} API-equivalent, "
             "Claude Code {}%, Codex {}%, best day {}, {} of {} days active, {} day streak").format(
                 n, render.fmt_hero(st["total"]), render.compact_cost(st["cost"]),
                 _pct(st["ct"], st["total"]), _pct(st["xt"], st["total"]),
                 render.compact_tokens(st["peak"]), st["active"], n, st["streak"])
    c = Canvas(W, CARD_H, label)
    right = W - PAD

    c.rect(0, 0, W, 4, "amb")
    c.add('<rect class="frame" x=".5" y=".5" width="{}" height="{}"/>'.format(W - 1, CARD_H - 1))

    # kicker row
    kw = c.text("sans", "AI CODING USAGE", PAD, 48, 11, "ink", tracking=1.8)
    c.text("sans", "LAST {} DAYS".format(n), PAD + kw + 14, 48, 11, "mut", tracking=1.8)
    if BRAND_TAG:
        c.text("sans", BRAND_TAG, right, 48, 10, "mut", "end", 1.6)

    # hero number, then what it is worth
    hero = render.fmt_hero(st["total"])
    hw = c.text("serif", hero, PAD - 3, 148, 92, "ink", tracking=-1.5)
    c.text("serif_i", "tokens", PAD - 3 + hw + 12, 148, 26, "body")
    c.text("serif_i", "{} at API list prices, not billed spend.".format(
        render.compact_cost(st["cost"])), PAD, 182, 19, "body")

    # source split: one thin bar per source, on a hairline track
    col_x, col_w = 520, right - 520
    for i, (cls, name, tok) in enumerate((("claude", "CLAUDE CODE", st["ct"]),
                                          ("codex", "CODEX", st["xt"]))):
        y = 92 + i * 52
        c.text("sans", name, col_x, y, 11, "mut", tracking=1.6)
        pct = "{}%".format(_pct(tok, st["total"]))
        pw = c.text("sans", pct, right, y, 11, "mut", "end", 1.0)
        c.text("serif", render.compact_tokens(tok), right - pw - 12, y + 1, 22, "ink", "end")
        c.rect(col_x, y + 12, col_w, 6, "brd", ' shape-rendering="crispEdges"')
        share = (float(tok) / st["total"]) if st["total"] else 0
        if tok:
            c.rect(col_x, y + 12, max(2, round(col_w * share)), 6, cls, ' shape-rendering="crispEdges"')

    # stat band
    top = 214
    c.line(PAD, top, right, top)
    peak_d = _day_label(st["peak_day"]) if st["peak_day"] else "-"
    cells = (
        ("BEST DAY", render.compact_tokens(st["peak"]), peak_d),
        ("AVG / ACTIVE DAY", render.compact_tokens(st["avg"]), ""),
        ("ACTIVE DAYS", "{}/{}".format(st["active"], n), ""),
        ("STREAK", str(st["streak"]), "DAY" if st["streak"] == 1 else "DAYS"),
    )
    cw = (right - PAD) / 4.0
    for i, (lab, val, unit) in enumerate(cells):
        x = PAD + i * cw + (0 if i == 0 else 20)
        if i:
            c.line(PAD + i * cw, top + 10, PAD + i * cw, top + 62)
        c.text("sans", lab, x, top + 28, 10, "mut", tracking=1.6)
        vw = c.text("serif", val, x, top + 58, 30, "ink")
        if unit:
            c.text("sans", unit, x + vw + 8, top + 58, 10, "mut", tracking=1.4)

    c.text("sans", "GENERATED {}".format(generated.upper()), PAD, CARD_H - 14, 9.5, "mut", tracking=1.2)
    return c.finish()


# ------------------------------------------------------------------ daily bars

PAD_L, PAD_R = 64, 40
PLOT_TOP, PLOT_H = 124, 200
BASE = PLOT_TOP + PLOT_H
DAILY_H = BASE + 74


def build_daily(st, generated):
    rows = st["rows"]
    n = len(rows)
    first, last = rows[0]["start"], rows[-1]["start"]
    # no %-d: it is a glibc extension and raises ValueError on Windows
    span = "{} {} to {} {}, {}".format(first.strftime("%b"), first.day,
                                       last.strftime("%b"), last.day, last.year)
    label = "Daily tokens by source, {}, {} total. Claude Code {}, Codex {}.".format(
        span, render.fmt_hero(st["total"]), render.compact_tokens(st["ct"]),
        render.compact_tokens(st["xt"]))
    c = Canvas(W, DAILY_H, label)
    right = W - PAD_R

    c.rect(0, 0, W, 4, "amb")
    c.add('<rect class="frame" x=".5" y=".5" width="{}" height="{}"/>'.format(W - 1, DAILY_H - 1))

    c.text("sans", "AI CODING USAGE", 40, 40, 11, "ink", tracking=1.8)
    if BRAND_TAG:
        c.text("sans", BRAND_TAG, W - 40, 40, 10, "mut", "end", 1.6)
    c.text("serif", "Daily tokens", 40, 78, 30, "ink", tracking=-0.3)
    c.text("serif_i", "{}. {} tokens.".format(span, render.fmt_hero(st["total"])), 40, 102, 17, "body")

    # legend, right-aligned on the title row
    lx = right
    for cls, name in (("codex", "CODEX"), ("claude", "CLAUDE CODE")):
        w = bf.measure("sans", name, 10.5, 1.4)
        c.text("sans", name, lx, 78, 10.5, "mut", "end", 1.4)
        c.rect(lx - w - 16, 69, 9, 9, cls)
        lx -= w + 16 + 22

    peak_top = max(render.nice_ticks(max(st["tokens"] + [1]))[-1], 1)
    ticks = render.nice_ticks(max(st["tokens"] + [1]))
    for t in ticks:
        y = BASE - PLOT_H * t / float(peak_top)
        if t:
            c.line(PAD_L, y, right, y)
        c.text("sans", render.compact_tokens(t) if t else "0", PAD_L - 12, y + 3.5, 10, "mut", "end", 0.4)
    c.add('<line class="hl" x1="{}" y1="{}" x2="{}" y2="{}" style="stroke:var(--muted)"/>'.format(
        PAD_L, BASE + .5, right, BASE + .5))

    slot = (right - PAD_L) / float(n)
    bw = min(22, int(slot * 0.64))
    totals = st["tokens"]
    peak_idx = totals.index(max(totals)) if any(totals) else -1
    stride = max(1, -(-n // 8))
    tops = []
    for i, row in enumerate(rows):
        cx = PAD_L + slot * (i + 0.5)
        x0 = round(cx - bw / 2.0)
        wip = row["partial"]
        y = BASE
        ytop = BASE
        for cls, src in (("claude", "claude"), ("codex", "codex")):
            v = row[src]["total"]
            if v <= 0:
                continue
            h = max(2.0, round(PLOT_H * v / float(peak_top)))
            gap = 1 if y != BASE else 0
            c.rect(x0, y - h, bw, h - gap, cls + " bar" + (" wip" if wip else ""))
            y -= h
            ytop = y
        tops.append(ytop)
        if (n - 1 - i) % stride == 0:
            c.text("sans", _day_label(row["start"]), cx, BASE + 22, 9.5, "mut", "middle", 0.8)

    marks = set()
    if peak_idx >= 0:
        marks.add(peak_idx)
    if n and totals[n - 1] > 0 and (n - 1 - peak_idx) > 1:
        marks.add(n - 1)
    for idx in sorted(marks):
        cx = PAD_L + slot * (idx + 0.5)
        near = min(tops[max(0, idx - 1): idx + 2] or [BASE])
        c.text("serif", render.compact_tokens(totals[idx]), cx, min(tops[idx], near) - 8, 16, "ink", "middle")

    c.text("sans", "GENERATED {}".format(generated.upper()), 40, DAILY_H - 16, 9.5, "mut", tracking=1.2)
    if rows[-1]["partial"]:
        c.text("sans", "FADED BAR = DAY IN PROGRESS", right, DAILY_H - 16, 9.5, "mut", "end", 1.2)
    return c.finish()


# ---------------------------------------------------------------------- badges

BADGE_H = 30


def _badge(label, value, aria, generated):
    lw = bf.measure("sans", label, 10, 1.5)
    vw = bf.measure("serif", value, 17)
    total = int(round(3 + 12 + lw + 12 + 1 + 12 + vw + 12))
    c = Canvas(total, BADGE_H, aria)
    c.add('<rect class="plate" x=".5" y=".5" width="{}" height="{}"/>'.format(total - 1, BADGE_H - 1))
    c.add('<rect class="frame" x=".5" y=".5" width="{}" height="{}"/>'.format(total - 1, BADGE_H - 1))
    c.rect(0, 0, 3, BADGE_H, "amb")
    x = 3 + 12
    c.text("sans", label, x, 19, 10, "mut", tracking=1.5)
    x += lw + 12
    c.line(x + .5, 7, x + .5, BADGE_H - 7)
    c.text("serif", value, x + 13, 21.5, 17, "ink")
    return c.finish()


def build_badges(st, generated):
    tok = render.fmt_hero(st["total"])
    cost = render.compact_cost(st["cost"])
    streak = "{} day{}".format(st["streak"], "" if st["streak"] == 1 else "s")
    return [
        ("badge/brand-tokens-30d.svg", _badge("TOKENS 30D", tok, "Tokens, last 30 days: " + tok, generated)),
        ("badge/brand-api-30d.svg", _badge("API-EQUIVALENT 30D", cost, "API-equivalent value, last 30 days: " + cost, generated)),
        ("badge/brand-streak.svg", _badge("STREAK", streak, "Active-day streak: " + streak, generated)),
    ]


def build_all(days, generated):
    st = _stats(days)
    if not st["rows"]:
        return []
    return ([("brand/card.svg", build_card(st, generated)),
             ("brand/daily.svg", build_daily(st, generated))]
            + build_badges(st, generated))
