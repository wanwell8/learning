"""Update the conference paper docx with the new simulation numbers.

Reads the original docx, modifies document.xml in-place via paragraph-level
text replacements that are anchored on surrounding context (so we don't
accidentally rewrite the wrong cell), and writes a new docx alongside.
"""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DOCX = Path("/root/.claude/uploads/e690f3a5-97d7-4844-b712-9d7233403758/a3960cf8-MultiDriver_DR_Interval_Modeling_Conference.docx")

# Paragraphs to delete from the document (identified by a unique substring).
PARAGRAPH_DELETIONS = [
    # The Fig 3 placement marker
    "[Insert Figure 3 here]",
    # The Fig 3 caption line
    "Sensitivity of the DR response interval width at the summer peak hour to participation bounds",
]
OUT_DOCX = ROOT / "paper" / "MultiDriver_DR_Interval_Modeling_Conference_revised.docx"
OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)

# Copy original then patch in-place
shutil.copy(SRC_DOCX, OUT_DOCX)

NS_W = "{http://purl.oclc.org/ooxml/wordprocessingml/main}"

# ---------------------------------------------------------------------------
# Replacements
# Each entry: (anchor_para_text, target_text_to_find_in_a_following_para, replacement)
# Anchor identifies a paragraph by its full text; "target" is then searched
# in *subsequent* paragraphs (in order) until a match is found, after which
# the cursor advances past that match.
# ---------------------------------------------------------------------------

# Table III: peak-hour widths in MW
# Original cells: Summer/0.153/0.035/0.162  Winter/0.079/0.022/0.079  Shoulder/0.010/0.004/0.010
# New           : Summer/0.197/0.027/0.232  Winter/0.095/0.013/0.098  Shoulder/0.022/0.004/0.022
SEQUENTIAL_REPLACEMENTS = [
    # ---- Table III (after caption "Peak-Hour DR Interval Width Comparison (MW)") ----
    ("Peak-Hour DR Interval Width Comparison (MW)", "0.153", "0.197"),  # Summer Proposed
    ("Peak-Hour DR Interval Width Comparison (MW)", "0.035", "0.027"),  # Summer Fixed
    ("Peak-Hour DR Interval Width Comparison (MW)", "0.162", "0.232"),  # Summer Unconstr
    ("Peak-Hour DR Interval Width Comparison (MW)", "0.079", "0.095"),  # Winter Proposed
    ("Peak-Hour DR Interval Width Comparison (MW)", "0.022", "0.013"),  # Winter Fixed
    ("Peak-Hour DR Interval Width Comparison (MW)", "0.079", "0.098"),  # Winter Unconstr
    ("Peak-Hour DR Interval Width Comparison (MW)", "0.010", "0.022"),  # Shoulder Proposed
    ("Peak-Hour DR Interval Width Comparison (MW)", "0.004", "0.004"),  # Shoulder Fixed (unchanged but include for clarity)
    ("Peak-Hour DR Interval Width Comparison (MW)", "0.010", "0.022"),  # Shoulder Unconstr

    # ---- Table IV (after caption "Sensitivity of Peak-Hour Interval Width to Design Drivers") ----
    ("Sensitivity of Peak-Hour Interval Width to Design Drivers", "0.153", "0.197"),  # Baseline width
    ("Sensitivity of Peak-Hour Interval Width to Design Drivers", "0.134", "0.187"),  # tau narrower
    ("Sensitivity of Peak-Hour Interval Width to Design Drivers", "-12%", "-5%"),
    ("Sensitivity of Peak-Hour Interval Width to Design Drivers", "0.172", "0.220"),  # tau wider
    ("Sensitivity of Peak-Hour Interval Width to Design Drivers", "+12%", "+12%"),
    ("Sensitivity of Peak-Hour Interval Width to Design Drivers", "0.100", "0.116"),  # eta=0.15
    ("Sensitivity of Peak-Hour Interval Width to Design Drivers", "-35%", "-41%"),
    ("Sensitivity of Peak-Hour Interval Width to Design Drivers", "0.215", "0.310"),  # eta=0.35
    ("Sensitivity of Peak-Hour Interval Width to Design Drivers", "+41%", "+57%"),
]

