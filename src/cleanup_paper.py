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

# -- New text for Fig. 2 caption (paragraph [77]) -- adds the probabilistic curve
NEW_FIG2_CAPTION = (
    "Comparison of 24-hour DR response interval envelopes at node 30 for the three "
    "typical days under the proposed, unconstrained, fixed-parameter, and probabilistic "
    "formulations; the right inset compares peak-hour interval widths across the four "
    "methods."
)


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

    # --- (2) Fix Fig 2 caption ---
    for ch in children:
        if ch.tag == NS_W + "p":
            text = get_paragraph_text(ch)
            if text.startswith("Comparison of 24-hour DR response interval envelopes"):
                set_paragraph_text(ch, NEW_FIG2_CAPTION)
                n_changes["rewrites"] += 1
                break
    else:
        print("[warn] could not find Fig 2 caption paragraph")

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

    # --- Serialize back ---
    new_xml = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(root, encoding="utf-8")
    files["word/document.xml"] = new_xml

    with zipfile.ZipFile(OUT_DOCX, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, payload in files.items():
            zout.writestr(name, payload)

    print(f"[info] paragraph rewrites: {n_changes['rewrites']}")
    print(f"[info] elements deleted:   {n_changes['deletions']}")
    print(f"[ok] wrote {OUT_DOCX} ({OUT_DOCX.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
