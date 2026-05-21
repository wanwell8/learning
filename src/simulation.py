"""
Multi-Driver Interval Modeling of Demand Response with Energy Conservation Constraint.

Pure-Python (stdlib only) reimplementation of the case study described in the paper.
Generates the data dumped into ../data/*.json for the SVG figure renderers.
"""

from __future__ import annotations

import json
import math
import os
import random
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

T = 24          # hours
L_WIN = 3       # cross-elasticity half-window (paper sec. III-A)
SELF_E = -0.30  # diagonal of E_DR
DECAY = math.log(4.0) / L_WIN  # so that the farthest period is ~1/4 of the immediate neighbour
DELTA_MAX = 0.30
XI_TOL = 0.05


# ---------------------------------------------------------------------------
# Load profiles -- shaped to a realistic residential daily curve
# ---------------------------------------------------------------------------
def _profile(peak_hour: int, peak: float, valley_frac: float = 0.35) -> list[float]:
    """Smooth profile: two gaussian bumps (morning small, evening large) + base."""
    base = peak * valley_frac
    morning_peak = peak * 0.65 if peak_hour >= 17 else peak * 0.55
    out = []
    for h in range(T):
        # evening / main peak
        main = (peak - base) * math.exp(-((h - peak_hour) ** 2) / 8.0)
        # morning shoulder around 8:00
        morn = (morning_peak - base) * math.exp(-((h - 8) ** 2) / 6.0) * 0.55
        v = base + max(main, morn)
        out.append(v)
    # rescale so max == peak
    m = max(out)
    return [v * peak / m for v in out]


def _reference_tariff(peak_hours: list[int], valley_hours: list[int]) -> list[float]:
    """Three-tier tariff: peak / shoulder / valley."""
    out = []
    for h in range(T):
        if h in peak_hours:
            out.append(1.40)
        elif h in valley_hours:
            out.append(0.55)
        else:
            out.append(1.00)
    return out


# ---------------------------------------------------------------------------
# Scenario definitions (Table II in the paper)
# ---------------------------------------------------------------------------
@dataclass
class Scenario:
    name: str
    days: int
    peak_load: float
    peak_hour: int
    tau_min: float
    tau_max: float
    eta_peak: float
    eta_off: float
    color: str
    peak_hours: list[int] = field(default_factory=list)
    valley_hours: list[int] = field(default_factory=list)

    @property
    def weight(self) -> float:
        return self.days / 365.0

    def load(self) -> list[float]:
        return _profile(self.peak_hour, self.peak_load)

    def cref(self) -> list[float]:
        return _reference_tariff(self.peak_hours, self.valley_hours)

    def eta(self) -> list[float]:
        return [self.eta_peak if h in self.peak_hours else self.eta_off for h in range(T)]


SUMMER = Scenario(
    "Summer", days=90, peak_load=0.85, peak_hour=19,
    tau_min=0.40, tau_max=0.70, eta_peak=0.25, eta_off=0.10,
    color="#d1495b",
    peak_hours=[18, 19, 20, 21],
    valley_hours=[1, 2, 3, 4, 5],
)
WINTER = Scenario(
    "Winter", days=90, peak_load=0.72, peak_hour=18,
    tau_min=0.30, tau_max=0.50, eta_peak=0.20, eta_off=0.08,
    color="#2e6f95",
    peak_hours=[17, 18, 19, 20],
    valley_hours=[1, 2, 3, 4, 5],
)
SHOULDER = Scenario(
    "Shoulder", days=185, peak_load=0.48, peak_hour=12,
    tau_min=0.20, tau_max=0.40, eta_peak=0.10, eta_off=0.05,
    color="#669973",
    peak_hours=[11, 12, 13, 19, 20],
    valley_hours=[1, 2, 3, 4, 5],
)
SCENARIOS = [SUMMER, WINTER, SHOULDER]