# ---------------------------------------------------------------------------
# Narrative-paragraph rewrites (whole-sentence replacements anchored by a
# distinctive substring). Each entry is (locate_substring, full new paragraph
# text-list-of-fragments). We will find the paragraph that contains
# locate_substring and overwrite its runs.
# ---------------------------------------------------------------------------
PARAGRAPH_REWRITES = [
    # IV-B first observation paragraph
    (
        "the proposed interval is 0.153 MW",
        "Three observations follow from Table III. First, the proposed model produces an interval "
        "that is consistently narrower than the unconstrained baseline but visibly wider than the "
        "fixed-parameter baseline. In the summer scenario, the proposed interval is 0.197 MW, "
        "which is about 15 percent below the unconstrained 0.232 MW and roughly 7.4 times the "
        "fixed-parameter 0.027 MW. The contraction relative to the unconstrained band is the "
        "contribution of the energy conservation filter, which discards trajectories that would "
        "silently shift energy out of the cycle; the expansion relative to the fixed-parameter "
        "band is the contribution of the joint interval drivers, which recover the epistemic "
        "spread that the midpoint formulation collapses."
    ),
    # IV-B second observation (seasonal ordering)
    (
        "the gap between summer and shoulder shrinks from 0.143 MW under the proposed model",
        "Second, the seasonal ordering of the interval widths (summer wider than winter wider than "
        "shoulder) is preserved by the proposed model. The ordering follows directly from the "
        "participation and tariff bounds in Table II, and it matches the operational intuition "
        "that DR flexibility is largest when peak-valley contrasts are sharpest. The fixed-parameter "
        "baseline preserves the ordering but compresses it: the gap between summer and shoulder "
        "shrinks from 0.175 MW under the proposed model to 0.023 MW under the fixed-parameter "
        "model, masking much of the seasonal differentiation that downstream scheduling could exploit."
    ),
    # IV-B third observation (rejection rates)
    (
        "approximately 80 percent of the Latin Hypercube samples are discarded",
        "Third, the rejection rate of the energy conservation filter is monitored across the three "
        "scenarios. In the summer scenario, approximately 62 percent of the Latin Hypercube samples "
        "are discarded for violating the cycle-energy tolerance; the rate drops to 46 percent in "
        "winter and to nearly zero in the shoulder season. The rate is moderate in all three cases, "
        "suggesting that the bounds in Table II are physically plausible and that the filter "
        "actively reshapes the band without dominating the sampling."
    ),
    # Sensitivity narrative paragraph
    (
        "The interval width at the summer peak hour is taken as the baseline",
        "The interval width at the summer peak hour is taken as the baseline (0.197 MW). The "
        "participation bounds and the tariff fluctuation coefficient at the peak hour are then "
        "varied one at a time around this baseline; the results are summarised in Table IV. The "
        "two design dials produce responses of different magnitudes: narrowing the participation "
        "interval from [0.40, 0.70] to [0.50, 0.60] contracts the band by 5 percent, while widening "
        "it to [0.30, 0.80] expands the band by 12 percent. Reducing the peak tariff fluctuation "
        "coefficient from 0.25 to 0.15 contracts the band by 41 percent; raising it to 0.35 "
        "expands it by 57 percent. The response is close to linear in both drivers within these "
        "ranges, which is consistent with the bilinear structure of the underlying elasticity "
        "formulation, while the tariff coefficient acts as the more powerful lever because it "
        "scales the per-unit price deviation directly."
    ),
    # IV-C probabilistic baseline result
    (
        "probabilistic baseline yields an envelope of 0.110 MW",
        "The probabilistic baseline yields an envelope of 0.063 MW, which sits between the "
        "proposed interval (0.197 MW) and the fixed-parameter baseline (0.027 MW). The contrast "
        "is informative. The probabilistic baseline produces a tighter envelope because the "
        "percentile cut-off discards the tails by construction, even though those tails correspond "
        "to physically admissible responses under the chosen distributions. The proposed interval "
        "retains the tails as long as they pass the magnitude and energy conservation filters, "
        "and is therefore more conservative by design. Whether this conservatism is desirable "
        "depends on the downstream use case: robust scheduling and worst-case studies favour the "
        "proposed interval, while expected-value studies and stochastic optimisation are better "
        "served by the probabilistic baseline."
    ),
    # IV-D convergence
    (
        "The width settles to within 9 percent",
        "The envelope is decided by extreme samples and is therefore more sensitive to sample "
        "size than mean-statistics estimators. To assess convergence, the sample size N is "
        "increased geometrically from 50 to 5000 with the summer typical-day parameters, and "
        "the resulting interval width at the peak hour is recorded across eight random seeds. "
        "The width settles to within 11 percent of its N = 5000 reference value once N reaches "
        "2000, and to within 20 percent once N reaches 500. The N = 2000 setting used elsewhere "
        "in this case study is therefore a reasonable compromise between fidelity and runtime."
    ),
    # IV-D rejection sentence (mirror of earlier change)
    (
        "Across the three typical-day scenarios, the rate stays in a moderate band: it is 80 percent",
        "The rejection rate of the energy conservation filter is also informative. Across the "
        "three typical-day scenarios, the rate stays in a moderate band: it is 62 percent for "
        "the summer scenario, 46 percent for winter, and near zero for the shoulder season. The "
        "rate would rise sharply if the participation or tariff bounds were widened beyond their "
        "physically plausible ranges, providing a useful diagnostic: a rejection rate above "
        "roughly one quarter of the samples in a low-eta scenario is a signal that the chosen "
        "bounds are inconsistent with the base load profile and should be revisited."
    ),
    # Post-Table-IV "interchangeable roles" paragraph -- updated to reflect
    # that tariff is now clearly the dominant lever in the new sensitivity sweep.
    (
        "play interchangeable roles as design dials",
        "The participation rate and the tariff coefficient therefore act as complementary but "
        "unequal design dials. From a system operator's perspective, narrowing the participation "
        "interval by improving forecast quality contracts the response band by only about a third "
        "as much as narrowing the tariff fluctuation coefficient by the same proportion through "
        "tighter day-ahead price discovery. Reporting the two sensitivities side by side helps "
        "quantify which lever is cheaper to actuate in a given regulatory environment, and the "
        "ratio suggests that, when both levers are accessible, tightening the tariff band offers "
        "the larger marginal reduction per unit of administrative cost."
    ),
    # Conclusion paragraph
    (
        "contracts the raw unconstrained band by roughly 5 percent",
        "This paper has presented a multi-driver interval model for price-based demand response "
        "in active distribution networks. By treating the user participation rate and the "
        "real-time tariff as joint interval inputs and by filtering the resulting candidate "
        "responses through a single-period magnitude limit and a whole-cycle energy conservation "
        "requirement, the model produces a response band that is physically consistent and "
        "scenario-aware. The typical-day partition exposes the band as a function of "
        "season-specific bounds rather than as a static year-long quantity, so that the band can "
        "be tuned by adjusting policy-side or market-side drivers independently. A case study on "
        "a modified IEEE 33-bus system shows that the proposed interval contracts the raw "
        "unconstrained band by roughly 15 percent while expanding the fixed-parameter band by a "
        "factor of about seven, preserves the seasonal ordering of the response amplitudes, and "
        "exhibits an approximately linear response to either of the two design dials within the "
        "studied ranges, with the tariff fluctuation coefficient acting as the dominant lever."
    ),
    # Fig 3 caption (was Fig 4) -- figure is now single panel, drop the (left)/(right)
    (
        "Sampling convergence: peak-hour interval width as a function of Latin Hypercube sample size N (left)",
        "Sample-size convergence of the peak-hour DR response interval width for the Summer "
        "typical day: mean across eight random seeds (solid line), inter-quartile spread "
        "(dark band), and full min-max envelope (light band), as a function of the Latin "
        "Hypercube sample size N."
    ),
    # Case study setup -- mention realistic synthesised inputs
    (
        "the base load profile is a typical residential daily curve with a peak demand of approximately 0.85 MW",
        "The proposed model is evaluated on a modified IEEE 33-bus distribution system in which "
        "four tie lines have been added so that the network supports both radial and meshed "
        "operation. The system base voltage is 12.66 kV and the base power is 10 MVA. Fig. 1 "
        "shows the topology of the test system; the DR resource is attached at node 30, where "
        "the base load profile is a synthesised residential daily curve that captures the "
        "morning shoulder around 07:00-09:00, a midday plateau driven by air-conditioning in "
        "summer, a sharp evening peak with asymmetric ramp-on/ramp-off, and a small post-peak "
        "rebound; the summer peak demand is approximately 0.85 MW. Three typical-day scenarios "
        "are defined to represent summer peak, winter peak, and shoulder-season conditions, "
        "each with its own base load profile, reference tariff curve, and participation/tariff "
        "bounds. The annual day-count weights are 90, 90, and 185, respectively. The "
        "single-period magnitude cap is set to 30 percent of the base load and the cycle-energy "
        "tolerance is 5 percent of the cumulative absolute response. The Latin Hypercube sample "
        "size [14] is N = 2000, and the participation rate within [tau_min, tau_max] is drawn "
        "from a Beta(2, 2) shape so that few households sit at the extremes of the interval; "
        "the cross-elasticity matrix uses a forward-asymmetric exponential decay that models the "
        "real-world tendency of households to defer load rather than to pre-empt it."
    ),
]

