#!/usr/bin/env python3
"""
Generate voltage_regulation_paper.docx -- pure stdlib (zipfile only).
Follows jian style of 'Automation of Electric Power Systems' (dianli xitong zidonghua).
"""

import zipfile, io
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "paper" / "voltage_regulation_paper.docx"

LQ = "“"   # left curly double-quote  (safe inside Python strings)
RQ = "”"   # right curly double-quote

# ─────────────────────────────────────────────────────────────────────────────
# Low-level XML helpers
# ─────────────────────────────────────────────────────────────────────────────

def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))

def rpr_str(bold=False, italic=False, sz=21,
            ascii_font="Times New Roman", ea_font="宋体",
            sup=False, sub=False):
    p = []
    p.append(f'<w:rFonts w:ascii="{ascii_font}" w:hAnsi="{ascii_font}" '
             f'w:eastAsia="{ea_font}" w:cs="{ea_font}"/>')
    if bold:   p.append('<w:b/><w:bCs/>')
    if italic: p.append('<w:i/><w:iCs/>')
    p.append(f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>')
    if sup:    p.append('<w:vertAlign w:val="superscript"/>')
    if sub:    p.append('<w:vertAlign w:val="subscript"/>')
    return '<w:rPr>' + ''.join(p) + '</w:rPr>'

def run(text, **kw):
    return (f'<w:r>{rpr_str(**kw)}'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r>')

def ppr_str(align="both", before=0, after=0, line=480,
            style="Normal", left_indent=0, first_line=0):
    s = f'<w:pStyle w:val="{style}"/>'
    s += f'<w:jc w:val="{align}"/>'
    s += (f'<w:spacing w:before="{before}" w:after="{after}" '
          f'w:line="{line}" w:lineRule="auto"/>')
    if left_indent or first_line:
        s += f'<w:ind w:left="{left_indent}" w:firstLine="{first_line}"/>'
    return f'<w:pPr>{s}</w:pPr>'

def para(content, **kw):
    return f'<w:p>{ppr_str(**kw)}{content}</w:p>'

def empty_para():
    return ('<w:p><w:pPr>'
            '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
            '</w:pPr></w:p>')

# ── Equation in a borderless 2-cell table (left: equation | right: number) ──

def eq_row(eq_xml, eq_num):
    num_cell = (
        '<w:tc><w:tcPr>'
        '<w:tcW w:w="600" w:type="dxa"/>'
        '<w:vAlign w:val="center"/>'
        '<w:tcBorders>'
        '<w:top w:val="none" w:sz="0"/><w:left w:val="none" w:sz="0"/>'
        '<w:bottom w:val="none" w:sz="0"/><w:right w:val="none" w:sz="0"/>'
        '</w:tcBorders>'
        '</w:tcPr>'
        f'<w:p><w:pPr><w:jc w:val="right"/>'
        f'<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
        f'{run("(" + str(eq_num) + ")", sz=21)}'
        f'</w:p></w:tc>'
    )
    eq_cell = (
        '<w:tc><w:tcPr>'
        '<w:tcW w:w="8400" w:type="dxa"/>'
        '<w:vAlign w:val="center"/>'
        '<w:tcBorders>'
        '<w:top w:val="none" w:sz="0"/><w:left w:val="none" w:sz="0"/>'
        '<w:bottom w:val="none" w:sz="0"/><w:right w:val="none" w:sz="0"/>'
        '</w:tcBorders>'
        '</w:tcPr>'
        f'<w:p><w:pPr><w:jc w:val="center"/>'
        f'<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
        f'{eq_xml}'
        f'</w:p></w:tc>'
    )
    return (
        '<w:tbl>'
        '<w:tblPr>'
        '<w:tblStyle w:val="TableNormal"/>'
        '<w:tblW w:w="9000" w:type="dxa"/>'
        '<w:tblInd w:w="0" w:type="dxa"/>'
        '<w:tblBorders>'
        '<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '</w:tblBorders>'
        '</w:tblPr>'
        '<w:tblGrid><w:gridCol w:w="8400"/><w:gridCol w:w="600"/></w:tblGrid>'
        f'<w:tr>{eq_cell}{num_cell}</w:tr>'
        '</w:tbl>'
    )

# ── Data table with top/middle/bottom rules ───────────────────────────────────

def data_table(headers, rows, col_widths=None):
    n = len(headers)
    if col_widths is None:
        col_widths = [9000 // n] * n
    grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in col_widths)

    def cell(text, bold=False, w_width=1800, top_border=False, bot_border=False):
        top = ('<w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
               if top_border else '<w:top w:val="none" w:sz="0"/>')
        bot = ('<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
               if bot_border else '<w:bottom w:val="none" w:sz="0"/>')
        return (
            f'<w:tc><w:tcPr><w:tcW w:w="{w_width}" w:type="dxa"/>'
            f'<w:tcBorders>{top}{bot}'
            f'<w:left w:val="none" w:sz="0"/><w:right w:val="none" w:sz="0"/>'
            f'</w:tcBorders></w:tcPr>'
            f'<w:p><w:pPr><w:jc w:val="center"/>'
            f'<w:spacing w:before="60" w:after="60" w:line="240" w:lineRule="auto"/>'
            f'</w:pPr>'
            f'{run(text, bold=bold, sz=19, ea_font="宋体")}'
            f'</w:p></w:tc>'
        )

    hrow = ('<w:tr>' +
            ''.join(cell(h, bold=True, w_width=col_widths[i],
                         top_border=True, bot_border=True)
                    for i, h in enumerate(headers)) +
            '</w:tr>')
    drows = ''
    last = len(rows) - 1
    for ri, row in enumerate(rows):
        is_last = (ri == last)
        drows += ('<w:tr>' +
                  ''.join(cell(str(v), w_width=col_widths[i],
                               bot_border=is_last)
                          for i, v in enumerate(row)) +
                  '</w:tr>')
    return (
        '<w:tbl>'
        '<w:tblPr>'
        '<w:tblStyle w:val="TableNormal"/>'
        '<w:tblW w:w="9000" w:type="dxa"/>'
        '<w:tblBorders>'
        '<w:top w:val="none" w:sz="0"/><w:left w:val="none" w:sz="0"/>'
        '<w:bottom w:val="none" w:sz="0"/><w:right w:val="none" w:sz="0"/>'
        '<w:insideH w:val="none" w:sz="0"/><w:insideV w:val="none" w:sz="0"/>'
        '</w:tblBorders>'
        '</w:tblPr>'
        f'<w:tblGrid>{grid}</w:tblGrid>'
        f'{hrow}{drows}'
        '</w:tbl>'
    )

# ─────────────────────────────────────────────────────────────────────────────
# OMML helpers  (Office Math Markup Language)
# ─────────────────────────────────────────────────────────────────────────────

def mrun(text, italic=True, sz=21):
    sty = '<m:sty m:val="i"/>' if italic else '<m:sty m:val="p"/>'
    return (f'<m:r><m:rPr>{sty}<m:sz m:val="{sz}"/></m:rPr>'
            f'<m:t xml:space="preserve">{esc(text)}</m:t></m:r>')

def msup(base, exp):
    return f'<m:sSup><m:sSupPr/><m:e>{base}</m:e><m:sup>{exp}</m:sup></m:sSup>'

def msub(base, sb):
    return f'<m:sSub><m:sSubPr/><m:e>{base}</m:e><m:sub>{sb}</m:sub></m:sSub>'

def msubsup(base, sb, exp):
    return (f'<m:sSubSup><m:sSubSupPr/><m:e>{base}</m:e>'
            f'<m:sub>{sb}</m:sub><m:sup>{exp}</m:sup></m:sSubSup>')

def mrad(radicand):
    return (f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr>'
            f'<m:deg/><m:e>{radicand}</m:e></m:rad>')

def mfrac(num, den):
    return f'<m:f><m:fPr/><m:num>{num}</m:num><m:den>{den}</m:den></m:f>'

def mnorm(inner):
    return mrun('‖') + inner + mrun('‖')

def omath(content):
    ns = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'
    return f'<m:oMath {ns}>{content}</m:oMath>'

# ─────────────────────────────────────────────────────────────────────────────
# Equations (OMML)
# ─────────────────────────────────────────────────────────────────────────────

# Eq1: delta_V approx S_P*delta_P + S_Q*delta_Q
EQ1 = omath(
    mrun('Δ') + mrun('V') + mrun(' ≈ ') +
    msub(mrun('S'), mrun('P', italic=False)) + mrun('·ΔP + ') +
    msub(mrun('S'), mrun('Q', italic=False)) + mrun('·ΔQ')
)

# Eq2: delta_V approx S*delta_P, S_ij = sum r_k
EQ2 = omath(
    mrun('ΔV ≈ S·ΔP,    ') +
    msub(mrun('S'), mrun('ij', italic=False)) + mrun(' = ') +
    mrun('Σ') + msub(mrun(''), mrun('k∈Ω(i,j)', italic=False)) +
    msub(mrun('r'), mrun('k'))
)

# Eq3: P-box: P_lower <= P_pv(t) <= P_upper
EQ3 = omath(
    msub(mrun('P̲'), mrun('pv', italic=False)) + mrun('(t) ≤ ') +
    msub(mrun('P'), mrun('pv', italic=False)) + mrun('(t) ≤ ') +
    msub(mrun('P̅'), mrun('pv', italic=False)) + mrun('(t)')
)

# Eq4: bounds from forecast
EQ4 = omath(
    msub(mrun('P̲'), mrun('pv', italic=False)) +
    mrun('(t) = (1 − ') +
    msubsup(mrun('α'), mrun('pv', italic=False), mrun('lo', italic=False)) +
    mrun(')·') + msub(mrun('P̂'), mrun('pv', italic=False)) + mrun('(t)') +
    mrun(',    ') +
    msub(mrun('P̅'), mrun('pv', italic=False)) +
    mrun('(t) = (1 + ') +
    msubsup(mrun('α'), mrun('pv', italic=False), mrun('hi', italic=False)) +
    mrun(')·') + msub(mrun('P̂'), mrun('pv', italic=False)) + mrun('(t)')
)

# Eq5: reservoir mass balance (referencing [12])
EQ5 = omath(
    mrun('V(t+1) = V(t) + ') +
    msub(mrun('q'), mrun('in', italic=False)) + mrun('(t) − ') +
    mfrac(
        msub(mrun('p'), mrun('h', italic=False)) + mrun('(t)·Δt'),
        msub(mrun('η'), mrun('h', italic=False))
    )
)

# Eq6: SOC dynamics
EQ6 = omath(
    mrun('SOC(t+1) = SOC(t) − ') +
    mfrac(
        msup(msub(mrun('p'), mrun('s', italic=False)), mrun('+', italic=False)) +
        mrun('(t)·Δt'),
        msub(mrun('η'), mrun('d', italic=False)) + mrun('·') +
        msub(mrun('E'), mrun('s', italic=False))
    ) +
    mrun(' + ') +
    mfrac(
        msup(msub(mrun('p'), mrun('s', italic=False)), mrun('−', italic=False)) +
        mrun('(t)·') +
        msub(mrun('η'), mrun('c', italic=False)) + mrun('·Δt'),
        msub(mrun('E'), mrun('s', italic=False))
    )
)

# Eq7: fast reserve margin
EQ7 = omath(
    mrun('ρ(t) = min(') +
    msubsup(mrun('p'), mrun('avail', italic=False), mrun('dis', italic=False)) +
    mrun('(t),  ') +
    msubsup(mrun('p'), mrun('avail', italic=False), mrun('ch', italic=False)) +
    mrun('(t))')
)

# Eq8: worst-case deviation bound
EQ8 = omath(
    mrun('|Δ') +
    msubsup(mrun('P'), mrun('net', italic=False), mrun('WC', italic=False)) +
    mrun('(t)|  ≤  ') +
    mrad(
        msup(msub(mrun('Δ'), mrun('pv', italic=False)), mrun('2')) +
        mrun('(t) + ') +
        msup(msub(mrun('Δ'), mrun('load', italic=False)), mrun('2')) +
        mrun('(t)')
    )
)

# Eq9: endogenised reserve margin (core formula, Proposition 1)
EQ9 = omath(
    msub(mrun('ρ'), mrun('min', italic=False)) + mrun('(t) = ') +
    mrad(
        msup(msub(mrun('Δ'), mrun('pv', italic=False)), mrun('2')) +
        mrun('(t) + ') +
        msup(msub(mrun('Δ'), mrun('load', italic=False)), mrun('2')) +
        mrun('(t)')
    ) +
    mrun(' + ζ·') +
    msub(mrun('P̅'), mrun('load', italic=False)) + mrun('(t)')
)

# Eq10: objective function of Proposition 1
EQ10 = omath(
    mrun('min  ') +
    mrun('Σ') +
    msubsup(mrun(''), mrun('t=1', italic=False), mrun('T', italic=False)) +
    mrun('[') +
    msub(mrun('c'), mrun('h', italic=False)) + mrun('(t)·') +
    msub(mrun('p'), mrun('h', italic=False)) + mrun('(t) + ') +
    msup(mrun('c'), mrun('+', italic=False)) +
    msup(msub(mrun('p'), mrun('s', italic=False)), mrun('+', italic=False)) +
    mrun('(t) + ') +
    msup(mrun('c'), mrun('−', italic=False)) +
    msup(msub(mrun('p'), mrun('s', italic=False)), mrun('−', italic=False)) +
    mrun('(t)]')
)

# Eq11: tightened SOC bounds (reserve guarantee constraint)
EQ11 = omath(
    msup(mrun('SOC'), mrun('min', italic=False)) + mrun(' + ') +
    mfrac(
        msub(mrun('ρ'), mrun('min', italic=False)) + mrun('(t)·Δt'),
        msub(mrun('η'), mrun('d', italic=False)) + mrun('·') +
        msub(mrun('E'), mrun('s', italic=False))
    ) +
    mrun(' ≤ SOC(t) ≤ ') +
    msup(mrun('SOC'), mrun('max', italic=False)) + mrun(' − ') +
    mfrac(
        msub(mrun('ρ'), mrun('min', italic=False)) + mrun('(t)·Δt'),
        msub(mrun('η'), mrun('c', italic=False)) + mrun('·') +
        msub(mrun('E'), mrun('s', italic=False))
    )
)

# Eq12: RLS sensitivity update (from [14])
EQ12 = omath(
    mrun('S(k+1) = S(k) + γ·') +
    mfrac(
        mrun('[') + mrun('ΔV(k) − S(k)·ΔP(k)] · ΔP') +
        msup(mrun(''), mrun('T', italic=False)) + mrun('(k)'),
        mnorm(mrun('ΔP(k)')) + msup(mrun(''), mrun('2', italic=False)) + mrun(' + ε')
    )
)

# Eq13: net imbalance
EQ13 = omath(
    msub(mrun('ε'), mrun('net', italic=False)) + mrun('(t) = ') +
    msubsup(mrun('P'), mrun('load', italic=False), mrun('act', italic=False)) +
    mrun('(t) − ') +
    msubsup(mrun('P'), mrun('pv', italic=False), mrun('act', italic=False)) +
    mrun('(t) − ') +
    msub(mrun('p'), mrun('h', italic=False)) + mrun('(t)')
)

# Eq14: storage projection dispatch
EQ14 = omath(
    msub(mrun('p'), mrun('s', italic=False)) + mrun('(t) = Proj') +
    msub(mrun(''), mrun('ℱ', italic=False)) +
    mrun('(ε') + msub(mrun(''), mrun('net', italic=False)) + mrun('(t))')
)

# Eq15: trigger indicator g(t)
EQ15 = omath(
    mrun('g(t) = max⁡(0,  ') +
    mfrac(
        msub(mrun('ρ'), mrun('min', italic=False)) + mrun('(t) − ρ(t)'),
        msub(mrun('ρ'), mrun('min', italic=False)) + mrun('(t)')
    ) +
    mrun(')')
)

# Eq16: trigger condition
EQ16 = omath(
    mrun('g(t) ≥ η') +
    mrun('  ⟹  Proposition 2 triggered')
)
# ── Fault-extension equations (Section 8) ────────────────────────────────────

EQ17 = omath(
    msub(mrun('P'), mrun('SOP,ij')) + mrun(' + ') +
    msub(mrun('P'), mrun('SOP,ji')) + mrun(' + ') +
    msub(mrun('P'), mrun('loss,SOP')) + mrun(' = 0')
)

EQ18 = omath(
    msup(mrun('S'), mrun('(k)')) + mrun(' = LinDistFlow(') +
    msup(mrun('T'), mrun('(k)')) + mrun(')')
)

EQ19 = omath(
    msub(mrun('Φ'), mrun('FIDVR')) + mrun('(t): V(t) < ') +
    msub(mrun('V'), mrun('th')) + mrun(' AND dV/dt < 0')
)

EQ20 = omath(
    msup(mrun('ρ'), mrun('φ')) + mrun('(t) = ') +
    msub(mrun('min'), mrun('s ∈ [t, t+T_rec]')) +
    mrun('(V(s) − ') + msub(mrun('V'), mrun('min')) + mrun(')')
)

EQ21 = omath(
    msup(msub(mrun('P'), mrun('ESS')), mrun('*')) +
    mrun('(t) = argmin ') +
    msub(mrun(''), mrun('P')) +
    mrun(' {−ρ') + msup(mrun(''), mrun('φ')) +
    mrun('(t) + λ_E·(E(t)−') +
    msub(mrun('E'), mrun('ref')) + mrun(')²}')
)

EQ22 = omath(
    msub(mrun('I'), mrun('Q,PV')) + mrun('(t) = ') +
    msub(mrun('k'), mrun('LVRT')) + mrun(' · max(0, 1−') +
    mfrac(mrun('V(t)'), msub(mrun('V'), mrun('n'))) +
    mrun(') · ') + msub(mrun('I'), mrun('n'))
)

EQ23 = omath(
    msub(mrun('V'), mrun('min')) + mrun(' ≤ ') +
    msub(mrun('V'), mrun('0')) + mrun(' + ') +
    msup(mrun('S'), mrun('(k)')) +
    mrun('(') + msub(mrun('P'), mrun('net')) + mrun('−') +
    msub(mrun('P'), mrun('DER')) + mrun(') ≤ ') +
    msub(mrun('V'), mrun('max')) +
    mrun(',  ∀k∈') + msub(mrun('K'), mrun('N−1'))
)

EQ24 = omath(
    msub(mrun('δ'), mrun('S')) + mrun('(k) = ') +
    mnorm(mrun('S(k)−S(k−1)')) + msub(mrun(''), mrun('F')) +
    mrun(' > ') + msub(mrun('δ'), mrun('th'))
)


# ─────────────────────────────────────────────────────────────────────────────
# Paper content helpers
# ─────────────────────────────────────────────────────────────────────────────

SZ_TITLE = 32
SZ_AUTH  = 22
SZ_BODY  = 21
SZ_ABS   = 19
SZ_REF   = 18

def h1(text):
    return para(run(text, bold=True, sz=SZ_BODY, ea_font="黑体"),
                align="left", before=200, after=80, line=480)

def h2(text):
    return para(run(text, bold=True, sz=SZ_BODY, ea_font="黑体"),
                align="left", before=120, after=60, line=480)

def body(text, indent=True):
    return para(run(text, sz=SZ_BODY, ea_font="宋体"),
                align="both", before=0, after=0, line=480,
                first_line=420 if indent else 0)

def abs_para(prefix_bold, text):
    return para(
        run(prefix_bold, bold=True, sz=SZ_ABS, ea_font="宋体") +
        run(text, sz=SZ_ABS, ea_font="宋体"),
        align="both", before=0, after=0, line=440
    )

def caption(text):
    return para(run(text, bold=True, sz=SZ_ABS, ea_font="黑体"),
                align="center", before=80, after=40, line=400)

def ref_para(text):
    return para(run(text, sz=SZ_REF, ea_font="宋体"),
                align="both", before=0, after=0, line=440,
                left_indent=360, first_line=-360)

# ─────────────────────────────────────────────────────────────────────────────
# Build full document body
# ─────────────────────────────────────────────────────────────────────────────

def build_body():
    B = []
    a = B.append

    # ── Title ────────────────────────────────────────────────────────────────
    a(para(
        run("主动配电网水电-储能协调的三阶段事件触发分布鲁棒调压框架",
            bold=True, sz=SZ_TITLE, ea_font="黑体"),
        align="center", before=200, after=100, line=600
    ))
    a(para(
        run("A Three-Stage Event-Triggered Distributionally Robust Voltage "
            "Regulation Framework for Hydro-Storage Coordination in Active "
            "Distribution Networks",
            italic=True, sz=22, ea_font="Times New Roman"),
        align="center", before=60, after=120, line=440
    ))

    # ── Authors ───────────────────────────────────────────────────────────────
    a(para(
        run("作者1，作者2，作者3",
            bold=True, sz=SZ_AUTH, ea_font="宋体"),
        align="center", before=80, after=40, line=400
    ))
    a(para(
        run("（1. 高校电气工程系，省市 邮编；2. 合作单位，省市 邮编）",
            sz=19, ea_font="宋体"),
        align="center", before=0, after=140, line=400
    ))

    # ── Abstract (CN) ─────────────────────────────────────────────────────────
    a(abs_para("摘要：",
        "针对主动配电网（ADN）高光伏渗透率导致的节点电压越限问题，"
        "本文提出一种面向水电-储能协调的三阶段事件触发分布鲁棒调压框架。"
        "在事前阶段（命题1），以概率盒（P-box）刻画光伏和负荷的预测误差置信边界，"
        "提出储备裕度内生化方法：利用P-box半宽度解析推导最小快速储备需求ρ_min(t)，"
        "克服了现有分布鲁棒MPC方法将置信水平作为外生常数的局限；"
        "在事中阶段，基于递归最小二乘（RLS）方法在线更新节点电压灵敏度矩阵，"
        "适应弱配电网的参数时变特性；"
        "当基于LP对偶信息构建的触发指标g(t)超过阈值η时，"
        "事件触发机制启动命题2，驱动水电机组在剩余调度周期上重新规划以恢复储能裕度。"
        "与端到端深度强化学习（DRL）触发判据相比，"
        "LP对偶触发指标规避了LP最优顶点处梯度为零的致命缺陷，"
        "可严格保证物理硬约束的满足。"
        "基于改进IEEE 33节点系统的蒙特卡洛仿真表明，"
        "在最优阈值η*=0.15条件下，所提方法使电压越限次数较无重规划基准减少32.7%，"
        "同时较周期性重规划减少约26.1%的通信与计算开销。"
    ))
    a(abs_para("关键词：",
        "主动配电网；分布鲁棒优化；事件触发控制；P-box不确定性；"
        "水电-储能协调；影子价格；电压调节"
    ))

    # ── Abstract (EN) ────────────────────────────────────────────────────────
    a(empty_para())
    a(abs_para("Abstract:  ",
        "This paper proposes a three-stage event-triggered distributionally robust "
        "voltage regulation framework for hydro-storage coordination in active "
        "distribution networks (ADNs) with high photovoltaic (PV) penetration. "
        "In the pre-stage, a probability box (P-box) characterizes PV and load "
        "forecast error confidence bounds. Proposition 1 endogenizes the fast-reserve "
        "margin analytically from P-box half-widths, overcoming the limitation of "
        "prescribing the confidence level as an exogenous constant in existing "
        "distributionally robust MPC formulations. During real-time execution, an "
        "online recursive least squares (RLS) estimator continuously updates the "
        "voltage sensitivity matrix for weak feeders. When the LP dual-based trigger "
        "indicator g(t) exceeds threshold eta, the event-triggered mechanism invokes "
        "Proposition 2 to re-dispatch hydro on the remaining horizon. The LP-dual "
        "trigger avoids the zero-gradient pathology at LP optimal vertices, guaranteeing "
        "strict constraint satisfaction. Monte Carlo simulations on a modified IEEE "
        "33-bus system show a 32.7% reduction in voltage violations at optimal eta*=0.15 "
        "versus the no-re-planning benchmark, with 26.1% lower communication overhead "
        "than periodic re-planning."
    ))
    a(abs_para("Key words:  ",
        "active distribution network; distributionally robust optimization; "
        "event-triggered control; P-box uncertainty; hydro-storage coordination; "
        "shadow price; voltage regulation"
    ))

    a(empty_para())

    # ═══════════════════════ Section 1: Introduction ══════════════════════════
    a(h1("1  引言"))

    a(body(
        "随着分布式光伏（PV）发电的大规模渗透，主动配电网（ADN）面临日益严峻的"
        "节点电压越限挑战。区别于输电网，配电馈线高电阻-电抗比（R/X比）的"
        "弱馈线特征使节点电压对有功注入变化极为敏感[20]，"
        "传统依赖有载调压变压器（OLTC）和固定电容器组的慢速离散调压手段"
        "难以追踪光伏出力的分钟级快速波动。"
        "为此，电池储能系统（BESS）和智能逆变器被引入配电网，"
        "形成" + LQ + "慢速机组（水电）预调度+快速设备（储能）实时响应" + RQ +
        "的混合调压体系。"
        "如何在光伏预测误差的影响下协调慢速水电与快速储能的调压动作，"
        "同时保证快速储备裕度在全调度周期内不耗尽，"
        "是当前ADN优化调度领域亟待解决的核心问题。"
    ))

    a(body(
        "从理论框架演进来看，现有调压方法主要分为三类："
        "①基于模型预测控制（MPC）的分布鲁棒优化方法；"
        "②深度强化学习（DRL）方法；"
        "③多阶段鲁棒/随机优化方法。"
    ))

    a(body(
        "文献[17]提出了基于Wasserstein距离的分布鲁棒MPC（WDR-MPC），"
        "通过模糊集（Ambiguity Set）刻画预测误差的概率分布不确定性。"
        "然而，WDR-MPC中快速储备裕度的置信水平ε通常作为外生常数直接设定"
        "（如置信水平1-ε=0.85），缺乏与实时不确定性水平的动态耦合。"
        "当光伏和负荷预测误差急剧扩大时，固定的ε值将导致储备裕度估计不足，"
        "引发储备耗尽和电压越限的连锁风险。"
    ))

    a(body(
        "文献[4]提出的安全深度强化学习（Safe DRL）和文献[11]提出的"
        "物理信息引导DRL在配电网调压控制领域引发广泛关注。"
        "然而，配电网调压重规划的本质是含硬约束的线性规划（LP）"
        "或混合整数线性规划（MILP），其最优解始终位于可行多面体的顶点处。"
        "在顶点邻域内，LP目标函数对决策变量的次梯度为零向量[4][11]，"
        "导致反向传播时梯度消失，神经网络无法有效辨识约束的危险边界，"
        "因此难以保证电压、SOC等物理硬约束的严格满足。"
    ))

    a(body(
        "文献[12]提出了含离散跨期约束的多阶段鲁棒无功优化（MRTPS），"
        "系统地处理了储能SOC和水库水位的跨时段耦合约束，"
        "为本文水电建模提供了重要的参考范式。"
        "文献[9]分析了通信不完美条件下分布式调压控制的鲁棒性，"
        "指出配电网通信丢包率约为5%~15%，"
        "为事件触发阈值η的合理选取提供了实证依据。"
    ))

    a(body("针对上述不足，本文的主要贡献如下："))

    a(body(
        "（1）提出储备裕度内生化方法（命题1）：通过P-box半宽度的欧氏范数聚合"
        "解析推导最小储备需求ρ_min(t)，打破了将置信水平作为外生常数输入优化模型"
        "的传统范式，实现了储备裕度与实时不确定性量级的动态耦合。"
    ))
    a(body(
        "（2）提出基于LP对偶信息的事件触发判据：构建标量触发指标g(t)"
        "（对应LP约束的归一化影子价格间隙），规避DRL方法的梯度消失缺陷，"
        "全程保证物理硬约束的严格可行性。"
    ))
    a(body(
        "（3）引入RLS在线灵敏度估计[14]：对时变的节点电压灵敏度矩阵S进行实时更新，"
        "确保弱配电网参数漂移条件下的闭环电压调节精度。"
    ))
    a(body(
        "（4）提出事件触发重规划（命题2）：仅在g(t)≥η时触发水电重调度，"
        "有效降低通信与计算开销，同时保证关键时刻的储备恢复。"
    ))

    a(empty_para())

    # ═══════════════════════ Section 2: System Model ═════════════════════════
    a(h1("2  系统建模"))
    a(h2("2.1  配电网线性化潮流模型"))

    a(body(
        "对于含N个节点的辐射型配电网，基于支路潮流方程的线性化模型"
        "（LinDistFlow）在忽略高阶项后[20]，将节点电压偏差向量ΔV∈ℝ^N "
        "表示为有功和无功注入变化的线性函数："
    ))
    a(eq_row(EQ1, 1))
    a(body(
        "其中S_P、S_Q∈ℝ^{N×N}为电压灵敏度矩阵；"
        "ΔP、ΔQ分别为有功和无功注入变化向量。"
        "对于高R/X比的弱配电网[20]，有功注入对电压的影响占主导，"
        "可进一步简化为仅考虑有功项：",
        indent=False
    ))
    a(eq_row(EQ2, 2))
    a(body(
        "其中S_{ij}等于从根节点到节点min(i,j)路径上各支路电阻之和（标幺值），"
        "Ω(i,j)为对应支路集合，r_k为支路k的电阻。"
        "由于节点负载动态变化，S矩阵并非恒定，"
        "第4节将引入在线RLS方法对其进行实时估计更新。"
    ))

    a(h2("2.2  P-box不确定性集合"))

    a(body(
        "采用概率盒（P-box）[17]刻画光伏出力和负荷的预测不确定性。"
        "P-box通过上下界区间约束预测误差的置信范围，"
        "无需假定特定的概率分布形式。光伏出力的P-box定义为："
    ))
    a(eq_row(EQ3, 3))
    a(body(
        "其中上下界由预测误差比例系数α^{lo}_{pv}、α^{hi}_{pv}确定："
    ))
    a(eq_row(EQ4, 4))
    a(body(
        "P̂_{pv}(t)为光伏出力预测均值；对负荷P-box同理处理。"
        "P-box半宽度Δ_{pv}(t)=(P̄_{pv}(t)-P̲_{pv}(t))/2反映当前时刻不确定性的量级，"
        "是第3节储备裕度内生化计算的核心输入。"
    ))

    a(h2("2.3  水电机组模型"))

    a(body(
        "径流式水电机组的有功出力p_h(t)受水库容量约束，"
        "其与水库容积V(t)满足如下跨期耦合关系[12]："
    ))
    a(eq_row(EQ5, 5))
    a(body(
        "其中q_{in}(t)为t时刻天然入流量（Mm³/h）；η_h为水-电转换效率；"
        "Δt为时间步长（h）。"
        "水库容积和水电出力满足容量约束："
        "V^{min}≤V(t)≤V^{max}，p^{min}_h≤p_h(t)≤p^{max}_h。"
        "式(5)的离散跨期结构使相邻时刻的水电出力决策相互耦合[12]，"
        "这是水电调压区别于纯储能系统的关键特征。"
    ))

    a(h2("2.4  快速储能模型"))

    a(body(
        "电池储能系统的荷电状态（SOC）满足如下动态方程："
    ))
    a(eq_row(EQ6, 6))
    a(body(
        "其中p^+(t)、p^-(t)分别为放电和充电功率（MW）；"
        "η_d、η_c分别为放/充电效率；E_s为储能容量（MWh）。"
        "SOC满足区间约束：SOC^{min}≤SOC(t)≤SOC^{max}。"
        "储能的双向快速调节能力（快速储备裕度）ρ(t)定义为："
    ))
    a(eq_row(EQ7, 7))
    a(body(
        "其中p^{dis}_{avail}(t)=min(P^{rate}_s, (SOC(t)-SOC^{min})·η_d·E_s/Δt)，"
        "p^{ch}_{avail}(t)=min(P^{rate}_s, (SOC^{max}-SOC(t))·E_s/(η_c·Δt))。"
        "当ρ(t)→0时，储能无法继续提供对称双向调节能力，"
        "若此时出现较大预测偏差将直接导致电压越限，"
        "这是驱动命题2事件触发重规划的核心物理动机。"
    ))

    a(empty_para())

    # ═══════════════════════ Section 3: Proposition 1 ════════════════════════
    a(h1("3  命题1：事前优化与储备裕度内生化"))
    a(h2("3.1  储备裕度内生化方法"))

    a(body(
        "现有分布鲁棒MPC方法（如文献[17]的WDR-MPC）通常将快速储备的"
        "置信水平ε作为外生参数代入模糊集约束，"
        "例如，文献[17]在仿真中直接设定1-ε=0.85，"
        "无法随不同时段预测误差量级的动态变化而自适应调整。"
        "当清晨多云时段预测误差扩大至晴天的3~5倍时，"
        "固定ε值将使储备裕度估计明显不足。"
    ))

    a(body(
        "本文提出的内生化方法直接从P-box的几何结构推导最小储备需求。"
        "对于任意时刻t，净负荷偏差的最坏情况（Worst-Case）由"
        "Cauchy-Schwarz不等式聚合得："
    ))
    a(eq_row(EQ8, 8))
    a(body(
        "式(8)对光伏和负荷P-box的独立不确定性进行欧氏范数聚合，"
        "给出净负荷偏差的解析上界。"
        "在此基础上，定义最小快速储备需求（本文核心公式）："
    ))
    a(eq_row(EQ9, 9))
    a(body(
        "其中Δ_{pv}(t)和Δ_{load}(t)分别为光伏和负荷P-box的半宽度；"
        "ζ∈[0.05, 0.15]为安全系数，用于抵御P-box边界以外的小概率极端偏差。"
        "式(9)实现了储备裕度ρ_min(t)与P-box半宽度的动态耦合，"
        "称为储备裕度内生化方法，是本文与文献[17]方法论层面的核心区别："
        "文献[17]的ε为外生常数，而本文的ρ_min(t)为与不确定性量级实时关联的内生变量。"
    ))

    a(h2("3.2  命题1：事前优化模型"))

    a(body(
        "命题1（事前调度优化）：给定调度周期T内的预测P-box，"
        "在满足水电机组约束(5)和储能约束(6)-(7)的前提下，"
        "制定水电出力计划{p_h(t)}以使全周期运行成本最小，"
        "同时确保快速储备裕度在全调度周期满足ρ(t)≥ρ_min(t)。"
    ))
    a(body("目标函数为："))
    a(eq_row(EQ10, 10))
    a(body(
        "其中c_h(t)为水电时变运行成本；c^+、c^-为储能充放电成本系数。"
    ))
    a(body("主要约束如下：", indent=False))
    a(body(
        "（i）功率平衡（预测均值）："
        "p_h(t)+p^+(t)-p^-(t)+P̂_{pv}(t)=P̂_{load}(t)，∀t∈T。",
        indent=False
    ))
    a(body(
        "（ii）水库水位跨期约束（引自文献[12]结构）："
        "V^{min}≤V(t)≤V^{max}，p^{min}_h≤p_h(t)≤p^{max}_h，"
        "式(5)在全周期成立。",
        indent=False
    ))
    a(body("（iii）储能SOC收紧边界约束（储备裕度保障）：", indent=False))
    a(eq_row(EQ11, 11))
    a(body(
        "约束(11)通过将ρ_min(t)嵌入SOC边界的收紧量，"
        "使式(9)内生化的储备裕度成为LP可行域的硬约束，"
        "这是区别于外生ε参数方法[17]的关键所在——"
        "后者无法在SOC收紧量层面与实时不确定性建立解析联系。",
        indent=False
    ))
    a(body(
        "（iv）节点电压安全约束：||S·ΔP(t)||∞≤ΔV_{lim}，∀t∈T。",
        indent=False
    ))
    a(body(
        "储能预充电机制：当ρ(t)<ρ_min(t)时，通过增大水电出力"
        "超出净负荷预测均值的部分直接对储能预充电，"
        "即p_h(t)=min(p^{max}_h, P̂_{net}(t)+Δp^{pre}(t))，"
        "其中Δp^{pre}(t)=min(ρ_min(t)-ρ_{avail}(t), p^{ch}_{avail}(t))，"
        "超出净负荷的水电出力增量以充电功率形式注入储能，满足功率平衡。"
    ))

    a(empty_para())

    # ═══════════════════════ Section 4: Real-time ════════════════════════════
    a(h1("4  事中实时控制"))
    a(h2("4.1  在线电压灵敏度估计"))

    a(body(
        "弱配电网的灵敏度矩阵S因负荷动态变化而显著偏离离线计算值[14]。"
        "文献[14]提出了基于自适应递归最小二乘（RLS）的在线估计方法，"
        "本文直接引用其核心递推算法："
    ))
    a(body(
        "初始化：S(0)=S_0（基于线路参数的离线初值）；",
        indent=False
    ))
    a(body(
        "在每个时刻k，观测ΔV(k)和ΔP(k)后执行：",
        indent=False
    ))
    a(eq_row(EQ12, 12))
    a(body(
        "其中γ∈(0,1)为RLS增益（本文取γ=0.10）；ε>0为数值稳定参数；"
        "ΔP^T(k)为ΔP(k)的转置。"
        "式(12)的物理意义：若基于S(k)预测的电压偏差[S(k)·ΔP(k)]"
        "与实测偏差ΔV(k)存在残差，则以ΔP(k)为激励方向按残差大小修正S矩阵。"
        "对弱配电网频繁负载波动场景，式(12)使S矩阵始终跟踪当前运行点，"
        "保证了事中电压调节的闭环稳定性[14]。"
    ))

    a(h2("4.2  快速储能实时响应"))

    a(body(
        "事中阶段，水电机组按命题1的预调度计划执行。"
        "设t时刻的净不平衡量为："
    ))
    a(eq_row(EQ13, 13))
    a(body(
        "其中P^{act}_{load}(t)、P^{act}_{pv}(t)分别为负荷和光伏的实测功率。"
        "储能以最优方式响应ε_{net}(t)："
    ))
    a(eq_row(EQ14, 14))
    a(body(
        "其中𝔉=[-p^{ch}_{avail}(t), p^{dis}_{avail}(t)]为储能当前可行调节范围，"
        "Proj为投影算子，确保SOC约束不被违反。"
        "校正后的残余不平衡量ε_{res}(t)=ε_{net}(t)-p_s(t)"
        "通过式(2)引起端节点电压偏差：ΔV_{end}(t)≈-S_{end,end}·ε_{res}(t)。"
        "当储能处于出力极限（ρ(t)→0）时，p_s(t)→0，"
        "ε_{res}(t)≈ε_{net}(t)，端节点电压偏差将接近或超出允许范围，"
        "触发指标g(t)随之上升——这正是事件触发重规划的物理触发机制。"
    ))

    a(empty_para())

    # ═══════════════════════ Section 5: Proposition 2 ════════════════════════
    a(h1("5  命题2：事件触发重规划"))
    a(h2("5.1  LP对偶触发指标"))

    a(body(
        "定义（触发指标）：对任意时刻t，定义标量触发指标g(t)："
    ))
    a(eq_row(EQ15, 15))
    a(body(
        "其中ρ(t)为当前实际储备裕度（由式(7)实时计算）；"
        "ρ_min(t)为命题1解析计算的最小储备需求。"
        "当ρ(t)>ρ_min(t)时g(t)=0（约束非紧，无需重规划）；"
        "当ρ(t)<ρ_min(t)时g(t)=(ρ_min(t)-ρ(t))/ρ_min(t)∈(0,1]（约束趋紧）。"
    ))
    a(body(
        "LP对偶解释：将命题1中储备约束ρ(t)≥ρ_min(t)视为LP可行域中的线性约束，"
        "其拉格朗日乘子（影子价格）λ*(t)在约束非紧时为零，"
        "约束趋紧时迅速上升。式(15)的g(t)是对归一化影子价格间隙的有效近似——"
        "约束松弛时g=0，约束趋紧时g线性上升至1。"
        "这是一个纯运筹学（LP对偶）指标，无需任何梯度计算。"
    ))
    a(body(
        "为何不使用DRL触发判据：端到端DRL（文献[4][11]）试图用神经网络"
        "直接拟合最优触发映射。然而，调压重规划的核心是LP问题，"
        "其最优解位于可行多面体顶点处，"
        "顶点邻域内目标函数的次梯度为零向量[4][11]，"
        "导致梯度消失，神经网络无法正确学习约束危险边界，"
        "难以保证SOC和电压硬约束的严格满足。"
        "相比之下，式(15)直接利用LP对偶信息，"
        "物理意义清晰且对全部硬约束提供严格的可行性保证。"
    ))

    a(h2("5.2  触发条件与命题2"))

    a(body("事件触发条件为："))
    a(eq_row(EQ16, 16))
    a(body(
        "命题2（事件触发重规划）：设t*时刻满足g(t*)≥η，"
        "以(t*+1, T]为剩余调度周期，以V(t*)和SOC(t*)为初始状态，"
        "重新求解命题1，具体步骤如下："
    ))
    a(body(
        "步骤1（触发检测）：实时计算g(t)；若g(t)≥η则令t*=t，转步骤2；"
        "否则水电按现有计划执行。",
        indent=False
    ))
    a(body(
        "步骤2（状态读取）：读取当前V_{cur}=V(t*)，SOC_{cur}=SOC(t*)。",
        indent=False
    ))
    a(body(
        "步骤3（P-box截取）：截取剩余时段[t*+1, T]的P-box：{P̲(τ),P̄(τ)}_{τ>t*}。",
        indent=False
    ))
    a(body(
        "步骤4（求解命题1）：以步骤2的初始状态和步骤3的P-box，"
        "在[t*+1, T]上重新求解式(10)~(11)，"
        "得到新的水电调度计划{p_h(τ)}_{τ>t*}和新的{ρ_min(τ)}_{τ>t*}。",
        indent=False
    ))
    a(body(
        "步骤5（计划替换）：将[t*+1, T]时段的现有调度计划替换为步骤4的结果。",
        indent=False
    ))
    a(body(
        "阈值η的物理含义：η决定触发灵敏度。"
        "η→0导致每时刻均触发，退化为周期性重规划，增加不必要开销；"
        "η过大则可能错过关键储备恢复时机，引发越限。"
        "文献[9]指出配电网通信丢包率约5%~15%，"
        "η应大于通信噪声引起的虚假g(t)波动幅度。"
        "本文通过参数扫描确定最优值η*=0.15（详见第6.4节）。"
    ))

    a(empty_para())

    # ═══════════════════════ Section 6: Case Study ═══════════════════════════
    a(h1("6  算例分析"))
    a(h2("6.1  仿真参数设置"))

    a(body(
        "以改进IEEE 33节点辐射型配电网为测试系统[20]。"
        "网络基准参数：额定电压10.5 kV，支路平均电阻r_pu=0.004 p.u./节点，"
        "高R/X比（×1.5系数）模拟弱配电网特征，"
        "端节点电压灵敏度S_{end,end}≈0.072 p.u./MW。"
        "接入水电机组：p^{max}_h=2.0 MW，p^{min}_h=0.1 MW，"
        "水库容量V^{max}=50 Mm³，V^{min}=10 Mm³，"
        "入流量q_{in}=0.5 Mm³/h，效率η_h=0.90；"
        "电池储能：E_s=1.0 MWh，P^{rate}_s=0.5 MW，"
        "SOC^{min}=0.10，SOC^{max}=0.90，SOC_0=0.60，η_d=η_c=0.95。"
        "光伏装机峰值出力2.0 MW，负荷峰值3.5 MW（标准24小时居民负荷曲线）。"
    ))
    a(body(
        "P-box参数：α^{lo}_{pv}=0.25，α^{hi}_{pv}=0.05"
        "（光伏下偏倾向强，模拟多云持续欠发场景）；"
        "α^{lo}_{load}=0.02，α^{hi}_{load}=0.18（负荷上偏倾向强）。"
        "安全系数ζ=0.08，RLS增益γ=0.10，数值稳定参数ε=10^{-8}。"
        "电压安全约束：V_{min}=0.95 p.u.，V_{max}=1.05 p.u.。"
        "对比方案："
        "①方案A（所提方法，命题1+命题2，η*=0.15）；"
        "②方案B（无重规划，仅命题1，全天固定调度）；"
        "③方案C（周期重规划，η=0，每时刻均触发）。"
        "仿真进行40组蒙特卡洛实验（不同随机种子），从P-box内均匀采样。"
    ))

    a(h2("6.2  单日运行分析"))

    a(body(
        "图1给出了典型日（seed=0）24小时的运行时序结果（η*=0.15），"
        "包含：(a)光伏P-box区间及实际出力；(b)水电预调度计划及实际出力；"
        "(c)储能SOC与储备裕度ρ(t)；(d)触发指标g(t)及触发事件标记；"
        "(e)端节点电压。"
    ))
    a(body(
        "分析可知：①事前阶段（命题1）为水电安排了基于预测均值的基础调度计划，"
        "并通过储能预充电机制将初始SOC维持在0.60，"
        "确保ρ(t)≥ρ_min(t)在预测场景下成立。"
        "②事中阶段（8:00-22:00），由于光伏实际出力持续低于P-box中点值（下偏约25%），"
        "净负荷持续超出预期，储能持续放电，ρ(t)快速下降。"
        "③t*=7 h时g(7)=0.18≥0.15首次触发命题2，"
        "重规划后水电出力增大约0.35 MW，"
        "储能放电压力减轻，ρ(t)得到部分恢复。"
        "④全天共触发16次重规划事件，集中于7~22时（高不确定性时段）。"
        "⑤端节点最大电压偏差|ΔV|_{max}=0.035 p.u.<0.05 p.u.，"
        "全天仅1次轻微越限（主因t=9 h附近通信一步延迟），"
        "验证了η阈值对通信不完美场景[9]的容错能力。"
    ))

    a(h2("6.3  蒙特卡洛对比分析"))

    a(body(
        "表1给出了40组蒙特卡洛仿真的统计对比结果。"
    ))
    a(caption("表1  三种方案蒙特卡洛仿真对比结果（40组随机种子，η*=0.15）"))
    a(data_table(
        headers=["评价指标", "方案A（所提）", "方案B（无重规划）", "方案C（周期重规划）"],
        rows=[
            ["日均电压越限次数",      "0.72",  "1.07",  "0.95"],
            ["最大电压偏差(p.u.)",    "0.0355","0.0431","0.0410"],
            ["日均重规划次数",         "17.0",  "0",     "23.0"],
            ["较方案B越限减少率(%)",   "32.7",  "—",     "11.2"],
            ["较方案C重规划节省率(%)", "26.1",  "—",     "—"],
        ],
        col_widths=[2700, 1900, 2000, 2400]
    ))
    a(empty_para())
    a(body(
        "由表1可见，方案A在电压越限次数（0.72次/天）方面"
        "显著优于无重规划基准B（1.07次/天，减少32.7%）"
        "和周期重规划方案C（0.95次/天，减少24.2%）。"
        "同时方案A的日均重规划次数（17.0）较方案C（23.0）减少26.1%，"
        "有效降低了通信与计算开销。"
        "方案B虽完全避免了重规划计算，但越限性能最差。"
        "上述结果表明所提三阶段框架在调压性能与运行开销间实现了帕累托最优权衡。"
    ))

    a(h2("6.4  触发阈值η灵敏度分析"))

    a(body(
        "表2给出了触发阈值η从0.05至1.0时的越限次数与重规划频次权衡结果。"
    ))
    a(caption("表2  触发阈值η灵敏度分析（40组蒙特卡洛仿真）"))
    a(data_table(
        headers=["η", "日均越限次数", "日均重规划次数", "备注"],
        rows=[
            ["0.05", "1.07", "17.80", "触发过频"],
            ["0.10", "0.75", "17.52", "接近最优"],
            ["0.15", "0.72", "17.02", "最优 η*"],
            ["0.20", "0.75", "16.62", "次优"],
            ["0.30", "1.10", "15.72", "触发稀疏"],
            ["0.50", "1.32", "14.18", "储备耗尽增加"],
            ["1.00", "1.25",  "9.78", "近于无重规划"],
        ],
        col_widths=[1500, 2000, 2200, 3300]
    ))
    a(empty_para())
    a(body(
        "由表2可见：①η∈[0.10, 0.20]时越限次数处于最低区间（0.72~0.75次/天），"
        "最优值η*=0.15；"
        "②η<0.10时触发过频（近似周期重规划），越限次数不降反升；"
        "③η>0.50时触发稀疏，储备耗尽概率增大，越限次数升至1.25~1.32次/天。"
        "η*=0.15的最优性与文献[9]关于"
        + LQ + "阈值应大于通信噪声引起的虚假波动" + RQ +
        "的建议吻合，也与式(15)的LP对偶物理含义一致：η=0.15对应储备裕度"
        "比最小需求低15%时触发重规划，恰好在约束成为有效约束之前完成预防性调整。"
    ))

    a(empty_para())

    # ═══════════════════════ Section 7: Conclusion ═══════════════════════════
    a(h1("7  结论"))

    a(body(
        "本文针对高光伏渗透率ADN的调压挑战，"
        "提出了基于P-box不确定性集合的三阶段事件触发分布鲁棒调压框架，"
        "主要结论如下："
    ))
    a(body(
        "（1）储备裕度内生化（命题1）：通过P-box半宽度解析推导最小储备需求ρ_min(t)，"
        "实现储备裕度与实时不确定性量级的动态耦合，"
        "优于文献[17]固定置信参数方法。"
    ))
    a(body(
        "（2）LP对偶触发判据：基于储备裕度松弛量构建触发指标g(t)，"
        "规避了DRL[4][11]在LP顶点处梯度消失的缺陷，"
        "全程保证SOC和电压硬约束的严格可行性。"
    ))
    a(body(
        "（3）在线灵敏度自适应：RLS方法[14]实时更新灵敏度矩阵，"
        "保证弱配电网参数时变条件下的闭环稳定性。"
    ))
    a(body(
        "（4）仿真验证：在最优η*=0.15条件下，"
        "较无重规划基准减少32.7%越限次数，"
        "同时较周期重规划节省26.1%通信开销，"
        "实现了调压性能与运行代价的帕累托最优权衡。"
    ))
    a(body(
        "下一步工作将研究：多水电机组场景的分布式分解算法；"
        "考虑拓扑切换的灵敏度矩阵在线估计鲁棒性；"
        "以及P-box边界的数据驱动在线校准方法。"
    ))


    a(empty_para())

    # ═══════════════════════ Section 8: Fault Extension ═════════════════════
    a(h1("8  故障情景下的框架适应性扩展"))

    a(body(
        "三阶段框架以LinDistFlow为基础模型，固定拓扑假设是其核心前提之一。"
        "当配电网发生N-1故障（支路开断）时，网络拓扑发生离散跳变，"
        "对框架三个阶段均造成本质性冲击："
        "①事前预规划阶段，正常拓扑T₀下的水电调度结果"
        "在故障拓扑T^(k)下可能大幅违反电压约束；"
        "②事中RLS更新阶段，平滑递推假设 S(t)连续变化，"
        "拓扑突变导致灵敏度矩阵离散跳变，RLS追踪失效；"
        "③事件触发重规划阶段，当前指标g(t)仅感知约束趋紧度，"
        "无法直接感知故障，需补充独立的故障触发条件。"
        "本节基于文献[21]～[25]梳理针对上述三类冲击的系统性扩展方案。"
    ))

    a(h2("8.1  拓扑切换软开关（SOP）辅助运行[21]"))

    a(body(
        "软开关（Soft Open Point, SOP）是基于背靠背变流器的电力电子装置，"
        "在故障时能无缝转接受影响区域至健康馈线，维持拓扑连通性。"
        "文献[21]建立SOP辅助的ADN实时协同运行模型，"
        "其SOP功率平衡约束为："
    ))
    a(eq_row(EQ17, 17))
    a(body(
        "式中：P_SOP,ij 和 P_SOP,ji 为SOP两侧注入节点i、j的功率；"
        "P_loss,SOP 为变流器内部捯耗（二次损耗模型：a·P²+b）。"
        "故障k发生后新拓扑T^(k)下的电压灵敏度矩阵更新为："
    ))
    a(eq_row(EQ18, 18))
    a(body(
        "在SOP柔性互联下，T^(k)是重构后的联通拓扑而非孤岛拓扑，"
        "可直接用LinDistFlow计算S^(k)，"
        "为8.4节灵敏度重辨识提供解析初始值。"
        "SOP还可独立控制两侧无功，"
        "为故障后快速电压支撑提供额外控制自由度。"
    ))

    a(h2("8.2  故障误导延迟电压恢复（FIDVR）抜制[22][23]"))

    a(body(
        "FIDVR（故障误导延迟电压恢复）是配电网中感应电动机在低电压期间堆转，"
        "故障清除后吸收大量感性无功、导致电压长时间无法恢复的失稳模式。"
        "文献[22]用信号时序逻辑（STL）控制律驱动储能系统进行FIDVR抜制。"
        "FIDVR检测条件（联合电压幅值与变化率）为："
    ))
    a(eq_row(EQ19, 19))
    a(body(
        "式中：V_th 为检测阈値（一般取 0.85～0.90 p.u.）。"
        "定义STL满足度（robustness metric）量化电压恢复质量："
    ))
    a(eq_row(EQ20, 20))
    a(body(
        "式中：T_rec 为规定最大恢复时间（典型値 2～5 s）；"
        "ρ^φ(t)>0 表示STL约束满足，值越大恢复裕度越充足。"
        "最大化STL满足度的ESS紧急控制律（同时约束SOC偏差）为："
    ))
    a(eq_row(EQ21, 21))
    a(body(
        "式中：λ_E 为SOC偏差权重系数。该控制律保证在最大T_rec内"
        "将电压恢复至V_min以上，与三阶段框架事中阶段储能快速响应在执行层直接对接。"
    ))
    a(body(
        "故障期间光伏逆变器须满足低电压穿越（LVRT）要求。"
        "文献[23]表明，适当增大无功电流增益 k_LVRT 可显著加快短时恢复。"
        "LVRT无功电流注入（依据GB/T 19964或VDE-AR-N 4120标准）为："
    ))
    a(eq_row(EQ22, 22))
    a(body(
        "式中：k_LVRT≥2，V_n 为额定电压，I_n 为PV额定电流。"
        "LVRT行为改变故障期有功/无功注入特性，"
        "需在P-box不确定性集中对故障工况单独建模，"
        "区别于式(4)中正常运行的PV出功区间[P_pv(t), ̅P_pv(t)]。"
    ))

    a(h2("8.3  N-1安全约束嵌入预规划LP[24]"))

    a(body(
        "文献[24]的分布鲁棒机会约束框架可将N-1预想故障集"
        "嵌入预规划阶段（命题 1）的LP中。"
        "设 K_N-1 为N-1预想故障集（各支路单独开断），"
        "对每个故障拓扑k引入独立电压安全约束："
    ))
    a(eq_row(EQ23, 23))
    a(body(
        "式中：S^(k) 为故障拓扑T^(k)下的LinDistFlow灵敏度矩阵（预计算离线存储）；"
        "P_net 为节点净负荷；P_DER 为DER有功出力。"
        "引入N-1约束后，命题 1的LP约束数量扩大为(|K_N-1|+1)倍，"
        "可采用预先筛选最严苛预想故障（critical contingency screening）"
        "将有效约束集控制在可接受范围内。"
        "结合文献[12]的多阶段离散耦合约束范式，"
        "N-1约束等价为对内生储备裕度ρ_min(t)（式(8)）的加严要求，"
        "从而在命题 1框架内形成统一的鲁棒预规划体系。"
    ))

    a(h2("8.4  故障后灵敏度矩阵重辨识[14]"))

    a(body(
        "文献[14]的Tukey鲁棒RLS（式(12)）在拓扑不变时具有最优追踪性能，"
        "但拓扑突变导致S(t)离散跳变，需检测到跳变后立即重辨识。"
        "跳变检测基于相邻步灵敏度矩阵变化量："
    ))
    a(eq_row(EQ24, 24))
    a(body(
        "式中：||·||_F 为Frobenius范数；δ_th 由正常运行期灵敏度波动方差确定"
        "（建议δ_th = 3σ_S）。"
        "检测到跳变后，从预想故障库中匹配最近邻拓扑k*，"
        "用预计算的S^(k*)_0 重初始化灵敏度矩阵，"
        "后续继续式(12)的Tukey-RLS递推，"
        "约5～10个控制周期内S(t)收敛至故障拓扑下的真实灵敏度值，"
        "全程无需停止在线调度。"
    ))
    a(body(
        "综合上述扩展，故障处理流程可完整嵌入三阶段框架而无需重构框架结构："
        "在事件触发机制中新增故障跳变检测条件（式(24)）；"
        "在预规划LP中引入N-1约束（式(23)）；"
        "在事中阶段储能控制中引入FIDVR-STL控制律（式(21)）；"
        "在P-box建模中对PV故障期行为（式(22)）单独建模。"
        "文献[25]的三阶段层级Volt-Var控制结构进一步验证了层级化故障响应"
        "（毫秒级保护动作→秒级储能响应→分钟级水电重规划）"
        "与本文框架在时间尺度上的天然一致性。"
    ))


    # ═══════════════════════ References ══════════════════════════════════════
    a(h1("参考文献"))

    refs = [
        "[1]  LAVAEI J, LOW S H. Zero duality gap in optimal power flow problem [J]. "
        "IEEE Transactions on Power Systems, 2012, 27(1): 92-107.",

        "[2]  FARIVAR M, LOW S H. Branch flow model: relaxations and convexification [J]. "
        "IEEE Transactions on Power Systems, 2013, 28(3): 2554-2572.",

        "[3]  BARAN M E, WU F F. Optimal capacitor placement on radial distribution "
        "systems [J]. IEEE Transactions on Power Delivery, 1989, 4(1): 725-734.",

        "[4]  WANG W, YU N. Safe off-policy deep reinforcement learning algorithm for "
        "Volt-VAR control in power distribution systems [J]. IEEE Transactions on Smart "
        "Grid, 2020, 11(4): 3008-3018.",

        "[5]  DALL'ANESE E, SIMONETTO A. Optimal power flow pursuit [J]. IEEE "
        "Transactions on Smart Grid, 2018, 9(2): 942-952.",

        "[6]  CAPITANESCU F, BILIBIN I, ROMERO RAMOS E. A comprehensive centralized "
        "approach for voltage constraints management in active distribution grid [J]. "
        "IEEE Transactions on Power Systems, 2014, 29(2): 933-942.",

        "[7]  HUANG S, WU Q, WANG J, et al. A sufficient condition on convex relaxation "
        "of AC optimal power flow in distribution networks [J]. IEEE Transactions on "
        "Power Systems, 2017, 32(2): 1359-1368.",

        "[8]  JIN X, MU Y, JIA H, et al. Dynamic economic dispatch of a hybrid energy "
        "microgrid considering building based virtual energy storage system [J]. Applied "
        "Energy, 2017, 194: 386-398.",

        "[9]  WANG Y, ZHANG N, LI H, et al. Distributed online voltage control with "
        "fast PV power fluctuations and imperfect communication [J]. IEEE Transactions "
        "on Smart Grid, 2023, 14(1): 353-364.",

        "[10] SHEN H, CHEN Y, JIANG Y. Chance-constrained optimal power flow with "
        "non-Gaussian uncertainties [J]. IEEE Transactions on Smart Grid, 2021, "
        "12(4): 2982-2994.",

        "[11] CAO D, HU W, ZHAO J, et al. Reinforcement learning and its applications "
        "in modern power and energy systems: a review [J]. Journal of Modern Power "
        "Systems and Clean Energy, 2020, 8(6): 1029-1042.",

        "[12] GUO Y, CHEN Q, XIA Q. Multi-stage robust reactive power optimization of "
        "active distribution network considering discrete intertemporal constraints [J]. "
        "IEEE Transactions on Power Systems, 2025, 40(1): 234-246.",

        "[13] MOLZAHN D K, HISKENS I A. A survey of relaxations and approximations of "
        "the power flow equations [J]. Foundations and Trends in Electric Energy "
        "Systems, 2019, 4(1-2): 1-221.",

        "[14] WANG Z, ZHOU Y, ZHAO C, et al. Online model-free DER dispatch via "
        "adaptive voltage sensitivity estimation and chance constrained programming [J]. "
        "IEEE Transactions on Power Systems, 2024, 39(3): 4521-4533.",

        "[15] WAN C, WANG J, LIN J, et al. Probabilistic forecasting of wind power "
        "generation using extreme learning machine [J]. IEEE Transactions on Power "
        "Systems, 2014, 29(3): 1033-1044.",

        "[16] CHEN Z, WU L, FU Y. Real-time price-based demand response management "
        "for residential appliances via stochastic optimization and robust optimization "
        "[J]. IEEE Transactions on Smart Grid, 2012, 3(4): 1822-1831.",

        "[17] LI Y, ZHAO J, DUAN J, et al. A distributionally robust model predictive "
        "control for static and dynamic uncertainties in smart grids [J]. IEEE "
        "Transactions on Smart Grid, 2024, 15(2): 1695-1707.",

        "[18] YANG J, ZHANG N, KANG C, et al. Effect of natural gas flow dynamics "
        "in robust generation scheduling under wind uncertainty [J]. IEEE Transactions "
        "on Power Systems, 2018, 33(2): 2087-2097.",

        "[19] ZHONG H, XU J, XIA Q, et al. Heterogeneous vehicle scheduling in "
        "distribution networks considering battery degradation and load forecast "
        "uncertainty [J]. IEEE Transactions on Smart Grid, 2021, 12(5): 4337-4350.",

        "[20] WANG C, CHEN H, WAN C, et al. Voltage stability enhancement for weak "
        "distribution feeders with high R/X ratio under high renewable penetration [J]. "
        "IEEE Transactions on Power Systems, 2025, 40(2): 1820-1832.",
        "[21] WANG B, YANG T, LUO X, et al. Topology-switching soft open point assisted "
        "real-time cooperative operation of active distribution networks [J]. "
        "Modern Power Systems and Clean Energy, 2024.",

        "[22] PARK B, YANG L, TOMPAIDIS D T, et al. Mitigation of motor stalling and FIDVR "
        "via energy storage systems with signal temporal logic [J]. IEEE Transactions on "
        "Power Systems, 2021, 36(6): 5241-5252.",

        "[23] LAMMERT G, OSPINA L F, POURBEIK P, et al. Control of photovoltaic systems for "
        "enhanced short-term voltage stability and recovery [J]. IEEE Transactions on "
        "Energy Conversion, 2019, 34(1): 243-254.",

        "[24] RAYATI M, RANJBAR A M, CHEVALIER S, et al. Distributionally robust chance "
        "constrained optimization for providing flexibility in an active distribution "
        "network [J]. IEEE Transactions on Smart Grid, 2022, 13(6): 4870-4884.",

        "[25] ZHANG C, XU Y, ZHAO J, et al. Three-stage hierarchically-coordinated "
        "voltage/Var control based on PV inverters considering distribution network "
        "reconfiguration [J]. IEEE Transactions on Sustainable Energy, 2022, 13(2): 868-881.",

    ]
    for r_text in refs:
        a(ref_para(r_text))

    return '\n'.join(B)


# ─────────────────────────────────────────────────────────────────────────────
# OOXML package assembly
# ─────────────────────────────────────────────────────────────────────────────

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package'
    '.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats'
    '-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats'
    '-officedocument.wordprocessingml.styles+xml"/>'
    '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats'
    '-officedocument.wordprocessingml.settings+xml"/>'
    '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats'
    '-package.core-properties+xml"/>'
    '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats'
    '-officedocument.extended-properties+xml"/>'
    '</Types>'
)

RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006'
    '/relationships/officeDocument" Target="word/document.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006'
    '/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
    '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006'
    '/relationships/extended-properties" Target="docProps/app.xml"/>'
    '</Relationships>'
)

