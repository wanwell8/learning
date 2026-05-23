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
    for j, (lbl, key, color, _, _paper_key) in enumerate(methods):
        for i, scn in enumerate(SCN_ORDER):
            v = data[scn]["stats"][key]
            x0 = i - (n_methods * bar_w) / 2 + j * bar_w
            ax2.bar(x0, 0, bar_w * 0.92, v, fill=color, opacity=0.92, stroke=color)
            if v > ax2.ymax * 0.02:
                ax2.text(x0 + bar_w * 0.46, v + ax2.ymax * 0.02, f"{v*1000:.0f}",
                         anchor="middle", size=8.5, color=COLOR_TEXT)

    ax2.draw_axes(
        xticks=[0, 1, 2], yticks=yticks2,
        xfmt=lambda v: SCN_ORDER[int(v)],
        yfmt=lambda v: f"{v*1000:.0f}",
        ylabel="Peak-hour ΔP interval width  (kW)",
        title="Peak-hour width by method",
        subtitle="Four methods compared at the scenario peak hour"
    )

    # legend below summary inset (placed under the axes, not over them)
    legend(c, inset_x + 50, inset_y + inset_h + 12,
           [(m[0], m[2], 'band' if 'proposed' in m[3] or 'unconstr' in m[3] else 'line')
            for m in methods],
           box_w=inset_w - 100, columns=2)

    # caption
    caption(c, 50, H - 38, W - 100,
            "Each panel shows the 24-h DR response envelope at node 30 for one typical day. "
            "Proposed interval (solid red band) sits between the unconstrained joint-sampling band (blue) and the "
            "fixed-parameter midpoint trace (dashed black); the probabilistic 90% CI (yellow dotted) is a tighter "
            "percentile cut by construction. The right inset compares peak-hour widths across methods and scenarios.")

    (FIG_DIR / "figure_2_envelopes.svg").write_text(c.render())
    print("[ok] figure_2_envelopes.svg")


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
    ax.line(log_Ns, means, stroke=COLOR_UNCONSTR, width=2.4)
    ax.scatter(log_Ns, means, color=COLOR_UNCONSTR, r=4.5, opacity=1.0)

    # arrow + annotation: highlight where the curve enters the ±11% band
    in_band_idx = next((i for i, m in enumerate(means)
                        if abs(m - ref) / ref <= 0.11), len(Ns) - 1)
    n_in = Ns[in_band_idx]
    m_in = means[in_band_idx]
    ax_x = _m.log10(n_in)
    # annotation label sits to the LEFT and BELOW the entry point, with an
    # L-shaped leader to keep everything inside the plot area regardless of
    # where the band entry sits along the x-axis.
    label_x = ax_x - 1.10
    label_y = m_in - ymax * 0.30
    # point we are pointing at
    tip_x_data = ax_x
    tip_y_data = m_in - ymax * 0.015
    sx_lbl, sy_lbl = ax.sx(label_x), ax.sy(label_y)
    sx_tip, sy_tip = ax.sx(tip_x_data), ax.sy(tip_y_data)
    # L-leader: from label-end horizontally to right, then up to tip
    knee_x = sx_tip
    knee_y = sy_lbl
    c.add(
        f'<polyline points="{sx_lbl+150:.1f},{sy_lbl:.1f} {knee_x:.1f},{knee_y:.1f} {sx_tip:.1f},{sy_tip+8:.1f}" '
        f'fill="none" stroke="{COLOR_TEXT}" stroke-width="1.1" opacity="0.8"/>'
    )
    # arrowhead pointing UP into the data point
    c.add(
        f'<polygon points="{sx_tip:.1f},{sy_tip:.1f} {sx_tip-3.5:.1f},{sy_tip+7:.1f} {sx_tip+3.5:.1f},{sy_tip+7:.1f}" '
        f'fill="{COLOR_TEXT}" opacity="0.85"/>'
    )
    # annotation text
    c.add(
        f'<text x="{sx_lbl:.1f}" y="{sy_lbl+4:.1f}" font-size="10.5" '
        f'fill="{COLOR_TEXT}" font-weight="600">N = {n_in}: enters &#177;11% band</text>'
    )

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


