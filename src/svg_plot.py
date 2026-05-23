"""Minimal pure-Python SVG plotting toolkit for publication-quality figures.
No external deps. Designed for the DR interval paper's result figures.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from html import escape


# ---------------------------------------------------------------------------
# Style tokens
# ---------------------------------------------------------------------------
COLOR_BG       = "#ffffff"
COLOR_PANEL    = "#fbfbfd"
COLOR_GRID     = "#e6e8eb"
COLOR_AXIS     = "#3b4252"
COLOR_TEXT     = "#1f2933"
COLOR_TEXT_MUT = "#5b6770"
COLOR_BASELINE = "#9aa5b1"

FONT = "Arial,Helvetica,'Helvetica Neue','Liberation Sans',sans-serif"


# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
@dataclass
class Canvas:
    width: float
    height: float
    elements: list[str] = field(default_factory=list)

    def add(self, s: str):
        self.elements.append(s)

    def render(self) -> str:
        body = "\n".join(self.elements)
        return (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width:.0f} {self.height:.0f}" '
            f'width="{self.width:.0f}" height="{self.height:.0f}" '
            f'font-family="{FONT}" font-size="12" color="{COLOR_TEXT}">\n'
            f'  <defs>\n'
            f'    <style>text{{fill:{COLOR_TEXT};}}</style>\n'
            f'  </defs>\n'
            f'  <rect x="0" y="0" width="{self.width:.0f}" height="{self.height:.0f}" fill="{COLOR_BG}"/>\n'
            f'{body}\n'
            f'</svg>\n'
        )


# ---------------------------------------------------------------------------
# Axes / panel
# ---------------------------------------------------------------------------
@dataclass
class Axes:
    canvas: Canvas
    x: float        # left of plot area
    y: float        # top of plot area
    w: float        # plot area width
    h: float        # plot area height
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    def sx(self, v: float) -> float:
        return self.x + (v - self.xmin) / (self.xmax - self.xmin) * self.w

    def sy(self, v: float) -> float:
        return self.y + self.h - (v - self.ymin) / (self.ymax - self.ymin) * self.h

    # ---- decorations ----
    def draw_background(self, fill: str = COLOR_PANEL):
        self.canvas.add(
            f'<rect x="{self.x:.1f}" y="{self.y:.1f}" width="{self.w:.1f}" height="{self.h:.1f}" '
            f'fill="{fill}" stroke="none"/>'
        )

    def draw_grid(self, xticks: list[float], yticks: list[float]):
        for x in xticks:
            sx = self.sx(x)
            self.canvas.add(
                f'<line x1="{sx:.1f}" y1="{self.y:.1f}" x2="{sx:.1f}" y2="{self.y+self.h:.1f}" '
                f'stroke="{COLOR_GRID}" stroke-width="1"/>'
            )
        for y in yticks:
            sy = self.sy(y)
            self.canvas.add(
                f'<line x1="{self.x:.1f}" y1="{sy:.1f}" x2="{self.x+self.w:.1f}" y2="{sy:.1f}" '
                f'stroke="{COLOR_GRID}" stroke-width="1"/>'
            )

    def draw_zero_line(self):
        if self.ymin < 0 < self.ymax:
            sy = self.sy(0)
            self.canvas.add(
                f'<line x1="{self.x:.1f}" y1="{sy:.1f}" x2="{self.x+self.w:.1f}" y2="{sy:.1f}" '
                f'stroke="{COLOR_AXIS}" stroke-width="0.8" stroke-dasharray="4 3" opacity="0.7"/>'
            )

    def draw_axes(self, xticks=None, yticks=None, xfmt=None, yfmt=None,
                  xlabel=None, ylabel=None, title=None, subtitle=None):
        # frame
        self.canvas.add(
            f'<rect x="{self.x:.1f}" y="{self.y:.1f}" width="{self.w:.1f}" height="{self.h:.1f}" '
            f'fill="none" stroke="{COLOR_AXIS}" stroke-width="0.8"/>'
        )
        # x ticks + labels
        if xticks is not None:
            for v in xticks:
                sx = self.sx(v)
                self.canvas.add(
                    f'<line x1="{sx:.1f}" y1="{self.y+self.h:.1f}" x2="{sx:.1f}" y2="{self.y+self.h+4:.1f}" '
                    f'stroke="{COLOR_AXIS}" stroke-width="0.8"/>'
                )
                label = xfmt(v) if xfmt else f'{v:g}'
                self.canvas.add(
                    f'<text x="{sx:.1f}" y="{self.y+self.h+16:.1f}" text-anchor="middle" '
                    f'fill="{COLOR_TEXT_MUT}" font-size="10.5">{escape(label)}</text>'
                )
        if yticks is not None:
            for v in yticks:
                sy = self.sy(v)
                self.canvas.add(
                    f'<line x1="{self.x-4:.1f}" y1="{sy:.1f}" x2="{self.x:.1f}" y2="{sy:.1f}" '
                    f'stroke="{COLOR_AXIS}" stroke-width="0.8"/>'
                )
                label = yfmt(v) if yfmt else f'{v:g}'
                self.canvas.add(
                    f'<text x="{self.x-7:.1f}" y="{sy+3.5:.1f}" text-anchor="end" '
                    f'fill="{COLOR_TEXT_MUT}" font-size="10.5">{escape(label)}</text>'
                )
        if xlabel:
            self.canvas.add(
                f'<text x="{self.x+self.w/2:.1f}" y="{self.y+self.h+35:.1f}" text-anchor="middle" '
                f'fill="{COLOR_TEXT}" font-size="11.5" font-weight="500">{escape(xlabel)}</text>'
            )
        if ylabel:
            cx = self.x - 38
            cy = self.y + self.h / 2
            self.canvas.add(
                f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" '
                f'fill="{COLOR_TEXT}" font-size="11.5" font-weight="500" '
                f'transform="rotate(-90 {cx:.1f} {cy:.1f})">{escape(ylabel)}</text>'
            )
        if title:
            self.canvas.add(
                f'<text x="{self.x:.1f}" y="{self.y-14:.1f}" text-anchor="start" '
                f'fill="{COLOR_TEXT}" font-size="13.5" font-weight="700">{escape(title)}</text>'
            )
        if subtitle:
            self.canvas.add(
                f'<text x="{self.x:.1f}" y="{self.y-2:.1f}" text-anchor="start" '
                f'fill="{COLOR_TEXT_MUT}" font-size="10.5" font-style="italic">{escape(subtitle)}</text>'
            )

    # ---- drawing primitives ----
    def line(self, xs: list[float], ys: list[float], stroke: str, width: float = 2.0,
             dash: str | None = None, opacity: float = 1.0):
        pts = " ".join(f"{self.sx(x):.2f},{self.sy(y):.2f}" for x, y in zip(xs, ys))
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
        self.canvas.add(
            f'<polyline points="{pts}" fill="none" stroke="{stroke}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}"{dash_attr}/>'
        )

    def fill_between(self, xs: list[float], lo: list[float], hi: list[float],
                     fill: str, opacity: float = 0.20, stroke: str | None = None):
        top = " ".join(f"{self.sx(x):.2f},{self.sy(y):.2f}" for x, y in zip(xs, hi))
        bot = " ".join(f"{self.sx(x):.2f},{self.sy(y):.2f}" for x, y in zip(reversed(xs), reversed(lo)))
        stroke_attr = f' stroke="{stroke}" stroke-width="1.0"' if stroke else ' stroke="none"'
        self.canvas.add(
            f'<polygon points="{top} {bot}" fill="{fill}" fill-opacity="{opacity}"{stroke_attr}/>'
        )

    def bar(self, x_left: float, y_bottom: float, width: float, height: float,
            fill: str, stroke: str | None = None, opacity: float = 1.0, rx: float = 2):
        sx = self.sx(x_left)
        sw = self.sx(x_left + width) - sx
        sy_b = self.sy(y_bottom)
        sy_t = self.sy(y_bottom + height)
        sh = sy_b - sy_t
        stroke_attr = f' stroke="{stroke}" stroke-width="0.6"' if stroke else ''
        self.canvas.add(
            f'<rect x="{sx:.2f}" y="{sy_t:.2f}" width="{sw:.2f}" height="{sh:.2f}" '
            f'fill="{fill}" fill-opacity="{opacity}" rx="{rx}"{stroke_attr}/>'
        )

    def vline(self, x: float, color: str = COLOR_AXIS, width: float = 1.0, dash: str = "3 3"):
        sx = self.sx(x)
        self.canvas.add(
            f'<line x1="{sx:.1f}" y1="{self.y:.1f}" x2="{sx:.1f}" y2="{self.y+self.h:.1f}" '
            f'stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}" opacity="0.85"/>'
        )

    def scatter(self, xs, ys, color, r: float = 3.0, opacity: float = 0.85):
        for x, y in zip(xs, ys):
            self.canvas.add(
                f'<circle cx="{self.sx(x):.2f}" cy="{self.sy(y):.2f}" r="{r}" '
                f'fill="{color}" opacity="{opacity}"/>'
            )

    def text(self, x: float, y: float, s: str, anchor: str = "start", color: str = COLOR_TEXT,
             size: float = 10.5, weight: str = "400", in_data: bool = True):
        if in_data:
            xx, yy = self.sx(x), self.sy(y)
        else:
            xx, yy = x, y
        self.canvas.add(
            f'<text x="{xx:.1f}" y="{yy:.1f}" text-anchor="{anchor}" fill="{color}" '
            f'font-size="{size}" font-weight="{weight}">{escape(s)}</text>'
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def nice_ticks(lo: float, hi: float, n: int = 6) -> list[float]:
    """Pretty axis ticks."""
    if hi == lo:
        return [lo]
    rng = hi - lo
    raw = rng / n
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if rng / step <= n + 1:
            break
    start = math.ceil(lo / step) * step
    out = []
    v = start
    while v <= hi + 1e-9:
        out.append(round(v, 10))
        v += step
    return out


def legend(canvas: Canvas, x: float, y: float, items: list[tuple[str, str, str]],
           box_w: float | None = None, columns: int = 1):
    """items: list of (label, color, kind) where kind in {'line','band','dash','dot'}"""
    line_h = 18
    pad = 10
    sw = 26
    if box_w is None:
        box_w = max(160, 30 + sw + max(len(t[0]) for t in items) * 7)
    rows = math.ceil(len(items) / columns)
    box_h = rows * line_h + 2 * pad
    canvas.add(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{box_w:.1f}" height="{box_h:.1f}" '
        f'fill="white" stroke="{COLOR_GRID}" stroke-width="1" rx="6"/>'
    )
    for idx, (label, color, kind) in enumerate(items):
        row = idx // columns
        col = idx % columns
        cx = x + pad + col * (box_w / columns)
        cy = y + pad + row * line_h + line_h / 2
        if kind == 'line':
            canvas.add(
                f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx+sw:.1f}" y2="{cy:.1f}" '
                f'stroke="{color}" stroke-width="2.4"/>'
            )
        elif kind == 'band':
            canvas.add(
                f'<rect x="{cx:.1f}" y="{cy-5:.1f}" width="{sw:.1f}" height="10" '
                f'fill="{color}" fill-opacity="0.30" stroke="{color}" stroke-width="0.8"/>'
            )
        elif kind == 'dash':
            canvas.add(
                f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx+sw:.1f}" y2="{cy:.1f}" '
                f'stroke="{color}" stroke-width="2.0" stroke-dasharray="5 3"/>'
            )
        elif kind == 'dot':
            canvas.add(
                f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx+sw:.1f}" y2="{cy:.1f}" '
                f'stroke="{color}" stroke-width="2.0" stroke-dasharray="1 3"/>'
            )
        canvas.add(
            f'<text x="{cx+sw+8:.1f}" y="{cy+3.5:.1f}" font-size="10.5" fill="{COLOR_TEXT}">{escape(label)}</text>'
        )


def title_block(canvas: Canvas, x: float, y: float, title: str, subtitle: str = ""):
    canvas.add(
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="17" font-weight="700" fill="{COLOR_TEXT}">{escape(title)}</text>'
    )
    if subtitle:
        canvas.add(
            f'<text x="{x:.1f}" y="{y+18:.1f}" font-size="11.5" font-style="italic" fill="{COLOR_TEXT_MUT}">{escape(subtitle)}</text>'
        )


def caption(canvas: Canvas, x: float, y: float, w: float, text: str):
    # naive wrap
    words = text.split()
    line = ""
    lines = []
    max_chars = int(w / 6.0)
    for word in words:
        if len(line) + len(word) + 1 > max_chars:
            lines.append(line.strip())
            line = ""
        line += word + " "
    if line.strip():
        lines.append(line.strip())
    for i, ln in enumerate(lines):
        canvas.add(
            f'<text x="{x:.1f}" y="{y+i*14:.1f}" font-size="10.5" fill="{COLOR_TEXT_MUT}">{escape(ln)}</text>'
        )
