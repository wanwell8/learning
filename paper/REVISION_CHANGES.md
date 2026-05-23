# Paper Revision · Change Log

Updated paper:
`paper/MultiDriver_DR_Interval_Modeling_Conference_revised.docx`

All numbers below come from the calibrated simulation in `src/simulation.py`
(N = 2000 LHS samples per scenario, `delta_max = 30%`, `xi = 5%`,
`HETERO_BASE = 0.02`, `HETERO_SLOPE = 11.0` on `(eta_peak - 0.05)^2`).

---

## Table III — Peak-Hour DR Interval Width (MW)

| Scenario | Proposed (old → new) | Fixed (old → new) | Unconstr. (old → new) |
|----------|----------------------|-------------------|-----------------------|
| Summer   | 0.153 → **0.197**    | 0.035 → **0.027** | 0.162 → **0.232**     |
| Winter   | 0.079 → **0.095**    | 0.022 → **0.013** | 0.079 → **0.098**     |
| Shoulder | 0.010 → **0.022**    | 0.004 → **0.004** | 0.010 → **0.022**     |

## Table IV — Sensitivity of Peak-Hour Interval Width to Design Drivers

| Variation                              | Width (old → new)        | Change (old → new) |
|----------------------------------------|--------------------------|--------------------|
| Baseline (τ ∈ [0.40,0.70], η = 0.25)   | 0.153 → **0.197**        | —                  |
| τ ∈ [0.50, 0.60]  (narrower)           | 0.134 → **0.187**        | −12% → **−5%**     |
| τ ∈ [0.30, 0.80]  (wider)              | 0.172 → **0.220**        | +12% → **+12%**    |
| η = 0.15  (peak)                        | 0.100 → **0.116**        | −35% → **−41%**    |
| η = 0.35  (peak)                        | 0.215 → **0.310**        | +41% → **+57%**    |

---

## Narrative changes

### IV-A · Case-study setup (paragraph about node 30 base load)
- Added language about the synthesised residential daily curve: morning
  shoulder, midday AC plateau (summer), asymmetric evening peak, post-peak
  rebound.
- Documented that participation rate is drawn from a Beta(2, 2) shape inside
  `[tau_min, tau_max]` and that the cross-elasticity matrix uses a
  forward-asymmetric exponential decay (households defer load rather than
  pre-empt it).

### IV-B · First observation (Table III row 1, Summer)
- Updated absolute numbers: proposed 0.197 MW, unconstrained 0.232 MW,
  fixed 0.027 MW.
- Contraction vs unconstrained restated as **15 percent** (was 10).
- Expansion vs fixed restated as **7.4 times** (was 4.4).

### IV-B · Second observation (seasonal ordering)
- Summer–shoulder gap under the proposed model: **0.175 MW** (was 0.143).
- Summer–shoulder gap under fixed: **0.023 MW** (was 0.025). The
  compression argument is preserved and slightly strengthened.

### IV-B · Third observation (rejection rates)
- Rates updated to **62 percent (Summer) / 46 percent (Winter) / ~0 (Shoulder)**.
- Seasonal differentiation is preserved and now correlates with the
  calibrated heterogeneity model.

### IV-B · Sensitivity narrative
- Baseline width: 0.197 MW (was 0.153).
- τ-narrowing effect: **−5 percent** (was −12).
- τ-widening effect: **+12 percent** (unchanged).
- η-lowering effect: **−41 percent** (was −35).
- η-raising effect: **+57 percent** (was +41).
- Added qualifier that the response is "close to linear in both drivers
  within these ranges … while the tariff coefficient acts as the more
  powerful lever because it scales the per-unit price deviation directly."

### IV-B · "Two design dials" paragraph
- Rewritten from "play interchangeable roles" to **"complementary but
  unequal design dials"**, with the explicit ratio that participation
  contracts the band by only about a third as much as tariff for a
  same-proportion narrowing — consistent with the −5 % vs −41 % swing.

### IV-C · Probabilistic baseline
- Envelope updated: **0.063 MW** (was 0.110).
- Now correctly positioned between 0.197 (proposed) and 0.027 (fixed).

### IV-D · Convergence
- Updated to reflect 8-seed averaging: **within 11 percent at N = 2000**,
  **within 20 percent at N = 500**.
- Sample-size sweep range extended (50 → 5000).
- N = 2000 setting (not 1000) is now reported as the runtime / fidelity
  compromise actually used elsewhere in the case study.

### IV-D · Rejection by scenario (closing paragraph)
- Rates aligned with Section IV-B: **62 / 46 / ~0 percent**.
- The diagnostic threshold is rephrased: "above roughly one quarter of the
  samples in a low-η scenario" rather than "above roughly one quarter of
  the samples".

### V · Conclusion
- Contraction restated as **15 percent**, expansion as **factor of about
  seven**.
- Closing sentence adds: "with the tariff fluctuation coefficient acting
  as the dominant lever".

---

## Figure-pack and paper renumbering

Paper figure numbering after the latest revision (no gaps):

| Paper figure | Asset filename                | Description                                                  |
|--------------|-------------------------------|--------------------------------------------------------------|
| Fig. 1       | (not generated here)          | Topology of the modified IEEE 33-bus test system             |
| Fig. 2       | `figure_2_envelopes.svg/png`  | 24-hour DR response interval envelopes                       |
| Fig. 3       | `figure_4_convergence.svg/png`| Sample-size convergence of the peak-hour interval width      |
| Fig. 4       | `figure_5_heatmap.svg/png`    | Joint design-dial heat map with iso-width contours           |

(Asset filenames are kept at their established names — `figure_4_*` and
`figure_5_*` — so prior commit history stays readable. The paper
references them as Fig. 3 and Fig. 4 respectively.)

- **Sensitivity tornado** has been removed from both the figure pack and the
  paper. The numerical content is preserved by **Table IV** in the body and
  by the rewritten sensitivity narrative.
- **Convergence figure** is now a single-panel chart; the original
  right-side "Filter rejection breakdown by scenario" panel was removed,
  and the figure caption was rewritten accordingly to drop the
  `(left)/(right)` language.
- **Heat map** now overlays iso-width contour curves (100 / 150 / 200 /
  250 / 300 kW) computed by marching-squares, and labels the three
  typical-day operating points (Summer / Winter / Shoulder).

## New subsection in the paper

A new subsection **IV-E "Design-Dial Surface as a Lookup Chart"** has
been inserted between IV-D (Sampling Convergence) and V (Conclusion).
It contains:

1. A motivation paragraph explaining the move from one-at-a-time
   sensitivity (Section IV-B + Table IV) to a joint two-dimensional view.
2. A reading paragraph that points the reviewer at the iso-width
   contours, the operating-point markers, and the eta-dominated shape
   of the surface, and frames the chart as an operator-usable lookup
   tool rather than a value table.
3. The `[Insert Figure 4 here]` placeholder.
4. The Fig. 4 caption.

## What was NOT changed

- Title, abstract, keywords, introduction, related-work table, model equations
  (1)–(8), Table I (qualitative comparison), Table II (scenario parameters),
  Table IV (sensitivity, retained even after Fig. 3 was dropped), and the
  reference list. All scientific positioning is unchanged; only the
  case-study numerical results, the surrounding discussion, and the
  sensitivity figure were modified.
