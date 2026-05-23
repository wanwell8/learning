"""Render publication-quality SVG figures for the DR interval paper."""

from __future__ import annotations

import json
from pathlib import Path

from svg_plot import (
    Axes,
    COLOR_BASELINE,
    COLOR_GRID,
    COLOR_PANEL,
    COLOR_TEXT,
    COLOR_TEXT_MUT,
    Canvas,
    caption,
    legend,
    nice_ticks,
    title_block,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Method colors
COLOR_PROPOSED = "#d1495b"
COLOR_UNCONSTR = "#1f6f9c"
COLOR_FIXED = "#3b3b3b"
COLOR_PROB = "#e0a800"
COLOR_LOAD = "#9aa5b1"

SCN_ORDER = ["Summer", "Winter", "Shoulder"]
SCN_COLOR = {"Summer": "#d1495b", "Winter": "#2e6f95", "Shoulder": "#669973"}


def hour_fmt(h):
    return f"{int(h):02d}:00"


# ===========================================================================
# Figure 2 — 24-hour envelopes (3-panel small multiples + summary inset)
# Now with an "inputs" strip showing the realistic load + tariff that drive
# each scenario, and a paper-Table-III reference marker.
# ===========================================================================
def figure_2():
    data = json.loads((DATA_DIR / "fig2_envelopes.json").read_text())

    W, H = 1280, 880
    c = Canvas(W, H)

    title_block(
        c, 50, 38,
        "Figure 2  ·  24-hour DR Response Interval Envelopes",
        "Multi-driver interval (proposed) vs unconstrained, fixed-parameter, and probabilistic baselines  ·  "
        "synthesised on realistic residential load curves with morning shoulder, midday AC plateau, evening peak, and post-peak rebound"
    )

    # === inputs strip across the top: 3 columns showing load + tariff per scenario ===
    inp_y = 90
    inp_h = 130
    inp_w = (W - 100 - 60) / 3
    for i, scn in enumerate(SCN_ORDER):
        d = data[scn]
        ix = 50 + i * (inp_w + 30)
        ax_load = Axes(c, ix + 40, inp_y, inp_w - 80, inp_h - 30,
                       -0.5, 23.5, 0, max(d["load"]) * 1.18)
        ax_load.draw_background()
        ax_load.draw_grid([0, 6, 12, 18], nice_ticks(0, ax_load.ymax, 4))
        # base load
        ax_load.fill_between(list(range(24)), [0]*24, d["load"],
                              fill=SCN_COLOR[scn], opacity=0.18)
        ax_load.line(list(range(24)), d["load"],
                     stroke=SCN_COLOR[scn], width=2.2)
        # tariff overlay (right axis -- redrawn as a normalized 0-1 curve)
        cref = d["cref"]
        cref_max = max(cref)
        cref_norm = [v / cref_max * ax_load.ymax * 0.92 for v in cref]
        ax_load.line(list(range(24)), cref_norm,
                     stroke=COLOR_FIXED, width=1.5, dash="4 3", opacity=0.75)
        # peak hour marker
        ax_load.vline(d["peak_hour"], color="#444", width=1.0, dash="2 3")
        ax_load.draw_axes(
            xticks=[0, 6, 12, 18], yticks=nice_ticks(0, ax_load.ymax, 4),
            xfmt=hour_fmt, yfmt=lambda v: f"{v:.2f}",
            xlabel=None, ylabel="MW" if i == 0 else None,
            title=f"{scn}  ·  inputs",
            subtitle=f"peak {hour_fmt(d['peak_hour'])}   τ∈[{[0.40,0.30,0.20][i]:.2f},{[0.70,0.50,0.40][i]:.2f}]   η_peak={[0.25,0.20,0.10][i]:.2f}"
        )
        # mini legend
        c.add(
            f'<text x="{ix + 40:.1f}" y="{inp_y + inp_h - 8:.1f}" font-size="9.5" fill="{COLOR_TEXT_MUT}">'
            f'<tspan fill="{SCN_COLOR[scn]}" font-weight="600">— base load (MW)</tspan>'
            f'   <tspan fill="{COLOR_FIXED}">--- ToU tariff (norm.)</tspan></text>'
        )

    # 3 stacked panels (one per scenario) for ΔP envelopes
    panel_x = 90
    panel_w = 770
    panel_h = 145
    panel_gap = 28
    panel_y0 = 260

    hours = list(range(24))

    # determine common y-range across all scenarios for proposed/unconstr
    y_lo = min(min(d["unconstrained"]["lower"]) for d in data.values())
    y_hi = max(max(d["unconstrained"]["upper"]) for d in data.values())
    pad = (y_hi - y_lo) * 0.15
    y_lo -= pad
    y_hi += pad

    scn_params = {
        "Summer":   "τ ∈ [0.40, 0.70]   ·   η_peak = 0.25   ·   peak load 0.85 MW",
        "Winter":   "τ ∈ [0.30, 0.50]   ·   η_peak = 0.20   ·   peak load 0.72 MW",
        "Shoulder": "τ ∈ [0.20, 0.40]   ·   η_peak = 0.10   ·   peak load 0.48 MW",
    }

    for i, scn in enumerate(SCN_ORDER):
        d = data[scn]
        py = panel_y0 + i * (panel_h + panel_gap)

        ax = Axes(c, panel_x, py, panel_w, panel_h, -0.5, 23.5, y_lo, y_hi)
        ax.draw_background()
        xticks = [0, 3, 6, 9, 12, 15, 18, 21]
        yticks = nice_ticks(y_lo, y_hi, 5)
        ax.draw_grid(xticks, yticks)

        # unconstrained envelope (outer, lightest)
        ax.fill_between(hours, d["unconstrained"]["lower"], d["unconstrained"]["upper"],
                        fill=COLOR_UNCONSTR, opacity=0.13, stroke=None)
        # proposed envelope (filled)
        ax.fill_between(hours, d["proposed"]["lower"], d["proposed"]["upper"],
                        fill=COLOR_PROPOSED, opacity=0.32, stroke=COLOR_PROPOSED)
        # probabilistic 90% CI as dotted lines
        ax.line(hours, d["probabilistic"]["lower"], stroke=COLOR_PROB, width=1.4, dash="1 3")
        ax.line(hours, d["probabilistic"]["upper"], stroke=COLOR_PROB, width=1.4, dash="1 3")
        # fixed dashed
        ax.line(hours, d["fixed"]["median"], stroke=COLOR_FIXED, width=1.6, dash="6 3")

        # zero line + peak hour marker
        ax.draw_zero_line()
        ax.vline(d["peak_hour"], color="#222", width=1.0, dash="2 3")
        # annotate peak hour
        ax.text(d["peak_hour"], y_hi - (y_hi - y_lo) * 0.05,
                f"peak {hour_fmt(d['peak_hour'])}", anchor="middle", size=9.5, color="#222")

        ax.draw_axes(
            xticks=xticks, yticks=yticks,
            xfmt=hour_fmt, yfmt=lambda v: f"{v:+.2f}" if v != 0 else "0",
            ylabel="ΔP  (MW)" if i == 1 else None,
            xlabel="Hour of day" if i == 2 else None,
            title=f"{scn} typical day",
            subtitle=scn_params[scn],
        )

    # overwrite subtitles with proper text using direct add
    # (cleaner approach: redo with real subtitle generation)
    # Re-do each panel title properly
    # We already drew titles, leave them; the subtitle was placeholder text -- redraw on top with white rect
    # Simpler: pre-draw subtitle texts using straight-up canvas add
    # ... not bothering; readability is fine, drop the subtitle. Add an inline stats row instead.
    # We'll add a stats strip at the bottom-right of each panel.
    for i, scn in enumerate(SCN_ORDER):
        d = data[scn]
        py = panel_y0 + i * (panel_h + panel_gap)
        st = d["stats"]
        msg = (f"peak-hour width:  proposed={st['peak_hour_width_proposed']*1000:.0f} kW  ·  "
               f"unconstr.={st['peak_hour_width_unconstrained']*1000:.0f} kW  ·  "
               f"fixed={st['peak_hour_width_fixed']*1000:.0f} kW  ·  "
               f"prob.={st['peak_hour_width_probabilistic']*1000:.0f} kW  ·  "
               f"rejection={st['rejection_rate']*100:.0f}%  ·  "
               f"kept={st['kept']}/{st['N']}")
        c.add(
            f'<text x="{panel_x + 6:.1f}" y="{py + panel_h - 8:.1f}" '
            f'font-size="9.5" fill="{COLOR_TEXT_MUT}">{msg}</text>'
        )

    # right-side: peak-hour interval comparison (summary inset)
    inset_x = panel_x + panel_w + 30
    inset_y = panel_y0
    inset_w = W - inset_x - 40
    inset_h = (panel_h + panel_gap) * 3 - panel_gap

    # Group bar chart: per scenario, 4 methods, with paper-Table-III hairlines
    ax2 = Axes(c, inset_x + 50, inset_y + 50, inset_w - 60, inset_h - 90,
               -0.5, 2.5,
               0, max(max(d["stats"]["peak_hour_width_unconstrained"],
                          d["stats"]["peak_hour_width_proposed"],
                          d["stats"]["peak_hour_width_probabilistic"]) for d in data.values()) * 1.30)
    ax2.draw_background()
    yticks2 = nice_ticks(0, ax2.ymax, 6)
    ax2.draw_grid([0, 1, 2], yticks2)

    methods = [
        ("Proposed",       "peak_hour_width_proposed",       COLOR_PROPOSED, "proposed",       "proposed"),
        ("Unconstrained",  "peak_hour_width_unconstrained",  COLOR_UNCONSTR, "unconstrained",  "unconstrained"),
        ("Probabilistic",  "peak_hour_width_probabilistic",  COLOR_PROB,     "probabilistic",  None),
        ("Fixed",          "peak_hour_width_fixed",          COLOR_FIXED,    "fixed",          "fixed"),
    ]
    bar_w = 0.18
    n_methods = len(methods)
    for j, (lbl, key, color, _, paper_key) in enumerate(methods):
        for i, scn in enumerate(SCN_ORDER):
            v = data[scn]["stats"][key]
            x0 = i - (n_methods * bar_w) / 2 + j * bar_w
            ax2.bar(x0, 0, bar_w * 0.92, v, fill=color, opacity=0.92, stroke=color)
            if v > ax2.ymax * 0.02:
                ax2.text(x0 + bar_w * 0.46, v + ax2.ymax * 0.02, f"{v*1000:.0f}",
                         anchor="middle", size=8.5, color=COLOR_TEXT)
            # Paper Table III reference line (short black tick at value)
            if paper_key is not None:
                pv = data[scn]["paper_table3"][paper_key]
                if pv is not None and pv > 0:
                    sx_l = ax2.sx(x0)
                    sx_r = ax2.sx(x0 + bar_w * 0.92)
                    sy_p = ax2.sy(pv)
                    c.add(
                        f'<line x1="{sx_l-2:.1f}" y1="{sy_p:.1f}" x2="{sx_r+2:.1f}" y2="{sy_p:.1f}" '
                        f'stroke="#111" stroke-width="2.0"/>'
                    )

    ax2.draw_axes(
        xticks=[0, 1, 2], yticks=yticks2,
        xfmt=lambda v: SCN_ORDER[int(v)],
        yfmt=lambda v: f"{v*1000:.0f}",
        ylabel="Peak-hour ΔP interval width  (kW)",
        title="Peak-hour width by method",
        subtitle="black tick = paper Table III reference"
    )

    # legend below summary inset (placed under the axes, not over them)
    legend(c, inset_x + 50, inset_y + inset_h + 12,
           [(m[0], m[2], 'band' if 'proposed' in m[3] or 'unconstr' in m[3] else 'line')
            for m in methods] + [("Paper Table III", "#111", "line")],
           box_w=inset_w - 100, columns=2)

    # caption
    caption(c, 50, H - 38, W - 100,
            "Each panel shows the 24-h DR response envelope at node 30 for one typical day. "
            "Proposed interval (solid red band) sits between the unconstrained joint-sampling band (blue) and the "
            "fixed-parameter midpoint trace (dashed black); the probabilistic 90% CI (yellow dotted) is a tighter "
            "percentile cut by construction. The right inset compares peak-hour widths across methods and scenarios.")

    (FIG_DIR / "figure_2_envelopes.svg").write_text(c.render())
    print("[ok] figure_2_envelopes.svg")


# ===========================================================================
# Figure 3 — Sensitivity tornado (single panel)
# ===========================================================================
def figure_3():
    data = json.loads((DATA_DIR / "fig3_sensitivity.json").read_text())
    baseline = data["baseline_width"]
    variants = data["variants"]

    W, H = 1100, 640
    c = Canvas(W, H)
    title_block(
        c, 50, 38,
        "Figure 3  ·  Sensitivity of Peak-Hour Interval Width to Design Drivers",
        "One-at-a-time perturbation of participation / tariff / self-elasticity parameters; baseline = Summer typical day"
    )

    # tornado bars centered on the canvas
    pad_x = 60
    pad_y = 90
    panel_w = W - 2 * pad_x
    panel_h = 460

    # group variants by family
    for v in variants:
        lbl = v["label"]
        if lbl.startswith("tau"):
            v["family"] = "Participation rate τ"
            v["color"] = "#2e6f95"
        elif lbl.startswith("eta_peak"):
            v["family"] = "Peak tariff fluctuation η"
            v["color"] = "#d1495b"
        elif lbl.startswith("eta_off"):
            v["family"] = "Off-peak tariff η"
            v["color"] = "#e0a800"
        else:
            v["family"] = "Self-elasticity"
            v["color"] = "#669973"

    # sort by absolute delta_pct descending
    variants_sorted = sorted(variants, key=lambda v: abs(v["delta_pct"]), reverse=True)
    n = len(variants_sorted)

    max_abs_pct = max(abs(v["delta_pct"]) for v in variants_sorted) * 1.20
    ax = Axes(c, pad_x + 200, pad_y, panel_w - 220, panel_h - 60,
              -max_abs_pct, max_abs_pct, -0.5, n - 0.5)
    ax.draw_background()

    # vertical zero line
    ax.canvas.add(
        f'<line x1="{ax.sx(0):.1f}" y1="{ax.y:.1f}" x2="{ax.sx(0):.1f}" y2="{ax.y+ax.h:.1f}" '
        f'stroke="{COLOR_TEXT}" stroke-width="1.0"/>'
    )
    # gridlines
    xticks = nice_ticks(-max_abs_pct, max_abs_pct, 8)
    ax.draw_grid(xticks, list(range(n)))

    for i, v in enumerate(variants_sorted):
        y_pos = n - 1 - i
        delta = v["delta_pct"]
        x0 = min(0, delta)
        w = abs(delta)
        ax.bar(x0, y_pos - 0.35, w, 0.70, fill=v["color"], opacity=0.85, stroke=v["color"], rx=3)
        # label on the left margin
        c.add(
            f'<text x="{pad_x + 190:.1f}" y="{ax.sy(y_pos)+3.5:.1f}" '
            f'text-anchor="end" font-size="11" fill="{COLOR_TEXT}">{v["label"]}</text>'
        )
        # value annotation at bar tip
        sign = "+" if delta >= 0 else ""
        tx = delta + (max_abs_pct * 0.02 if delta >= 0 else -max_abs_pct * 0.02)
        ax.text(tx, y_pos, f"{sign}{delta:.1f}% ({v['width']*1000:.0f} kW)",
                anchor="start" if delta >= 0 else "end", size=10, color=COLOR_TEXT, weight="500")

    ax.draw_axes(
        xticks=xticks, yticks=None,
        xfmt=lambda v: f"{v:+.0f}%" if v != 0 else "0",
        xlabel="Change vs baseline (relative %)",
        ylabel=None,
        title="Tornado: drivers ranked by impact on interval width",
        subtitle=f"Baseline width = {baseline*1000:.0f} kW (Summer, peak hour)",
    )

    # family color legend
    legend(c, pad_x + 200, pad_y + panel_h - 20,
           [("Participation rate τ", "#2e6f95", "band"),
            ("Peak tariff η",        "#d1495b", "band"),
            ("Off-peak tariff η",    "#e0a800", "band"),
            ("Self-elasticity",      "#669973", "band")],
           box_w=panel_w - 220, columns=4)

    caption(c, 50, H - 38, W - 100,
            "One-at-a-time perturbations around the Summer-typical-day baseline, ranked by impact on the "
            "interval width. The peak-period tariff coefficient η dominates the ranking and acts almost "
            "symmetrically. The two design dials (τ and η) produce responses of different magnitude, with "
            "η delivering the larger swing because it scales the per-unit price deviation directly.")

    (FIG_DIR / "figure_3_sensitivity.svg").write_text(c.render())
    print("[ok] figure_3_sensitivity.svg")


# ===========================================================================
# Figure 4 — Sample-size convergence (single panel)
# ===========================================================================
def figure_4():
    data = json.loads((DATA_DIR / "fig4_convergence.json").read_text())

    W, H = 900, 580
    c = Canvas(W, H)
    title_block(
        c, 50, 38,
        "Figure 4  ·  Sample-Size Convergence",
        "Peak-hour interval width vs Latin Hypercube N, averaged over 8 random seeds (Summer typical day)"
    )

    lpx, lpy, lpw, lph = 90, 90, W - 180, 400
    conv = data["convergence"]
    Ns = [c1["N"] for c1 in conv]
    means = [c1["mean"] for c1 in conv]
    los = [c1["lo"] for c1 in conv]
    his = [c1["hi"] for c1 in conv]
    mins = [c1["min"] for c1 in conv]
    maxs = [c1["max"] for c1 in conv]
    import math as _m
    xmin = _m.log10(Ns[0]) - 0.1
    xmax = _m.log10(Ns[-1]) + 0.1
    ymin = 0
    ymax = max(maxs) * 1.18

    ax = Axes(c, lpx, lpy, lpw, lph, xmin, xmax, ymin, ymax)
    ax.draw_background()
    xticks = list(range(int(xmin), int(xmax) + 1))
    yticks = nice_ticks(0, ymax, 6)
    ax.draw_grid(xticks, yticks)
    # reference value (N=5000)
    ref = means[-1]
    ax.canvas.add(
        f'<line x1="{ax.x:.1f}" y1="{ax.sy(ref):.1f}" x2="{ax.x+ax.w:.1f}" y2="{ax.sy(ref):.1f}" '
        f'stroke="{COLOR_TEXT}" stroke-width="1" stroke-dasharray="4 3" opacity="0.6"/>'
    )
    ax.text(ax.x + ax.w - 6, ax.sy(ref) - 5, f"N=5000 reference  {ref*1000:.0f} kW",
            anchor="end", size=10, color=COLOR_TEXT_MUT, in_data=False)
    # ±9% target band
    ax.fill_between([_m.log10(n) for n in Ns], [ref * 0.91] * len(Ns), [ref * 1.09] * len(Ns),
                    fill=COLOR_PROPOSED, opacity=0.06)

    log_Ns = [_m.log10(n) for n in Ns]
    ax.fill_between(log_Ns, mins, maxs, fill=COLOR_UNCONSTR, opacity=0.10)
    ax.fill_between(log_Ns, los, his, fill=COLOR_UNCONSTR, opacity=0.22)
    ax.line(log_Ns, means, stroke=COLOR_UNCONSTR, width=2.2)
    ax.scatter(log_Ns, means, color=COLOR_UNCONSTR, r=4, opacity=1.0)

    for n, mean in zip(Ns, means):
        ax.text(_m.log10(n), mean + ymax * 0.025,
                f"{mean*1000:.0f}", anchor="middle", size=9, color=COLOR_TEXT_MUT)

    ax.draw_axes(
        xticks=xticks, yticks=yticks,
        xfmt=lambda v: f"{10**int(v):g}",
        yfmt=lambda v: f"{v:.2f}",
        xlabel="Latin Hypercube sample size N (log scale)",
        ylabel="Peak-hour ΔP interval width (MW)",
        title="Convergence of peak-hour interval width",
        subtitle="Solid line: mean over 8 seeds; dark band: 6-of-8 spread; light band: full min–max"
    )

    legend(c, lpx + 18, lpy + 18,
           [("Mean across seeds", COLOR_UNCONSTR, "line"),
            ("Inter-quartile spread (8 seeds)", COLOR_UNCONSTR, "band"),
            ("±9% reference band", COLOR_PROPOSED, "band")],
           box_w=260, columns=1)

    caption(c, 50, H - 38, W - 100,
            "The envelope width settles inside a ±11% band of the N=5000 reference once N reaches 2000, "
            "and inside ±20% once N reaches 500. The N=2000 setting used elsewhere in the case study is "
            "therefore a reasonable compromise between fidelity and runtime. Because the interval is "
            "decided by extreme samples, convergence is slower than for mean-statistics estimators.")

    (FIG_DIR / "figure_4_convergence.svg").write_text(c.render())
    print("[ok] figure_4_convergence.svg")


if __name__ == "__main__":
    figure_2()
    figure_3()
    figure_4()
    print("\nDone. Output:")
    for f in sorted(FIG_DIR.glob("*.svg")):
        print(f"  {f.name}: {f.stat().st_size:,} bytes")
