# token-history, Capital Suite edition

A daily record of Claude Code and Codex token usage, rendered as static SVG for a
GitHub profile. This is a fork of [keli-wen/token-history](https://github.com/keli-wen/token-history)
(MIT). The collector, the data model and the upstream chart styles are his. The
Capital Suite style in `scripts/styles/capitalsuite.py` is the addition.

| File | What it is |
|---|---|
| `charts/brand/card.svg` | 30-day hero number, source split, stat band |
| `charts/brand/daily.svg` | Daily tokens, stacked by source |
| `charts/badge/brand-tokens-30d.svg` | Badge: tokens, last 30 days |
| `charts/badge/brand-api-30d.svg` | Badge: API-equivalent value, last 30 days |
| `charts/badge/brand-streak.svg` | Badge: active-day streak |

Cost figures are API-equivalent value at list prices, not billed spend.

## Embed in a profile README

The profile uses the upstream pixel look:

```markdown
<div align="center">

### AI coding usage

<img src="https://raw.githubusercontent.com/killerwaz/token-history/master/charts/badge/pixel-tokens-30d.svg" alt="Tokens, last 30 days">
<img src="https://raw.githubusercontent.com/killerwaz/token-history/master/charts/badge/pixel-api-30d.svg" alt="API-equivalent value, last 30 days">
<img src="https://raw.githubusercontent.com/killerwaz/token-history/master/charts/badge/pixel-streak.svg" alt="Active-day streak">

<img src="https://raw.githubusercontent.com/killerwaz/token-history/master/charts/day/pixel-card.svg" alt="AI coding usage, last 30 days" width="100%">
<img src="https://raw.githubusercontent.com/killerwaz/token-history/master/charts/day/pixel-tokens.svg" alt="Daily tokens, last 30 days" width="100%">

</div>
```

To switch to the Capital Suite style, replace the five URLs:

| Pixel | Capital Suite |
|---|---|
| `badge/pixel-tokens-30d.svg` | `badge/brand-tokens-30d.svg` |
| `badge/pixel-api-30d.svg` | `badge/brand-api-30d.svg` |
| `badge/pixel-streak.svg` | `badge/brand-streak.svg` |
| `day/pixel-card.svg` | `brand/card.svg` |
| `day/pixel-tokens.svg` | `brand/daily.svg` |

The fork has to stay public for these URLs to load for visitors.

## Windows setup

Needs Git, Node.js (for `npx ccusage`) and [uv](https://docs.astral.sh/uv/) (`winget install astral-sh.uv`).

```powershell
git clone https://github.com/killerwaz/token-history; cd token-history
copy config.example.json config.json     # then set "host" to a neutral alias; check "timezone" and "branch"

# Before trusting anything, confirm ccusage sees your logs on THIS machine:
npx ccusage@latest daily
npx ccusage@latest codex daily

uv run scripts\collect.py --all --no-git  # backfill everything ccusage still has, no commit yet
uv run scripts\render.py
```

Open `charts\brand\card.svg` in a browser. When it looks right, commit and push, then
install the schedule:

```powershell
git add -A; git commit -m "first snapshot"; git push
powershell -ExecutionPolicy Bypass -File scripts\install-task-windows.ps1
Get-ScheduledTaskInfo -TaskName token-history-collect     # LastTaskResult 0 means success
```

Claude Code deletes transcripts older than 30 days by default, so run the backfill
once now. History that ccusage can no longer read cannot be recovered.

Do not sync `~/.claude` or `~/.codex` between machines. Every machine needs its own
`host` alias and its own logs, or totals double-count.

## Style knobs

At the top of `scripts/styles/capitalsuite.py`:

- `BRAND_TAG`: the small tag on the right of each chart. `""` removes it.
- `MARK`: `"amber"` (the brand fill) or `"amberdeep"`. Plain amber is 2.51:1 against
  Paper, under the 3:1 bar for chart marks. `"amberdeep"` is 3.67:1.

The dark palette is the reserved dark-editorial alternate. Its body, muted, border
and Codex values are derived, so review them before treating them as final.

## Typefaces

Newsreader and Inter are outlined into `scripts/brandfont.py`, because an SVG shown
through `<img>` on GitHub cannot load webfonts. To regenerate after changing a face
or the character set:

```
pip install fonttools
python assets/gen_brand_glyphs.py
```

Both typefaces are SIL Open Font License 1.1. The notices are in `assets/fonts/`.