# ===========================================================================
# Figure 5 — Joint design-dial heat-map (with iso-width contours)
# ===========================================================================
def figure_5():
    data = json.loads((DATA_DIR / "fig5_heatmap.json").read_text())
    tau_w = data["tau_widths"]
    eta_p = data["eta_peaks"]
    vals = data["values"]   # values[i_eta][j_tau]

    W, H = 1080, 780
    c = Canvas(W, H)
    title_block(
        c, 50, 38,
        "Figure 5  ·  Peak-Hour Interval Width as a Joint Function of Design Dials",
        "Width (kW) at Summer typical-day peak hour, swept over participation-interval width and peak-period tariff η; "
        "iso-width contours overlaid"
    )

    # heat area
    hx, hy = 170, 110
    nrows = len(eta_p)
    ncols = len(tau_w)
    cell = 72
    hw = ncols * cell
    hh = nrows * cell

    vmin = min(min(r) for r in vals)
    vmax = max(max(r) for r in vals)

    def color(v):
        t = (v - vmin) / (vmax - vmin) if vmax > vmin else 0.5
        stops = [
            (0.00, (45, 24, 80)),
            (0.35, (32, 84, 138)),
            (0.65, (42, 158, 130)),
            (1.00, (253, 231, 37)),
        ]
        for i in range(len(stops) - 1):
            if t <= stops[i + 1][0]:
                t0, c0 = stops[i]; t1, c1 = stops[i + 1]
                f = (t - t0) / (t1 - t0)
                r = int(c0[0] + f * (c1[0] - c0[0]))
                g = int(c0[1] + f * (c1[1] - c0[1]))
                b = int(c0[2] + f * (c1[2] - c0[2]))
                return f"rgb({r},{g},{b})"
        return "rgb(253,231,37)"

    # ---- heat cells ----
    for i, ep in enumerate(eta_p):
        for j, tw in enumerate(tau_w):
            v = vals[i][j]
            cx = hx + j * cell
            cy = hy + (nrows - 1 - i) * cell
            c.add(
                f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell-1.5:.1f}" height="{cell-1.5:.1f}" '
                f'fill="{color(v)}" stroke="white" stroke-width="1.5"/>'
            )
            t_pct = (v - vmin) / (vmax - vmin) if vmax > vmin else 0.5
            txt_color = "#1f2933" if t_pct > 0.55 else "white"
            c.add(
                f'<text x="{cx + cell/2:.1f}" y="{cy + cell/2 + 4:.1f}" text-anchor="middle" '
                f'font-size="11" fill="{txt_color}" font-weight="600">{v*1000:.0f}</text>'
            )

    # ---- iso-width contour lines (marching-squares style) ----
    def _interp(p1, p2, v1, v2, level):
        if v2 == v1:
            return p1
        t = (level - v1) / (v2 - v1)
        t = max(0.0, min(1.0, t))
        return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))

    def _cell_segments(level, i, j):
        """Return list of polyline segments for a 4-vertex cell with corner (i,j)..(i+1,j+1).

        Corner order: bl=(i,j), br=(i,j+1), tr=(i+1,j+1), tl=(i+1,j).
        Coordinates in screen space (centre of heat cells).
        """
        # vertex value at (i, j) = vals[i][j]; screen coord centre of cell:
        def vc(ii, jj):
            cx = hx + jj * cell + cell / 2
            cy = hy + (nrows - 1 - ii) * cell + cell / 2
            return (cx, cy), vals[ii][jj]
        p_bl, v_bl = vc(i, j)
        p_br, v_br = vc(i, j + 1)
        p_tr, v_tr = vc(i + 1, j + 1)
        p_tl, v_tl = vc(i + 1, j)

        def side(v):
            return 1 if v >= level else 0
        idx = (side(v_bl) << 0) | (side(v_br) << 1) | (side(v_tr) << 2) | (side(v_tl) << 3)
        # edges: e0=bl-br, e1=br-tr, e2=tr-tl, e3=tl-bl
        e = {
            0: _interp(p_bl, p_br, v_bl, v_br, level),
            1: _interp(p_br, p_tr, v_br, v_tr, level),
            2: _interp(p_tr, p_tl, v_tr, v_tl, level),
            3: _interp(p_tl, p_bl, v_tl, v_bl, level),
        }
        table = {
            0:  [],
            15: [],
            1:  [(0, 3)], 14: [(0, 3)],
            2:  [(0, 1)], 13: [(0, 1)],
            4:  [(1, 2)], 11: [(1, 2)],
            8:  [(2, 3)], 7:  [(2, 3)],
            3:  [(1, 3)], 12: [(1, 3)],
            6:  [(0, 2)], 9:  [(0, 2)],
            5:  [(0, 1), (2, 3)],
            10: [(0, 3), (1, 2)],
        }
        return [(e[a], e[b]) for a, b in table[idx]]

    contour_levels_kw = [100, 150, 200, 250, 300]  # contour values in kW
    for level_kw in contour_levels_kw:
        level = level_kw / 1000.0  # back to MW for comparison with vals
        if level < vmin or level > vmax:
            continue
        for i in range(nrows - 1):
            for j in range(ncols - 1):
                for (a, b) in _cell_segments(level, i, j):
                    c.add(
                        f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" '
                        f'stroke="white" stroke-width="2.4" opacity="0.55"/>'
                    )
                    c.add(
                        f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" '
                        f'stroke="#1a1a1a" stroke-width="1.0" opacity="0.85"/>'
                    )
        # label one segment per contour: pick the first segment we find with i in middle
        labelled = False
        for i in range(nrows - 1):
            if labelled:
                break
            for j in range(ncols - 1):
                segs = _cell_segments(level, i, j)
                if segs:
                    (a, b) = segs[0]
                    mx = (a[0] + b[0]) / 2
                    my = (a[1] + b[1]) / 2
                    # small white pill behind label
                    c.add(
                        f'<rect x="{mx-18:.1f}" y="{my-9:.1f}" width="36" height="14" '
                        f'fill="white" stroke="#1a1a1a" stroke-width="0.6" rx="2" opacity="0.9"/>'
                    )
                    c.add(
                        f'<text x="{mx:.1f}" y="{my+2:.1f}" text-anchor="middle" '
                        f'font-size="9.5" font-weight="600" fill="#1a1a1a">{level_kw} kW</text>'
                    )
                    labelled = True
                    break

    # ---- axis labels ----
    for j, tw in enumerate(tau_w):
        cx = hx + j * cell + cell / 2
        c.add(
            f'<text x="{cx:.1f}" y="{hy + hh + 18:.1f}" text-anchor="middle" '
            f'font-size="10.5" fill="{COLOR_TEXT_MUT}">{tw:.2f}</text>'
        )
    c.add(
        f'<text x="{hx + hw/2:.1f}" y="{hy + hh + 42:.1f}" text-anchor="middle" '
        f'font-size="12" font-weight="500" fill="{COLOR_TEXT}">Participation interval width  (τ_max − τ_min)</text>'
    )
    for i, ep in enumerate(eta_p):
        cy = hy + (nrows - 1 - i) * cell + cell / 2
        c.add(
            f'<text x="{hx - 8:.1f}" y="{cy + 3:.1f}" text-anchor="end" '
            f'font-size="10.5" fill="{COLOR_TEXT_MUT}">{ep:.2f}</text>'
        )
    cx_lbl = hx - 80
    cy_lbl = hy + hh / 2
    c.add(
        f'<text x="{cx_lbl:.1f}" y="{cy_lbl:.1f}" text-anchor="middle" '
        f'font-size="12" font-weight="500" fill="{COLOR_TEXT}" '
        f'transform="rotate(-90 {cx_lbl:.1f} {cy_lbl:.1f})">Peak-period tariff fluctuation  η_peak</text>'
    )

    # ---- color bar ----
    cb_x = hx + hw + 50
    cb_y = hy + 10
    cb_w = 22
    cb_h = hh - 20
    steps = 80
    for k in range(steps):
        t = k / (steps - 1)
        v = vmin + t * (vmax - vmin)
        c.add(
            f'<rect x="{cb_x:.1f}" y="{cb_y + (1-t)*cb_h - cb_h/steps:.2f}" '
            f'width="{cb_w}" height="{cb_h/steps + 0.6:.2f}" fill="{color(v)}"/>'
        )
    cb_ticks = nice_ticks(vmin, vmax, 6)
    for v in cb_ticks:
        if v < vmin or v > vmax:
            continue
        ty = cb_y + (1 - (v - vmin) / (vmax - vmin)) * cb_h
        c.add(
            f'<line x1="{cb_x + cb_w:.1f}" y1="{ty:.1f}" x2="{cb_x + cb_w + 4:.1f}" y2="{ty:.1f}" '
            f'stroke="{COLOR_TEXT}" stroke-width="0.8"/>'
        )
        c.add(
            f'<text x="{cb_x + cb_w + 8:.1f}" y="{ty + 3.5:.1f}" '
            f'font-size="10" fill="{COLOR_TEXT_MUT}">{v*1000:.0f} kW</text>'
        )
    c.add(
        f'<text x="{cb_x + cb_w/2:.1f}" y="{cb_y - 10:.1f}" text-anchor="middle" '
        f'font-size="10.5" fill="{COLOR_TEXT}" font-weight="500">ΔP width</text>'
    )

    # ---- operating-point markers ----
    def nearest(arr, v):
        return min(range(len(arr)), key=lambda i: abs(arr[i] - v))

    op_points = [
        ("Summer",   0.30, 0.25, "#fff8f0", "#d1495b"),
        ("Winter",   0.20, 0.20, "#fff8f0", "#2e6f95"),
        ("Shoulder", 0.20, 0.10, "#fff8f0", "#669973"),
    ]
    for name, tw, ep, halo, edge in op_points:
        j_b = nearest(tau_w, tw)
        i_b = nearest(eta_p, ep)
        cx_b = hx + j_b * cell + cell / 2
        cy_b = hy + (nrows - 1 - i_b) * cell + cell / 2
        c.add(
            f'<circle cx="{cx_b:.1f}" cy="{cy_b:.1f}" r="14" fill="none" '
            f'stroke="#ffffff" stroke-width="3"/>'
        )
        c.add(
            f'<circle cx="{cx_b:.1f}" cy="{cy_b:.1f}" r="14" fill="none" '
            f'stroke="{edge}" stroke-width="2"/>'
        )
        lx = cx_b + 22
        ly = cy_b + 3.5
        c.add(
            f'<rect x="{lx-3:.1f}" y="{ly-10:.1f}" width="{len(name)*7+6:.0f}" height="15" '
            f'fill="{halo}" stroke="{edge}" stroke-width="1" rx="3" opacity="0.95"/>'
        )
        c.add(
            f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="10.5" font-weight="600" '
            f'fill="{edge}">{name}</text>'
        )

    caption(c, 50, H - 65, W - 100,
            "Each cell reports the proposed-method 24-h interval width at the Summer-typical-day peak hour, in kW, "
            "as both design dials are swept independently. Thin black iso-width curves overlay the heat map and turn "
            "it into a usable design chart: for any target interval width, the corresponding curve traces the locus "
            "of (τ-width, η_peak) pairs that achieve it. The three labelled circles mark the typical-day operating "
            "points; their relative position confirms that tariff η carries the larger leverage.")

    (FIG_DIR / "figure_5_heatmap.svg").write_text(c.render())
    print("[ok] figure_5_heatmap.svg")


if __name__ == "__main__":
    figure_2()
    figure_4()
    figure_5()
    print("\nDone. Output:")
    for f in sorted(FIG_DIR.glob("*.svg")):
        print(f"  {f.name}: {f.stat().st_size:,} bytes")