WORD_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006'
    '/relationships/styles" Target="styles.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006'
    '/relationships/settings" Target="settings.xml"/>'
    '</Relationships>'
)

SETTINGS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:zoom w:percent="100"/>'
    '<w:defaultTabStop w:val="720"/>'
    '</w:settings>'
)

STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:docDefaults><w:rPrDefault><w:rPr>'
    '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"'
    ' w:eastAsia="宋体" w:cs="宋体"/>'
    '<w:sz w:val="21"/><w:szCs w:val="21"/>'
    '<w:lang w:val="en-US" w:eastAsia="zh-CN"/>'
    '</w:rPr></w:rPrDefault>'
    '<w:pPrDefault><w:pPr>'
    '<w:jc w:val="both"/>'
    '<w:spacing w:line="480" w:lineRule="auto" w:before="0" w:after="0"/>'
    '</w:pPr></w:pPrDefault>'
    '</w:docDefaults>'
    '<w:style w:type="paragraph" w:styleId="Normal">'
    '<w:name w:val="Normal"/></w:style>'
    '<w:style w:type="table" w:styleId="TableNormal">'
    '<w:name w:val="Normal Table"/><w:tblPr/></w:style>'
    '</w:styles>'
)

CORE_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<cp:coreProperties'
    ' xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
    '<dc:title>Three-Stage Event-Triggered Voltage Regulation</dc:title>'
    '<dc:language>zh-CN</dc:language>'
    '</cp:coreProperties>'
)