# ---------------------------------------------------------------------------
# Elasticity matrix  (T x T, banded, exponential decay, self-elasticity on diag)
#
# Designed so that the *load-weighted* column sums vanish:
#     sum_t  P_t * E[t,j]  =  0      for every j
# which (combined with eq. (1) ΔP = tau * diag(P) * E * r) guarantees that
# any response is a pure shift -- a single Latin-Hypercube draw is then
# close to net-zero before the energy filter is even applied, so the filter
# does its real job of trimming the *tails* rather than killing every sample.
# ---------------------------------------------------------------------------
def build_E(P: list[float], self_e: float = SELF_E, decay: float = DECAY) -> list[list[float]]:
    """Banded elasticity matrix designed for approximate load-weighted balance:
        sum_t  P_t * E[t,j]  =  0
    so that an ideal sample is nearly net-zero before the filter.
    """
    E = [[0.0] * T for _ in range(T)]
    for j in range(T):
        E[j][j] = self_e
        weights = {}
        for t in range(T):
            if t == j:
                continue
            d = min(abs(t - j), T - abs(t - j))
            if 1 <= d <= L_WIN:
                weights[t] = P[t] * math.exp(-decay * (d - 1))
        wsum = sum(weights.values()) or 1.0
        target = -self_e * P[j]
        for t, w in weights.items():
            E[t][j] = (w / wsum) * (target / P[t] if P[t] > 0 else 0.0)
    return E


# Heterogeneity in per-user response: scales each off-diagonal of E
# independently per sample, representing individual elasticity variation.
HETERO_SIGMA = 0.40


def matvec(M: list[list[float]], v: list[float]) -> list[float]:
    return [sum(M[i][j] * v[j] for j in range(len(v))) for i in range(len(M))]


# ---------------------------------------------------------------------------
# Sampling  --  Latin Hypercube on (tau, c1..cT)
# ---------------------------------------------------------------------------
def lhs(n: int, dim: int, rng: random.Random) -> list[list[float]]:
    """Standard Latin Hypercube on the unit cube, no correlation correction."""
    out = [[0.0] * dim for _ in range(n)]
    for d in range(dim):
        perm = list(range(n))
        rng.shuffle(perm)
        for s in range(n):
            out[s][d] = (perm[s] + rng.random()) / n
    return out


