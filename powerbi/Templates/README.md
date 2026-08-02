# Reproducible Power BI Mockup Build

`pages.json` holds the content for all 8 dashboard pages (title, question, KPIs, chart legends,
axis labels, tooltip content and narrative). `render_mockups.py` is pure Python + Pillow -- no
Power BI Desktop, browser, or external design tool is required to reproduce every image in
`powerbi/Screenshots/` and `powerbi/Mockups/`.

## Rebuild the images

```bash
pip install -r requirements.txt   # Pillow is the only dependency this script needs
python powerbi/Templates/render_mockups.py
```

This regenerates all 8 `powerbi/Screenshots/*.png` (clean) and all 8
`powerbi/Mockups/*_annotated.png` (numbered callouts explaining the layout) files in place.

## Design system

- **Palette**: `powerbi/theme.json` -- a warm teal-green primary (`#0E3B36` nav, `#1F8A72` chart
  teal) with a coral/salmon accent (`#E8785F`), distinct from every sibling portfolio project.
- **Interaction contract**, present on every page: a colour-coded legend under every chart,
  labelled axes, one hover-tooltip callout anchored to a data point, a cross-filter highlight
  (outlined bar/cell/row), and a persistent, removable filter-chip row top-right.
- **Layout templates**: `trend` (line + bar), `matrix` (heatmap + donut), `distribution` (bar +
  line), `table` (ranked/status table + bar) -- reused across the 8 pages so the report reads as
  one coherent product.

## Known layout pitfalls this build already accounts for

1. **Tooltip flipping into the title/KPI row.** `tooltip_bubble()` accepts a `min_y` (the chart
   card's own top edge) and clamps the bubble to it; if the anchor point is close enough to the
   card top that the bubble would still collide, it centres vertically on the anchor instead of
   only ever placing itself above the point.
2. **Centred labels overflowing a narrow bar.** `bars()` only centres a value label inside a bar
   when the bar is wide/tall enough (>=90px); narrower bars get the label placed just outside
   instead, so text never overflows a thin bar.
3. **Sidebar nav labels overflowing the rail.** Nav labels in `pages.json` are kept short enough
   to fit the 220px-wide sidebar at the rendered font size -- verified with
   `ImageFont.getlength()` against the fixed rail width during design, not just eyeballed.

## Editing content

Change a KPI value, chart legend, tooltip, or narrative by editing `pages.json` -- no code
changes needed for a content update. Only touch `render_mockups.py` if you're changing the visual
design itself (a new chart type, a new interaction element, a palette change).