# ---------------------------------------------------------------------------
# Plain text-in-paragraph substitutions (no paragraph rewrite, no anchor)
# ---------------------------------------------------------------------------
GLOBAL_TEXT_REPLACEMENTS = [
    # Renumber: convergence figure was [Insert Figure 4 here] -> now Figure 3
    ("[Insert Figure 4 here]", "[Insert Figure 3 here]"),
]

# ---------------------------------------------------------------------------
# Content to append before the "Conclusion" heading
#   Renamed plan:
#       Fig. 3 = sample-size convergence (was Fig. 4)
#       Fig. 4 = design-dial heat map   (was Fig. 5, new in paper)
#   The block below is the new IV.E subsection that introduces Fig. 4.
# ---------------------------------------------------------------------------
NEW_SUBSECTION_BLOCK = [
    ("heading2", "Design-Dial Surface as a Lookup Chart"),
    ("body",
     "Section IV-B examined the two design dials -- participation interval and tariff "
     "fluctuation coefficient -- one at a time. To turn those findings into an operational "
     "tool, the peak-hour interval width is now plotted as a two-dimensional surface in "
     "(participation-interval width, peak-period tariff fluctuation) space. For each grid "
     "point the proposed method is rerun with the Summer-typical-day base load and tariff "
     "structure, and the resulting peak-hour interval width is recorded. The surface "
     "therefore represents what an operator would observe if both bounds were dialled "
     "jointly, including any coupling that the one-at-a-time view cannot capture."),
    ("body",
     "Fig. 4 shows the resulting heat map together with five iso-width contour curves at "
     "100, 150, 200, 250, and 300 kW. Two observations stand out. First, the contours are "
     "almost horizontal at low values of eta and bend upward at high values, which provides "
     "a graphical confirmation of the sensitivity ranking in Table IV: the tariff "
     "fluctuation coefficient is the dominant driver, and the participation rate becomes a "
     "relevant lever only after eta is already large. Second, the three labelled circles "
     "show where the Summer, Winter, and Shoulder operating points sit on the surface; "
     "their vertical separation is much larger than their horizontal separation, again "
     "reflecting the eta-dominated structure. The surface is therefore usable as a design "
     "lookup chart: for any target interval width, the corresponding contour traces the "
     "locus of (tau-width, eta) pairs that achieve it, and the operator can pick the pair "
     "that is cheapest to actuate in the local regulatory environment."),
    ("placeholder", "[Insert Figure 4 here]"),
    ("caption",
     "Peak-hour interval width (kW) at the Summer typical-day peak hour as a joint "
     "function of the participation-interval width and the peak-period tariff fluctuation "
     "coefficient eta; iso-width contours overlaid and the three typical-day operating "
     "points marked."),
]


# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------
def get_paragraph_text(p_elem) -> str:
    out = ""
    for t in p_elem.iter(NS_W + "t"):
        if t.text:
            out += t.text
    return out


def set_paragraph_text(p_elem, new_text: str):
    """Replace all text in a paragraph by clearing existing runs and adding a new one."""
    # Find any existing run to copy run properties from
    existing_runs = list(p_elem.findall(NS_W + "r"))
    rpr_template = None
    if existing_runs:
        rpr_template = existing_runs[0].find(NS_W + "rPr")

    # Remove all existing runs
    for r in existing_runs:
        p_elem.remove(r)

    # Add a fresh run with the new text
    import xml.etree.ElementTree as ET
    new_r = ET.SubElement(p_elem, NS_W + "r")
    if rpr_template is not None:
        # Copy run properties by deep-copy via ET
        import copy
        new_r.append(copy.deepcopy(rpr_template))
    new_t = ET.SubElement(new_r, NS_W + "t")
    new_t.text = new_text
    new_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def replace_in_paragraph_keep_runs(p_elem, old: str, new: str) -> bool:
    """If `old` appears inside the joined text of p_elem, replace it.
    Falls back to wiping runs if the match crosses run boundaries.
    Returns True on success.
    """
    runs = list(p_elem.iter(NS_W + "t"))
    joined = "".join(t.text or "" for t in runs)
    if old not in joined:
        return False
    new_joined = joined.replace(old, new, 1)
    # If it's a small cell with a single run, just set the run's text
    if len(runs) == 1:
        runs[0].text = new_joined
        runs[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return True
    # Multi-run: replace via the wipe-and-rewrite path
    set_paragraph_text(p_elem, new_joined)
    return True


def main():
    import xml.etree.ElementTree as ET
    # Register namespaces so output keeps prefixes
    ET.register_namespace("w", "http://purl.oclc.org/ooxml/wordprocessingml/main")

    with zipfile.ZipFile(OUT_DOCX, "r") as zin:
        names = zin.namelist()
        data = {n: zin.read(n) for n in names}

    document_xml = data["word/document.xml"].decode("utf-8")
    # ElementTree parsing -- need to re-register all namespaces to avoid losing prefixes
    # Parse the full doc preserving namespaces by using fromstring + ElementTree
    # but ET will rename namespaces unless registered.
    # Simpler: re-register all namespaces we see in root attrib
    import re as _re
    for m in _re.finditer(r'xmlns:([a-zA-Z0-9]+)="([^"]+)"', document_xml[:5000]):
        ET.register_namespace(m.group(1), m.group(2))

    root = ET.fromstring(document_xml)
    body = root.find(NS_W + "body")
    paragraphs = list(body.iter(NS_W + "p"))

    print(f"[info] {len(paragraphs)} paragraphs found")

    # --- Apply paragraph-level full rewrites first (they need unique anchors) ---
    rewrite_count = 0
    for locate, new_full in PARAGRAPH_REWRITES:
        hit = False
        for p in paragraphs:
            text = get_paragraph_text(p)
            if locate in text:
                set_paragraph_text(p, new_full)
                rewrite_count += 1
                hit = True
                break
        if not hit:
            print(f"[warn] full-rewrite anchor not found: {locate[:60]}...")
    print(f"[info] {rewrite_count}/{len(PARAGRAPH_REWRITES)} paragraph rewrites applied")

    # --- Apply sequential table-cell replacements ---
    # group by anchor: scan paragraphs in order, find anchor, then find each "old" in
    # the following paragraphs in sequence, replacing only the first occurrence per item.
    grouped: dict[str, list[tuple[str, str]]] = {}
    order: list[str] = []
    for anchor, old, new in SEQUENTIAL_REPLACEMENTS:
        if anchor not in grouped:
            grouped[anchor] = []
            order.append(anchor)
        grouped[anchor].append((old, new))

    seq_count = 0
    for anchor in order:
        # find anchor paragraph index
        anchor_idx = None
        for i, p in enumerate(paragraphs):
            text = get_paragraph_text(p)
            if anchor in text:
                anchor_idx = i
                break
        if anchor_idx is None:
            print(f"[warn] sequential anchor not found: {anchor}")
            continue

        cursor = anchor_idx + 1
        for old, new in grouped[anchor]:
            done = False
            while cursor < len(paragraphs):
                text = get_paragraph_text(paragraphs[cursor])
                if old in text:
                    if replace_in_paragraph_keep_runs(paragraphs[cursor], old, new):
                        seq_count += 1
                        done = True
                        cursor += 1
                        break
                cursor += 1
            if not done:
                print(f"[warn] sequential value not found after {anchor[:40]}...: {old}")

    print(f"[info] {seq_count}/{len(SEQUENTIAL_REPLACEMENTS)} sequential replacements applied")

    # --- Apply paragraph deletions ---
    # Build a child -> parent map so we can remove paragraphs at any nesting depth.
    parent_of = {child: parent for parent in root.iter() for child in parent}
    del_count = 0
    for locate in PARAGRAPH_DELETIONS:
        target = None
        for p in root.iter(NS_W + "p"):
            text = get_paragraph_text(p)
            if locate in text:
                target = p
                break
        if target is None:
            print(f"[warn] deletion anchor not found: {locate[:60]}...")
            continue
        parent = parent_of.get(target)
        if parent is None:
            print(f"[warn] could not find parent for: {locate[:60]}...")
            continue
        parent.remove(target)
        del_count += 1
    print(f"[info] {del_count}/{len(PARAGRAPH_DELETIONS)} paragraph deletions applied")

    # --- Apply global text replacements (any number of hits, all paragraphs) ---
    glob_count = 0
    for old, new in GLOBAL_TEXT_REPLACEMENTS:
        for p in root.iter(NS_W + "p"):
            text = get_paragraph_text(p)
            if old in text:
                if replace_in_paragraph_keep_runs(p, old, new):
                    glob_count += 1
    print(f"[info] {glob_count} global text replacement(s) applied")

    # --- Insert the new IV.E subsection just before the "Conclusion" heading ---
    # locate Conclusion paragraph (exact short text)
    import copy as _copy
    parent_of = {child: parent for parent in root.iter() for child in parent}
    conclusion_p = None
    for p in root.iter(NS_W + "p"):
        text = get_paragraph_text(p).strip()
        if text == "Conclusion":
            conclusion_p = p
            break
    if conclusion_p is None:
        print("[warn] could not find Conclusion heading; new subsection not inserted")
    else:
        conclusion_parent = parent_of[conclusion_p]
        # find the index of Conclusion within its parent
        siblings = list(conclusion_parent)
        cidx = siblings.index(conclusion_p)

        # Collect template paragraphs to clone for each style we need:
        #   heading2  -> use the existing "Sampling Convergence and Rejection Behaviour" heading
        #   body      -> use the body-text paragraph right after that heading
        #   placeholder -> use the existing "[Insert Figure 3 here]" paragraph (just renumbered)
        #   caption   -> use the existing convergence figure caption paragraph
        templates = {}
        for p in root.iter(NS_W + "p"):
            t = get_paragraph_text(p).strip()
            if t == "Sampling Convergence and Rejection Behaviour" and "heading2" not in templates:
                templates["heading2"] = p
            elif t == "[Insert Figure 3 here]" and "placeholder" not in templates:
                templates["placeholder"] = p
            elif t.startswith("Sample-size convergence of the peak-hour DR response") and "caption" not in templates:
                templates["caption"] = p

        # find a generic body paragraph: the rewritten convergence narrative starts with
        # "The envelope is decided by extreme samples"
        for p in root.iter(NS_W + "p"):
            t = get_paragraph_text(p)
            if t.startswith("The envelope is decided by extreme samples"):
                templates["body"] = p
                break

        missing = [k for k in ("heading2", "body", "placeholder", "caption") if k not in templates]
        if missing:
            print(f"[warn] missing templates for: {missing}; new subsection not inserted")
        else:
            inserted = 0
            for kind, text in NEW_SUBSECTION_BLOCK:
                tmpl = templates[kind]
                new_p = _copy.deepcopy(tmpl)
                set_paragraph_text(new_p, text)
                conclusion_parent.insert(cidx, new_p)
                cidx += 1
                inserted += 1
            print(f"[info] inserted {inserted} new paragraphs before Conclusion")

    # --- Serialize back ---
    new_xml = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(root, encoding="utf-8")
    data["word/document.xml"] = new_xml

    # Write zip
    with zipfile.ZipFile(OUT_DOCX, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, payload in data.items():
            zout.writestr(name, payload)

    print(f"[ok] wrote {OUT_DOCX}")
    print(f"     size: {OUT_DOCX.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
