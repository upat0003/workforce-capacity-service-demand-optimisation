"""Render reproducible portfolio screenshots and annotated wireframes for the
Workforce Capacity and Service-Demand Optimisation Power BI report, from the
page metadata in pages.json. Pure Python + Pillow, no external design tool
dependency - re-run any time the metrics in pages.json change.

    python -m powerbi.Templates.render_mockups
    # or
    python powerbi/Templates/render_mockups.py
"""
from __future__ import annotations
import json
import math
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SPEC = json.loads((Path(__file__).with_name("pages.json")).read_text())
W, H = 1600, 900

# Unique project palette: warm teal-green primary with a coral/salmon accent -
# distinct from every sibling portfolio project's palette (see docs/architecture.md).
COL = {
    "nav": "#0E3B36", "bg": "#F5F8F7", "card": "#FFFFFF", "ink": "#1C2E2B", "muted": "#5C726D",
    "grid": "#DCE6E3",
    "teal": "#1F8A72", "coral": "#E8785F", "amber": "#E3A73E", "blue": "#4F7B94", "plum": "#8F5C7C",
    "tooltip": "#0E2B27", "tooltip_text": "#F5F8F7", "chip": "#E7F1EE", "chip_border": "#B9CFC8",
}


def font(size: int, bold: bool = False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def txt(d, xy, s, size=18, fill=None, bold=False, anchor=None):
    d.text(xy, str(s), font=font(size, bold), fill=fill or COL["ink"], anchor=anchor)


def text_w(d, s, size=13, bold=False):
    return d.textlength(str(s), font=font(size, bold))


def card(d, box, title=None):
    d.rounded_rectangle(box, 14, fill=COL["card"], outline=COL["grid"], width=2)
    if title:
        txt(d, (box[0] + 22, box[1] + 18), title, 17, COL["ink"], True)


def legend(d, xy, entries):
    """Colour-swatch + label legend row, drawn directly beneath its chart."""
    x, y = xy
    for label, colour in entries:
        c = COL.get(colour, colour)
        d.ellipse((x, y + 3, x + 12, y + 15), fill=c)
        txt(d, (x + 18, y), label, 12, COL["muted"])
        x += 18 + text_w(d, label, 12) + 22


def axis_labels(d, box, labels, ylabel=None):
    x1, y1, x2, y2 = box
    if labels:
        n = len(labels)
        for i, lab in enumerate(labels):
            cx = x1 + (i + 0.5) * (x2 - x1) / n
            txt(d, (cx, y2 + 8), lab, 11, COL["muted"], anchor="ma")
    if ylabel:
        txt(d, (x1 - 4, y1 - 18), ylabel, 11, COL["muted"])


def tooltip_bubble(d, anchor_xy, label, value, bound_left=14, bound_right=W - 14, min_y=110):
    """Dark hover-tooltip bubble with a pointer/leader line anchored to a data point.

    Fix for a known pitfall: a tooltip anchored near the top of a chart used to flip
    upward into the page title/subtitle/KPI row. Here the tooltip's minimum y is
    clamped to `min_y` (the caller passes the chart card's own top edge), and if the
    anchor is close enough to the card top that the bubble would still collide, the
    bubble is centred vertically on the anchor and nudged to whichever side has room,
    instead of only ever being placed above the point.
    """
    ax, ay = anchor_xy
    w = max(130, int(text_w(d, value, 13, True)) + 30)
    bh = 46
    by = ay - bh - 10
    if by < min_y:
        by = max(min_y, ay - bh // 2)  # centre on the anchor rather than flipping above it
    bx = ax + 18
    if bx + w > bound_right:
        bx = ax - w - 18
    if bx < bound_left:
        bx = bound_left
    d.rounded_rectangle((bx, by, bx + w, by + bh), 9, fill=COL["tooltip"])
    txt(d, (bx + 13, by + 7), label, 11, "#9FC3B8", True)
    txt(d, (bx + 13, by + 24), value, 13, COL["tooltip_text"], True)
    lx = bx + 12 if bx > ax else bx + w - 12
    ly = by + bh if by > ay else by
    d.line((ax, ay, lx, ly), fill=COL["tooltip"], width=2)
    d.ellipse((ax - 5, ay - 5, ax + 5, ay + 5), outline=COL["tooltip"], width=2, fill="white")


def filter_chips(d, right_x, y, chips):
    widths = [int(text_w(d, label, 13)) + 46 for label in chips]
    x = right_x - sum(widths) - 10 * (len(chips) - 1)
    for label, w in zip(chips, widths):
        d.rounded_rectangle((x, y, x + w, y + 30), 15, fill=COL["chip"], outline=COL["chip_border"], width=1)
        txt(d, (x + 14, y + 7), label, 13, COL["nav"])
        txt(d, (x + w - 20, y + 7), "x", 13, COL["muted"], True)
        x += w + 10


def line_chart(d, box, accent, points, highlight_idx=None):
    x1, y1, x2, y2 = box
    d.line((x1, y2, x2, y2), fill=COL["grid"], width=2)
    d.line((x1, y1, x1, y2), fill=COL["grid"], width=2)
    coords = [(x1 + i * (x2 - x1) / (len(points) - 1), y2 - p * (y2 - y1)) for i, p in enumerate(points)]
    d.line(coords, fill=accent, width=5, joint="curve")
    for i, (x, y) in enumerate(coords):
        r = 7 if i == highlight_idx else 4
        d.ellipse((x - r, y - r, x + r, y + r), fill=accent,
                   outline="white" if i == highlight_idx else None, width=3 if i == highlight_idx else 0)
    return coords[highlight_idx if highlight_idx is not None else -1]


def bars(d, box, values, colors=None, horizontal=False, highlight_idx=None, value_labels=None):
    """Bar chart with a cross-filter highlight outline. Value labels (if provided) are
    drawn centred inside a bar only when it is wide/tall enough (>=90px); narrower bars
    get a small colour swatch and label placed just outside the bar instead, so text
    never overflows a thin bar (a known layout pitfall in earlier report iterations)."""
    x1, y1, x2, y2 = box
    colors = colors or [COL["teal"]] * len(values)
    anchor = (x1, y1)
    if horizontal:
        gap = (y2 - y1) / len(values)
        for i, v in enumerate(values):
            b = (x1, y1 + i * gap + 5, x1 + v * (x2 - x1), y1 + (i + 1) * gap - 5)
            outline = COL["ink"] if i == highlight_idx else None
            d.rounded_rectangle(b, 5, fill=colors[i % len(colors)], outline=outline, width=3 if outline else 0)
            if i == highlight_idx:
                anchor = (b[2], (b[1] + b[3]) / 2)
            if value_labels:
                bar_w = b[2] - b[0]
                lab = str(value_labels[i])
                if bar_w >= 90:
                    txt(d, ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2), lab, 12, "white", True, anchor="mm")
                else:
                    d.ellipse((b[2] + 8, (b[1] + b[3]) / 2 - 4, b[2] + 16, (b[1] + b[3]) / 2 + 4), fill=colors[i % len(colors)])
                    txt(d, (b[2] + 22, (b[1] + b[3]) / 2), lab, 12, COL["ink"], False, anchor="lm")
    else:
        gap = (x2 - x1) / len(values)
        for i, v in enumerate(values):
            b = (x1 + i * gap + 8, y2 - v * (y2 - y1), x1 + (i + 1) * gap - 8, y2)
            outline = COL["ink"] if i == highlight_idx else None
            d.rounded_rectangle(b, 6, fill=colors[i % len(colors)], outline=outline, width=3 if outline else 0)
            if i == highlight_idx:
                anchor = ((b[0] + b[2]) / 2, b[1])
            if value_labels:
                bar_h = b[3] - b[1]
                lab = str(value_labels[i])
                if bar_h >= 90 and (b[2] - b[0]) >= 40:
                    txt(d, ((b[0] + b[2]) / 2, b[1] + 10), lab, 12, "white", True, anchor="ma")
                else:
                    txt(d, ((b[0] + b[2]) / 2, b[1] - 16), lab, 12, COL["ink"], True, anchor="ma")
    return anchor


def donut(d, box, parts, highlight_idx=None):
    total = sum(parts)
    start = -90
    colors = [COL["teal"], COL["coral"], COL["amber"], COL["plum"], COL["blue"]]
    anchor = None
    for i, v in enumerate(parts):
        end = start + 360 * v / total
        width = 34 if i == highlight_idx else 28
        d.arc(box, start, end, fill=colors[i % len(colors)], width=width)
        if i == highlight_idx:
            mid = math.radians((start + end) / 2)
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            r = (box[2] - box[0]) / 2
            anchor = (cx + (r + 24) * math.cos(mid), cy + (r + 24) * math.sin(mid))
        start = end
    return anchor or ((box[0] + box[2]) / 2, box[1])


def heatmap(d, box, rows=5, cols=7, highlight=(1, 2)):
    x1, y1, x2, y2 = box
    cw, ch = (x2 - x1) / cols, (y2 - y1) / rows
    palette = ["#EAF3F0", "#BFE3D8", "#8FD0BE", "#4CB59D", "#0E3B36"]
    anchor = (x1, y1)
    for r in range(rows):
        for c in range(cols):
            cell = (x1 + c * cw, y1 + r * ch, x1 + (c + 1) * cw - 3, y1 + (r + 1) * ch - 3)
            d.rectangle(cell, fill=palette[(r * 3 + c * 2) % 5])
            if (r, c) == highlight:
                d.rectangle(cell, outline=COL["ink"], width=3)
                anchor = (cell[2], cell[1])
    return anchor


def table(d, box, rows, columns=None, highlight_row=0):
    x1, y1, x2, y2 = box
    h = (y2 - y1) / (rows + 1)
    d.rectangle((x1, y1, x2, y1 + h), fill="#EAF1EE")
    columns = columns or ["Item", "Status", "Age", "Owner"]
    ncols = len(columns)
    colw = (x2 - x1 - 42) / max(ncols - 1, 1)
    txt(d, (x1 + 42, y1 + h / 2), columns[0], 12, COL["nav"], True, anchor="lm")
    for ci, cname in enumerate(columns[1:]):
        txt(d, (x1 + 42 + ci * colw + (x2 - x1 - 42) * 0.55, y1 + h / 2), cname, 12, COL["nav"], True, anchor="lm")
    anchor = (x1, y1 + h)
    for r in range(rows):
        y = y1 + (r + 1) * h
        d.line((x1, y, x2, y), fill=COL["grid"], width=1)
        row_box = (x1, y, x2, y + h)
        if r == highlight_row:
            d.rectangle(row_box, fill="#F1F8F5")
        d.ellipse((x1 + 14, y + 12, x1 + 26, y + 24), fill=[COL["coral"], COL["amber"], COL["teal"]][r % 3])
        d.rounded_rectangle((x1 + 42, y + 12, x1 + 230 + (r % 3) * 60, y + 21), 4, fill="#A9C0BA")
        d.rounded_rectangle((x2 - 180, y + 12, x2 - 35, y + 21), 4, fill="#CBDAD4")
        if r == highlight_row:
            d.rectangle(row_box, outline=COL["ink"], width=2)
            anchor = (x1 + 230 + (r % 3) * 60, y + 16)
    return anchor


def render(page, idx, annotated=False):
    im = Image.new("RGB", (W, H), COL["bg"])
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 238, H), fill=COL["nav"])
    txt(d, (30, 30), SPEC["short_title"], 23, "white", True)
    for i, p in enumerate(SPEC["pages"]):
        y = 104 + i * 58
        if i == idx:
            d.rounded_rectangle((18, y - 10, 220, y + 34), 10, fill="#164A42")
        txt(d, (34, y), f"{i+1:02d}  {p['nav']}", 14, "white" if i == idx else "#A9CAC1", i == idx)
    txt(d, (278, 30), page["title"], 30, COL["ink"], True)
    txt(d, (278, 72), page["question"], 16, COL["muted"])
    filter_chips(d, 1565, 26, ["Period: Latest 12mo", "Region: All", "Model: v1.0.0"])
    for i, k in enumerate(page["kpis"]):
        x = 278 + i * 310
        card(d, (x, 112, x + 285, 220))
        txt(d, (x + 20, 132), k[0], 14, COL["muted"], True)
        txt(d, (x + 20, 164), k[1], 27, k[3], True)
        txt(d, (x + 20, 198), k[2], 13, COL["muted"])

    layout = page["layout"]
    tips = []  # (anchor, tooltip_meta, bound_left, bound_right, min_y)
    chart_top = 246

    if layout == "trend":
        card(d, (278, chart_top, 1010, 565), page["visuals"][0])
        a1 = line_chart(d, (322, 320, 966, 495), COL["teal"], [.30, .36, .33, .45, .52, .48, .60, .64, .70, .66, .77, .82], highlight_idx=11)
        axis_labels(d, (322, 320, 966, 495), page.get("chart1_xlabels"), page.get("chart1_ylabel"))
        legend(d, (322, 529), page.get("chart1_legend", []))
        tips.append((a1, page.get("tooltip1"), 300, 1000, chart_top + 8))
        card(d, (1034, chart_top, 1565, 565), page["visuals"][1])
        a2 = bars(d, (1080, 320, 1518, 495), [.45, .70, .58, .84, .62], [COL["blue"], COL["coral"], COL["amber"], COL["teal"], COL["plum"]], True, highlight_idx=3)
        axis_labels(d, (1080, 320, 1518, 495), None, page.get("chart2_ylabel"))
        legend(d, (1080, 529), page.get("chart2_legend", []))
        tips.append((a2, page.get("tooltip2"), 1056, 1555, chart_top + 8))
    elif layout == "matrix":
        card(d, (278, chart_top, 1030, 565), page["visuals"][0])
        a1 = heatmap(d, (322, 320, 986, 495))
        axis_labels(d, (322, 320, 986, 495), page.get("chart1_xlabels"), page.get("chart1_ylabel"))
        legend(d, (322, 529), page.get("chart1_legend", []))
        tips.append((a1, page.get("tooltip1"), 300, 1020, chart_top + 8))
        card(d, (1054, chart_top, 1565, 565), page["visuals"][1])
        a2 = donut(d, (1168, 318, 1428, 510), [42, 26, 20, 12], highlight_idx=0)
        legend(d, (1168, 522), page.get("chart2_legend", []))
        tips.append((a2, page.get("tooltip2"), 1076, 1555, chart_top + 8))
    elif layout == "distribution":
        card(d, (278, chart_top, 930, 565), page["visuals"][0])
        a1 = bars(d, (320, 325, 888, 495), [.26, .50, .74, .40], [COL["teal"], COL["coral"], COL["amber"], COL["plum"]], highlight_idx=1)
        axis_labels(d, (320, 325, 888, 495), page.get("chart1_xlabels"), page.get("chart1_ylabel"))
        legend(d, (320, 529), page.get("chart1_legend", []))
        tips.append((a1, page.get("tooltip1"), 298, 920, chart_top + 8))
        card(d, (954, chart_top, 1565, 565), page["visuals"][1])
        a2 = line_chart(d, (1002, 325, 1518, 495), COL["blue"], [.20, .28, .41, .37, .54, .66, .73, .78], highlight_idx=7)
        axis_labels(d, (1002, 325, 1518, 495), page.get("chart2_xlabels"), page.get("chart2_ylabel"))
        legend(d, (1002, 529), page.get("chart2_legend", []))
        tips.append((a2, page.get("tooltip2"), 976, 1555, chart_top + 8))
    else:  # table
        card(d, (278, chart_top, 1565, 565), page["visuals"][0])
        a1 = table(d, (310, 310, 1533, 535), 5, page.get("table_xlabels"), highlight_row=0)
        legend(d, (310, 548), page.get("table_legend", []))
        tips.append((a1, page.get("tooltip1"), 298, 1555, chart_top + 8))

    card(d, (278, 590, 905, 850), page["visuals"][2])
    bars(d, (320, 660, 860, 812), [.78, .60, .46, .68, .35], [COL["teal"], COL["coral"], COL["amber"], COL["blue"], COL["plum"]], True, highlight_idx=0)
    card(d, (929, 590, 1565, 850), "What this means")
    for i, line in enumerate(textwrap.wrap(page["story"], 54)):
        txt(d, (963, 654 + i * 30), line, 18, COL["ink"])

    for anchor, tip, bl, br, min_y in tips:
        if anchor and tip:
            tooltip_bubble(d, anchor, tip.get("label", ""), tip.get("value", ""), bl, br, min_y)

    if annotated:
        overlay = Image.new("RGBA", (W, H), (255, 255, 255, 80))
        im = Image.alpha_composite(im.convert("RGBA"), overlay)
        d = ImageDraw.Draw(im)
        notes = [
            ((250, 102), "1", "Headline KPIs"), ((250, chart_top - 4), "2", "Primary decision view"),
            ((905, 585), "3", "Narrative and action"), ((850, 6), "4", "Filter chips"),
            ((1290, 300), "5", "Hover tooltip"),
            ((1010, 285) if layout in ("trend", "distribution") else (1034, 285), "6", "Cross-filter highlight"),
        ]
        for (x, y), n, label in notes:
            d.ellipse((x, y, x + 34, y + 34), fill="#C9573F")
            txt(d, (x + 17, y + 17), n, 16, "white", True, "mm")
            txt(d, (x + 43, y + 7), label, 15, "#7A2E1F", True)
    return im.convert("RGB")


def main():
    shots = ROOT / "powerbi/Screenshots"
    mocks = ROOT / "powerbi/Mockups"
    shots.mkdir(parents=True, exist_ok=True)
    mocks.mkdir(parents=True, exist_ok=True)
    for i, page in enumerate(SPEC["pages"]):
        slug = f"{i+1:02d}_{page['slug']}"
        render(page, i).save(shots / f"{slug}.png", optimize=True)
        render(page, i, True).save(mocks / f"{slug}_annotated.png", optimize=True)
    print(f"Rendered {len(SPEC['pages'])} screenshots and {len(SPEC['pages'])} annotated mockups")


if __name__ == "__main__":
    main()