# ---------------------------------------------------------------------------
# Per-scenario sampling and filtering
# ---------------------------------------------------------------------------
def simulate(scn: Scenario, N: int = 2000, seed: int = 42,
             apply_energy_filter: bool = True, apply_mag_filter: bool = True,
             self_e: float = SELF_E, hetero_sigma: float = HETERO_SIGMA):
    rng = random.Random(seed)
    P = scn.load()
    cref = scn.cref()
    eta = scn.eta()
    cflat = sum(cref) / T  # flat reference for the per-unit deviation
    E_base = build_E(P, self_e=self_e)

    U = lhs(N, T + 1, rng)

    kept = []
    rejected_mag = 0
    rejected_energy = 0
    for s in range(N):
        u = U[s]
        tau = scn.tau_min + (scn.tau_max - scn.tau_min) * u[0]
        c = [cref[t] * (1 - eta[t] + 2 * eta[t] * u[t + 1]) for t in range(T)]
        r = [(c[t] - cflat) / cflat for t in range(T)]

        # per-sample elasticity heterogeneity: off-diagonals scale independently,
        # modelling user-by-user variation in cross-period substitution.
        E_local = [row[:] for row in E_base]
        for i in range(T):
            for j in range(T):
                if i != j and E_local[i][j] != 0.0:
                    E_local[i][j] *= max(0.0, 1.0 + hetero_sigma * rng.gauss(0.0, 1.0))

        dPP = matvec(E_local, r)                       # E * r
        dP = [tau * P[t] * dPP[t] for t in range(T)]

        if apply_mag_filter and any(abs(dP[t]) > DELTA_MAX * P[t] for t in range(T)):
            rejected_mag += 1
            continue
        abs_sum = sum(abs(x) for x in dP) or 1.0
        if apply_energy_filter and abs(sum(dP)) > XI_TOL * abs_sum:
            rejected_energy += 1
            continue
        kept.append(dP)

    if not kept:
        kept = [[0.0] * T]
    lower = [min(s[t] for s in kept) for t in range(T)]
    upper = [max(s[t] for s in kept) for t in range(T)]
    median = [sorted(s[t] for s in kept)[len(kept) // 2] for t in range(T)]
    return {
        "load": P,
        "cref": cref,
        "lower": lower,
        "upper": upper,
        "median": median,
        "kept": len(kept),
        "N": N,
        "rejected_mag": rejected_mag,
        "rejected_energy": rejected_energy,
    }


def fixed_baseline(scn: Scenario):
    """Single-point midpoint baseline (Table III column 'Fixed')."""
    P = scn.load()
    cref = scn.cref()
    eta = scn.eta()
    cflat = sum(cref) / T
    tau_mid = 0.5 * (scn.tau_min + scn.tau_max)
    E_local = build_E(P)

    # midpoint tariff path -- use cref exactly (eta -> 0 around reference)
    c_low = [cref[t] * (1 - eta[t]) for t in range(T)]
    c_high = [cref[t] * (1 + eta[t]) for t in range(T)]
    r_low = [(c_low[t] - cflat) / cflat for t in range(T)]
    r_high = [(c_high[t] - cflat) / cflat for t in range(T)]
    dPP_low = matvec(E_local, r_low)
    dPP_high = matvec(E_local, r_high)
    dP_low = [tau_mid * P[t] * dPP_low[t] for t in range(T)]
    dP_high = [tau_mid * P[t] * dPP_high[t] for t in range(T)]
    lower = [min(dP_low[t], dP_high[t]) for t in range(T)]
    upper = [max(dP_low[t], dP_high[t]) for t in range(T)]
    median = [0.5 * (lower[t] + upper[t]) for t in range(T)]
    return {"lower": lower, "upper": upper, "median": median, "load": P}


def probabilistic_baseline(scn: Scenario, N: int = 10000, seed: int = 7):
    """Probabilistic envelope using truncated-Gaussian + Beta draws (paper, sec. IV-C)."""
    rng = random.Random(seed)
    P = scn.load()
    cref = scn.cref()
    eta = scn.eta()
    cflat = sum(cref) / T
    mid = 0.5 * (scn.tau_min + scn.tau_max)
    half = 0.5 * (scn.tau_max - scn.tau_min)

    E_local = build_E(P)
    samples = []
    for _ in range(N):
        # Beta(2,2)-like via sum-of-uniforms then rescale to [tau_min, tau_max]
        u = 0.5 * (rng.random() + rng.random())   # mean 0.5, ~tri
        tau = scn.tau_min + (scn.tau_max - scn.tau_min) * u
        c = []
        for t in range(T):
            sigma = eta[t] * cref[t] / 3.0       # 3-sigma = eta * cref
            # truncated normal via rejection
            for _try in range(8):
                z = rng.gauss(0.0, 1.0)
                if abs(z) <= 3.0:
                    break
            c.append(cref[t] + sigma * z)
        r = [(c[t] - cflat) / cflat for t in range(T)]
        dPP = matvec(E_local, r)
        dP = [tau * P[t] * dPP[t] for t in range(T)]
        samples.append(dP)

    # 5/95 percentiles per hour
    lower = []
    upper = []
    for t in range(T):
        col = sorted(s[t] for s in samples)
        lower.append(col[int(0.05 * N)])
        upper.append(col[int(0.95 * N)])
    return {"lower": lower, "upper": upper, "median": [0.5 * (l + u) for l, u in zip(lower, upper)]}


# ---------------------------------------------------------------------------
# Main: generate all figure data
# ---------------------------------------------------------------------------
def main():
    # ----- Figure 2: 24-hour envelopes per scenario, 3 methods -----
    fig2 = {}
    for scn in SCENARIOS:
        proposed = simulate(scn, N=2000)
        unconstr = simulate(scn, N=2000, apply_energy_filter=False, apply_mag_filter=False)
        fixed = fixed_baseline(scn)
        prob = probabilistic_baseline(scn, N=8000)
        fig2[scn.name] = {
            "color": scn.color,
            "peak_hour": scn.peak_hour,
            "load": proposed["load"],
            "cref": proposed["cref"],
            "proposed": {"lower": proposed["lower"], "upper": proposed["upper"], "median": proposed["median"]},
            "unconstrained": {"lower": unconstr["lower"], "upper": unconstr["upper"], "median": unconstr["median"]},
            "fixed": {"lower": fixed["lower"], "upper": fixed["upper"], "median": fixed["median"]},
            "probabilistic": {"lower": prob["lower"], "upper": prob["upper"], "median": prob["median"]},
            "stats": {
                "kept": proposed["kept"], "N": proposed["N"],
                "rejected_mag": proposed["rejected_mag"],
                "rejected_energy": proposed["rejected_energy"],
                "rejection_rate": (proposed["N"] - proposed["kept"]) / proposed["N"],
                "peak_hour_width_proposed":     proposed["upper"][scn.peak_hour] - proposed["lower"][scn.peak_hour],
                "peak_hour_width_unconstrained": unconstr["upper"][scn.peak_hour] - unconstr["lower"][scn.peak_hour],
                "peak_hour_width_fixed":        fixed["upper"][scn.peak_hour] - fixed["lower"][scn.peak_hour],
                "peak_hour_width_probabilistic": prob["upper"][scn.peak_hour] - prob["lower"][scn.peak_hour],
            }
        }

    (DATA_DIR / "fig2_envelopes.json").write_text(json.dumps(fig2, indent=2))

    # ----- Figure 3: Sensitivity (tornado) -----
    # baseline = summer proposed
    baseline_w = fig2["Summer"]["stats"]["peak_hour_width_proposed"]
    variants = []
    for label, mods, self_e_override in [
        ("tau in [0.50, 0.60]",   {"tau_min": 0.50, "tau_max": 0.60}, SELF_E),
        ("tau in [0.30, 0.80]",   {"tau_min": 0.30, "tau_max": 0.80}, SELF_E),
        ("eta_peak = 0.15",       {"eta_peak": 0.15}, SELF_E),
        ("eta_peak = 0.35",       {"eta_peak": 0.35}, SELF_E),
        ("eta_off = 0.05",        {"eta_off": 0.05}, SELF_E),
        ("eta_off = 0.20",        {"eta_off": 0.20}, SELF_E),
        ("self-elast -0.20",      {}, -0.20),
        ("self-elast -0.40",      {}, -0.40),
    ]:
        scn_mod = Scenario(**{**SUMMER.__dict__, **mods})
        out = simulate(scn_mod, N=2000, seed=42, self_e=self_e_override)
        w = out["upper"][SUMMER.peak_hour] - out["lower"][SUMMER.peak_hour]
        variants.append({"label": label, "width": w,
                         "delta_pct": (w - baseline_w) / baseline_w * 100.0 if baseline_w else 0.0})

    (DATA_DIR / "fig3_sensitivity.json").write_text(json.dumps({
        "baseline_width": baseline_w,
        "variants": variants,
    }, indent=2))

    # ----- Figure 4: Convergence + rejection by scenario -----
    convergence = []
    Ns = [50, 100, 200, 500, 1000, 2000, 5000]
    # use multiple seeds for confidence band
    for N in Ns:
        widths = []
        for seed in range(8):
            out = simulate(SUMMER, N=N, seed=100 + seed)
            widths.append(out["upper"][SUMMER.peak_hour] - out["lower"][SUMMER.peak_hour])
        widths.sort()
        convergence.append({
            "N": N,
            "mean": sum(widths) / len(widths),
            "lo":   widths[1],
            "hi":   widths[-2],
            "min": widths[0],
            "max": widths[-1],
        })

    rejection_by_scn = []
    for scn in SCENARIOS:
        out_p = simulate(scn, N=2000, seed=42)
        rejection_by_scn.append({
            "name": scn.name,
            "color": scn.color,
            "rejected_energy": out_p["rejected_energy"],
            "rejected_mag": out_p["rejected_mag"],
            "kept": out_p["kept"],
            "N": out_p["N"],
        })

    (DATA_DIR / "fig4_convergence.json").write_text(json.dumps({
        "convergence": convergence,
        "rejection": rejection_by_scn,
    }, indent=2))

    # ----- Figure 5 (BONUS): driver heatmap -- width as a function of tau-width x eta_peak
    heat = []
    tau_widths = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
    eta_peaks  = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35]
    for ep in eta_peaks:
        row = []
        for tw in tau_widths:
            mid = 0.55
            scn_mod = Scenario(**{**SUMMER.__dict__,
                                  "tau_min": mid - tw / 2,
                                  "tau_max": mid + tw / 2,
                                  "eta_peak": ep})
            out = simulate(scn_mod, N=1000, seed=21)
            w = out["upper"][SUMMER.peak_hour] - out["lower"][SUMMER.peak_hour]
            row.append(w)
        heat.append(row)
    (DATA_DIR / "fig5_heatmap.json").write_text(json.dumps({
        "tau_widths": tau_widths, "eta_peaks": eta_peaks, "values": heat,
    }, indent=2))

    print("[ok] generated:")
    for p in sorted(DATA_DIR.glob("*.json")):
        print("   ", p.name, os.path.getsize(p), "bytes")

    print()
    print("Peak-hour widths (Table III reproduction):")
    print(f"  {'Scenario':<10} {'Proposed':>10} {'Fixed':>10} {'Unconstr':>10} {'Prob':>10} {'Rej %':>8}")
    for n, data in fig2.items():
        st = data["stats"]
        print(f"  {n:<10} {st['peak_hour_width_proposed']:>10.3f} "
              f"{st['peak_hour_width_fixed']:>10.3f} "
              f"{st['peak_hour_width_unconstrained']:>10.3f} "
              f"{st['peak_hour_width_probabilistic']:>10.3f} "
              f"{st['rejection_rate']*100:>7.1f}%")


if __name__ == "__main__":
    main()