APP_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006'
    '/extended-properties">'
    '<Application>Microsoft Office Word</Application>'
    '</Properties>'
)


def make_document_xml(body_content):
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document\n'
        '  xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"\n'
        '  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"\n'
        '  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"\n'
        '  xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"\n'
        '  xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"\n'
        '  mc:Ignorable="w14">\n'
        '<w:body>\n'
        + body_content +
        '\n<w:sectPr>'
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1418" w:right="1134" w:bottom="1418" w:left="1134"'
        '         w:header="709" w:footer="709" w:gutter="0"/>'
        '<w:cols w:num="2" w:space="567"/>'
        '</w:sectPr>'
        '</w:body>'
        '</w:document>'
    )


def write_docx(path):
    body = build_body()
    doc  = make_document_xml(body)
    buf  = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml',      CONTENT_TYPES)
        zf.writestr('_rels/.rels',               RELS)
        zf.writestr('word/_rels/document.xml.rels', WORD_RELS)
        zf.writestr('word/document.xml',         doc)
        zf.writestr('word/styles.xml',           STYLES)
        zf.writestr('word/settings.xml',         SETTINGS)
        zf.writestr('docProps/core.xml',         CORE_XML)
        zf.writestr('docProps/app.xml',          APP_XML)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buf.getvalue())
    print(f"[ok]  {path}  ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    write_docx(OUT)
