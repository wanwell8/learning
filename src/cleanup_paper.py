"""Clean up the latest user-uploaded paper:
  1. Delete Table I (the qualitative comparison table) -- both its caption
     paragraph and the <w:tbl> element itself.
  2. Rewrite the paragraph that introduced Table I so the section still flows
     and the contribution positioning is preserved as prose.
  3. Fix the Fig. 2 caption to add the probabilistic-baseline curve that the
     figure actually shows.

The newly uploaded docx uses the schemas.openxmlformats namespace and has
real embedded figures, so we keep the binary parts (media/embeddings) intact
and only patch word/document.xml.
"""

from __future__ import annotations

import copy
import shutil
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SRC_DOCX = Path("/root/.claude/uploads/f42250ba-9904-4eaf-978b-d6768fc5cc48/06df1a41-MultiDriver_DR_Interval_Modeling_Conference.docx")
OUT_DOCX = ROOT / "paper" / "MultiDriver_DR_Interval_Modeling_Conference_revised.docx"

NS_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ET.register_namespace("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main")

# -- New text for paragraph [32], with the "three vs four" inconsistency fixed
NEW_PARA_32 = (
    "These streams differ on several fronts that matter for active distribution "
    "networks: how the response is mathematically represented (probability density, "
    "membership function, parameter set, or bounds), whether more than one driver is "
    "varied at a time, whether a daily energy balance is enforced, the optimisation "
    "cost they impose downstream, and the data they require. Probabilistic descriptions "
    "need many observations and enforce balance only implicitly through the chosen "
    "distribution; conventional interval and fuzzy methods need only bounds or an "
    "expert-supplied membership function but typically skip the balance check; "
    "decision-dependent formulations are the most expressive but the most expensive. "
    "The proposed multi-driver interval approach occupies an intermediate position: it "
    "varies two drivers jointly, so it is more expressive than the fixed-parameter and "
    "single-driver baselines, yet it is lighter in assumption load and computation than "
    "probabilistic or decision-dependent approaches, and the daily energy balance is "
    "built into the candidate-trajectory filter rather than added as a downstream check."
)

# -- New text for Fig. 1 caption (was Fig. 2). The figure shows envelopes for the three typical days.
NEW_FIG1_CAPTION = (
    "Comparison of 24-hour DR response interval envelopes at node 30 for the three "
    "typical days under the proposed, unconstrained, fixed-parameter, and probabilistic "
    "formulations; the right inset compares peak-hour interval widths across the four "
    "methods."
)

# -- New text for the case-study setup paragraph: drops the topology reference
#    (the IEEE 33-bus topology figure is no longer in the paper) and renumbers Fig. 2 -> Fig. 1.
NEW_CASE_SETUP = (
    "The proposed model is evaluated on a modified IEEE 33-bus distribution system in "
    "which four tie lines have been added so that the network supports both radial and "
    "meshed operation. The system base voltage is 12.66 kV and the base power is 10 MVA. "
    "The DR resource is attached at node 30, where the base load profile is a "
    "synthesised residential daily curve that captures the morning shoulder around "
    "07:00-09:00, a midday plateau driven by air-conditioning in summer, a sharp "
    "evening peak with asymmetric ramp-on/ramp-off, and a small post-peak rebound; the "
    "summer peak demand is approximately 0.85 MW. Three typical-day scenarios are "
    "defined to represent summer peak, winter peak, and shoulder-season conditions, "
    "each with its own base load profile, reference tariff curve, and "
    "participation/tariff bounds. The annual day-count weights are 90, 90, and 185, "
    "respectively. The single-period magnitude cap is set to 30 percent of the base load "
    "and the cycle-energy tolerance is 5 percent of the cumulative absolute response. "
    "The Latin Hypercube sample size [14] is N = 2000, and the participation rate "
    "within [tau_min, tau_max] is drawn from a Beta(2, 2) shape so that few households "
    "sit at the extremes of the interval; the cross-elasticity matrix uses a "
    "forward-asymmetric exponential decay that models the real-world tendency of "
    "households to defer load rather than to pre-empt it."
)

# -- Inline figure-reference renumbering (applied to every paragraph)
INLINE_TEXT_REPLACEMENTS = [
    # the topology figure is gone, so Fig 2/3/4 become Fig 1/2/3 throughout
    ("Figure 2", "Figure 1"),
    ("Fig. 2",  "Fig. 1"),
    ("Fig 2",   "Fig 1"),
    ("Figure 3", "Figure 2"),
    ("Fig. 3",  "Fig. 2"),
    ("Fig 3",   "Fig 2"),
    ("Figure 4", "Figure 3"),
    ("Fig. 4",  "Fig. 3"),
    ("Fig 4",   "Fig 3"),
]

# -- Targeted fixes for the 6 review issues identified in the final read-through
TARGETED_TEXT_FIXES = [
    # Issue 1: Section IV-B examined the two design dials -- wrong, that was IV-C (Sensitivity Analysis)
    ("Section IV-B examined the two design dials",
     "Section IV-C examined the two design dials"),

    # Issue 4: at the start of a sentence in the heat-map paragraph, IEEE style
    # uses the spelled-out "Figure" -- match the [101] "Figure 1 illustrates" style.
    # By the time this fix runs, INLINE_TEXT_REPLACEMENTS has already renumbered
    # Fig. 4 -> Fig. 3, so we anchor on the post-renumbering text.
    ("Fig. 3 shows the resulting heat map",
     "Figure 3 shows the resulting heat map"),

    # Issue 6: "hosting capacity of distributed renewables" is an awkward
    # construction (hosting capacity is a property of the network)
    ("improves the hosting capacity of distributed renewables",
     "improves the network's hosting capacity for distributed renewables"),
]

# -- Issue 5: replace Latin transliterations of Greek letters with the real
# symbol, with word boundaries so we never touch words like "beta" inside
# "Beta(2,2)" (capital B) or "plateau"/"status"/etc.
import re as _re

GREEK_REPLACEMENTS_RE = [
    # Specific multi-character patterns first (so they win over the catch-alls)
    (_re.compile(r'\[tau_min, tau_max\]'), '[τmin, τmax]'),
    (_re.compile(r'\btau_min\b'),          'τmin'),
    (_re.compile(r'\btau_max\b'),          'τmax'),
    (_re.compile(r'\btau in \['),          'τ ∈ ['),     # set membership notation
    (_re.compile(r'\btau\b'),              'τ'),
    (_re.compile(r'\beta \(peak\)'),       'η (peak)'),
    (_re.compile(r'\beta \(off-peak\)'),   'η (off-peak)'),
    (_re.compile(r'\beta\(t\)'),           'η(t)'),
    (_re.compile(r'\blow-eta\b'),          'low-η'),
    (_re.compile(r'\beta\s*=\s*'),         'η = '),       # eta = 0.25 etc.
    (_re.compile(r'\beta\b'),              'η'),
]


def get_paragraph_text(p_elem) -> str:
    return "".join((t.text or "") for t in p_elem.iter(NS_W + "t"))


def set_paragraph_text(p_elem, new_text: str):
    """Wipe runs and write a single run carrying the run properties of the first existing run."""
    existing_runs = list(p_elem.findall(NS_W + "r"))
    rpr_template = None
    if existing_runs:
        rpr_template = existing_runs[0].find(NS_W + "rPr")
    for r in existing_runs:
        p_elem.remove(r)
    new_r = ET.SubElement(p_elem, NS_W + "r")
    if rpr_template is not None:
        new_r.append(copy.deepcopy(rpr_template))
    new_t = ET.SubElement(new_r, NS_W + "t")
    new_t.text = new_text
    new_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def main():
    shutil.copy(SRC_DOCX, OUT_DOCX)

    with zipfile.ZipFile(OUT_DOCX, "r") as zin:
        files = {n: zin.read(n) for n in zin.namelist()}

    document_xml = files["word/document.xml"].decode("utf-8")
    root = ET.fromstring(document_xml)
    body = root.find(NS_W + "body")
    children = list(body)

    n_changes = {"rewrites": 0, "deletions": 0}

    # --- (1) Rewrite paragraph [32]: "Table I summarises ..." ---
    for ch in children:
        if ch.tag == NS_W + "p":
            if get_paragraph_text(ch).startswith("Table I summarises"):
                set_paragraph_text(ch, NEW_PARA_32)
                n_changes["rewrites"] += 1
                break
    else:
        print("[warn] could not find Table-I-intro paragraph")

    # --- (2) Fix the figure caption (renumbered to Fig. 1: envelopes) ---
    for ch in children:
        if ch.tag == NS_W + "p":
            text = get_paragraph_text(ch)
            if text.startswith("Comparison of 24-hour DR response interval envelopes"):
                set_paragraph_text(ch, NEW_FIG1_CAPTION)
                n_changes["rewrites"] += 1
                break
    else:
        print("[warn] could not find envelopes-figure caption paragraph")

    # --- (2b) Rewrite the case-study setup paragraph to drop the missing topology figure ---
    for ch in children:
        if ch.tag == NS_W + "p":
            text = get_paragraph_text(ch)
            if text.startswith("The proposed model is evaluated on a modified IEEE 33-bus"):
                set_paragraph_text(ch, NEW_CASE_SETUP)
                n_changes["rewrites"] += 1
                break
    else:
        print("[warn] could not find case-study setup paragraph")

    # --- (3) Delete Table I: caption paragraph + the <w:tbl> element ---
    to_delete = []
    for i, ch in enumerate(children):
        if ch.tag == NS_W + "p":
            if get_paragraph_text(ch).strip() == "Comparison of DR Uncertainty Modeling Approaches":
                to_delete.append(ch)
                # the table itself should be the very next sibling
                if i + 1 < len(children) and children[i + 1].tag == NS_W + "tbl":
                    to_delete.append(children[i + 1])
                # plus the trailing empty paragraph if present, to avoid a stray blank line
                if i + 2 < len(children):
                    nxt = children[i + 2]
                    if nxt.tag == NS_W + "p" and not get_paragraph_text(nxt).strip():
                        to_delete.append(nxt)
                break

    for elem in to_delete:
        body.remove(elem)
        n_changes["deletions"] += 1

    if n_changes["deletions"] == 0:
        print("[warn] Table I not found / not deleted")

    # --- (4) Inline figure-reference renumbering (Fig 2/3/4 -> Fig 1/2/3) ---
    n_changes["renumbered"] = 0
    for p in body.iter(NS_W + "p"):
        text = get_paragraph_text(p)
        if not text:
            continue
        new_text = text
        for old, new in INLINE_TEXT_REPLACEMENTS:
            new_text = new_text.replace(old, new)
        if new_text != text:
            set_paragraph_text(p, new_text)
            n_changes["renumbered"] += 1

    # --- (5) Issue 2: rewrite the Table II descriptor paragraph ---
    # "tightest in the shoulder season" was misleading because Winter and
    # Shoulder both have a width-0.20 participation interval; only the values
    # are lower in Shoulder. Restate as "sit lowest".
    n_changes["issue2"] = 0
    for p in body.iter(NS_W + "p"):
        text = get_paragraph_text(p)
        if "tightest in the shoulder season" in text:
            new = text.replace(
                "The participation bounds are tightest in the shoulder season, "
                "where users have lower incentives to respond, and widest in the summer",
                "The participation bounds sit lowest in the shoulder season, "
                "where users have lower incentives to respond, and are widest in the summer",
            )
            if new != text:
                set_paragraph_text(p, new)
                n_changes["issue2"] += 1
            break

    # --- (6) Issue 6 + Issue 1 + Issue 4 (targeted text fixes) ---
    n_changes["targeted"] = 0
    for old, new in TARGETED_TEXT_FIXES:
        for p in body.iter(NS_W + "p"):
            text = get_paragraph_text(p)
            if old in text:
                set_paragraph_text(p, text.replace(old, new))
                n_changes["targeted"] += 1
                break

    # --- (7) Issue 5: Latin "tau" / "eta" -> Greek "τ" / "η" ---
    n_changes["greek"] = 0
    for p in body.iter(NS_W + "p"):
        text = get_paragraph_text(p)
        if not text:
            continue
        new_text = text
        for pat, repl in GREEK_REPLACEMENTS_RE:
            new_text = pat.sub(repl, new_text)
        if new_text != text:
            set_paragraph_text(p, new_text)
            n_changes["greek"] += 1

    # --- (8) Issue 3: terminal period on reference [15] ---
    n_changes["ref_dot"] = 0
    for p in body.iter(NS_W + "p"):
        text = get_paragraph_text(p)
        # match by the distinctive end of Bertsimas & Sim entry, then ensure trailing "."
        if 'D. Bertsimas and M. Sim' in text and "The price of robustness" in text:
            if text.rstrip().endswith("2004"):
                new = text.rstrip() + "."
                set_paragraph_text(p, new)
                n_changes["ref_dot"] += 1
            break

    # --- Serialize back ---
    new_xml = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(root, encoding="utf-8")
    files["word/document.xml"] = new_xml

    with zipfile.ZipFile(OUT_DOCX, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, payload in files.items():
            zout.writestr(name, payload)

    print(f"[info] paragraph rewrites:           {n_changes['rewrites']}")
    print(f"[info] elements deleted:             {n_changes['deletions']}")
    print(f"[info] paragraphs with renumbering:  {n_changes['renumbered']}")
    print(f"[info] Issue 2 fixes:                {n_changes['issue2']}")
    print(f"[info] targeted text fixes (1,4,6):  {n_changes['targeted']}")
    print(f"[info] Greek-letter replacements:    {n_changes['greek']}")
    print(f"[info] Issue 3 ref-period fixes:     {n_changes['ref_dot']}")
    print(f"[ok] wrote {OUT_DOCX} ({OUT_DOCX.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
