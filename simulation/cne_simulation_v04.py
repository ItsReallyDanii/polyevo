"""
Phase 3: CNE Dependency Accumulation Simulation
Epistatic-Metabolic Entanglement (EME) Hypothesis

Hypothesis originated by: Daniel Sleiman
Implemented by: Claude Sonnet 4.6 + Perplexity Sonnet 4.6 Thinking
Version: v0.4 — May 2026

THEORY:
Once a lineage crosses a critical metabolic energy threshold (delta_E >= ~0.55-0.70),
neutral genetic dependencies accumulate around the high-energy hardware via Constructive
Neutral Evolution (CNE) at a rate that makes deletion of the primary trait effectively
lethal. Apparent "reversals" are bypass constructions, not true deletions.

USAGE:
    pip install numpy matplotlib scipy
    python cne_simulation_v04.py                        # fast: 800 lineages x 5000 gens (~35s)
    python cne_simulation_v04.py --n 3000 --gens 8000   # publication quality (~90s)
    python cne_simulation_v04.py --csv-only             # no matplotlib needed
    python cne_simulation_v04.py --real-de              # use empirical dE from CSV
    python cne_simulation_v04.py --help

OUTPUTS:
    outputs/phase3_results.csv        Per-dE results table
    outputs/phase3_results.json       Machine-readable results + sigmoid params
    outputs/phase3_cne_simulation.png 3-panel figure (if matplotlib available)
    outputs/phase3_summary.txt        Terminal-ready summary block
"""

import numpy as np
import argparse, json, os, time, csv

# ── CLI ───────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="EME CNE Simulation v0.4",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument("--n",       type=int,   default=800,
    help="Lineages per dE level (default 800; use 3000 for publication quality)")
parser.add_argument("--gens",    type=int,   default=5000,
    help="Generations per lineage (default 5000; use 8000 for full run)")
parser.add_argument("--mut",     type=float, default=0.003,
    help="Base neutral mutation attachment rate (default 0.003)")
parser.add_argument("--thresh",  type=float, default=0.50,
    help="Lethality threshold: deletion_cost >= this = locked-in (default 0.50)")
parser.add_argument("--seed",    type=int,   default=42,
    help="Random seed (default 42)")
parser.add_argument("--out",     type=str,   default="outputs",
    help="Output directory (default: outputs/)")
parser.add_argument("--csv-only", action="store_true",
    help="Skip matplotlib — produce CSV, JSON, TXT only")
parser.add_argument("--real-de", action="store_true",
    help="Load dE values from data/species_bypass_table.csv instead of defaults")
args = parser.parse_args()

os.makedirs(args.out, exist_ok=True)
np.random.seed(args.seed)

# ── Delta_E levels ────────────────────────────────────────────────────────────
DEFAULT_DE_LEVELS = [0.1, 0.25, 0.5, 0.75, 1.0]
DEFAULT_LABELS = {
    0.10: "Partial fish (ectotherm baseline)",
    0.25: "Naked mole-rat equiv (behavioral outsourcing)",
    0.50: "Leatherback / Bluefin tuna (vascular bypass)",
    0.75: "Crocodilian ancestor (cardiovascular bypass)",
    1.00: "Full archosaurian endotherm (baseline endotherm)",
}
DEFAULT_SPECIES = {
    0.10: "Ectotherm baseline",
    0.25: "Heterocephalus glaber",
    0.50: "Dermochelys coriacea / Thunnus thynnus",
    0.75: "Crocodylus porosus",
    1.00: "Gallus gallus / Mus musculus",
}

def load_real_de():
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "species_bypass_table.csv")
    if not os.path.exists(csv_path):
        print(f"[!] --real-de set but {csv_path} not found. Run phase2_data_pull.py first.")
        print("    Falling back to estimated dE values.\n")
        return DEFAULT_DE_LEVELS, DEFAULT_LABELS, DEFAULT_SPECIES
    de_vals, labels, species = [], {}, {}
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            de = float(row["estimated_delta_e"])
            de_vals.append(de)
            labels[de] = row.get("label", row["species"])
            species[de] = row["species"]
    de_vals = sorted(set(de_vals))
    print(f"  Loaded {len(de_vals)} dE levels from species_bypass_table.csv")
    return de_vals, labels, species

DELTA_E_LEVELS, LABELS, SPECIES = (
    load_real_de() if args.real_de else (DEFAULT_DE_LEVELS, DEFAULT_LABELS, DEFAULT_SPECIES)
)

# ── Core model ────────────────────────────────────────────────────────────────

def attachment_prob(de, deps):
    """
    P(neutral dependency attaches this generation).
    base rate scales with de^1.5; autocatalytic boost: more deps = more surface area.
    Capped at 0.20 to prevent runaway.
    """
    base = args.mut * (de ** 1.5)
    return min(base * (1 + deps * 0.015), 0.20)

def deletion_cost(deps, de):
    """
    P(deleting primary trait is lethal | deps accumulated).
    Exponential approach to 1.0; rate of approach scales with de.
    """
    if deps == 0:
        return 0.0
    return min(1.0 - np.exp(-deps * de * 0.12), 1.0)

def sigmoid(x, L, k, x0):
    return L / (1.0 + np.exp(-k * (x - x0)))

# ── Run ───────────────────────────────────────────────────────────────────────

print("=" * 62)
print("  EME CNE Simulation v0.4 — Epistatic-Metabolic Entanglement")
print("  Hypothesis by Daniel Sleiman")
print("=" * 62)
print(f"\n  Lineages/dE  : {args.n}")
print(f"  Generations  : {args.gens}")
print(f"  Mut rate     : {args.mut}")
print(f"  Leth thresh  : {args.thresh}")
print(f"  Seed         : {args.seed}")
print(f"  dE levels    : {DELTA_E_LEVELS}")
print(f"  Output       : {args.out}/\n")

t0 = time.time()
pct_locked_vals, avg_lock_gen_vals = [], []
all_results = {}

for de in DELTA_E_LEVELS:
    locked_gens, deps_at_lock, final_deps = [], [], []
    for _ in range(args.n):
        deps, locked_gen = 0, -1
        for gen in range(args.gens):
            if np.random.random() < attachment_prob(de, deps):
                deps += 1
            if locked_gen == -1 and deletion_cost(deps, de) >= args.thresh:
                locked_gen = gen
                deps_at_lock.append(deps)
                break
        final_deps.append(deps)
        locked_gens.append(locked_gen)

    locked = [g for g in locked_gens if g != -1]
    never  = [g for g in locked_gens if g == -1]
    pct    = len(locked) / args.n * 100
    avg_lg = float(np.mean(locked))   if locked else None
    med_lg = float(np.median(locked)) if locked else None
    avg_dal = float(np.mean(deps_at_lock)) if deps_at_lock else 0.0
    avg_fd  = float(np.mean(final_deps))

    pct_locked_vals.append(pct)
    avg_lock_gen_vals.append(avg_lg)
    all_results[de] = {
        "delta_e": de,
        "label": LABELS.get(de, str(de)),
        "species_analog": SPECIES.get(de, "unknown"),
        "pct_locked": round(pct, 2),
        "pct_never_locked": round(len(never) / args.n * 100, 2),
        "avg_lock_gen": round(avg_lg, 1) if avg_lg is not None else None,
        "median_lock_gen": round(med_lg, 1) if med_lg is not None else None,
        "avg_deps_at_lock": round(avg_dal, 2),
        "avg_final_deps": round(avg_fd, 2),
    }
    ls   = f"{avg_lg:>7.0f}" if avg_lg is not None else "    N/A"
    flag = "  ← THRESHOLD ZONE" if 0 < pct < 100 else ""
    print(f"  dE={de:.2f} | {pct:6.1f}% locked | lock gen={ls} | deps@lock={avg_dal:5.1f}{flag}")

print(f"\n  Runtime: {time.time()-t0:.1f}s\n")

# ── Stats ─────────────────────────────────────────────────────────────────────
print("── Statistical Analysis ──")

lin_fit = np.polyfit(DELTA_E_LEVELS, pct_locked_vals, 1)
lin_res = float(np.sum((np.polyval(lin_fit, DELTA_E_LEVELS) - pct_locked_vals) ** 2))
sig_params = {}; ratio = 0.0; verdict = "insufficient data"
speed_r = speed_p = None

try:
    from scipy.optimize import curve_fit
    from scipy.stats import pearsonr

    popt, _ = curve_fit(sigmoid, DELTA_E_LEVELS, pct_locked_vals,
                        p0=[100, 10, 0.5], maxfev=10000,
                        bounds=([50, 0.1, 0.0], [110, 100, 1.0]))
    sig_res = float(np.sum((sigmoid(np.array(DELTA_E_LEVELS), *popt) - pct_locked_vals) ** 2))
    ratio   = lin_res / (sig_res + 1e-12)
    verdict = ("SIGMOIDAL THRESHOLD CONFIRMED" if ratio > 100 else
               "moderate sigmoid" if ratio > 5 else "weak sigmoid")
    sig_params = {"L": round(float(popt[0]),3), "k": round(float(popt[1]),3),
                  "x0_threshold": round(float(popt[2]),4)}
    print(f"  Sigmoid L={sig_params['L']:.1f}  k={sig_params['k']:.2f}  "
          f"threshold dE*={sig_params['x0_threshold']:.4f}")
    print(f"  Linear/Sigmoid ratio: {ratio:.0f}x  →  {verdict}")

    valid = [(de, ag) for de, ag in zip(DELTA_E_LEVELS, avg_lock_gen_vals) if ag is not None]
    if len(valid) >= 3:
        speed_r, speed_p = pearsonr([v[0] for v in valid], [v[1] for v in valid])
        sig_str = "p<0.05 ✓" if speed_p < 0.05 else f"p={speed_p:.4f} (marginal — add more dE levels)"
        print(f"  Lock-in speed r={speed_r:.4f}, {sig_str}")

except ImportError:
    print("  [!] scipy not found — pip install scipy  (skipping curve fit)")
except Exception as e:
    print(f"  Sigmoid fit error: {e}")

# ── CSV ───────────────────────────────────────────────────────────────────────
fieldnames = ["delta_e","label","species_analog","pct_locked","pct_never_locked",
              "avg_lock_gen","median_lock_gen","avg_deps_at_lock","avg_final_deps"]
csv_path = os.path.join(args.out, "phase3_results.csv")
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for de in DELTA_E_LEVELS:
        w.writerow({k: all_results[de][k] for k in fieldnames})
print(f"\n  CSV  → {csv_path}")

# ── JSON ──────────────────────────────────────────────────────────────────────
out_json = {
    "meta": {"project": "EME Hypothesis", "author": "Daniel Sleiman", "version": "v0.4",
             "params": {"n": args.n, "gens": args.gens, "mut": args.mut,
                        "thresh": args.thresh, "seed": args.seed}},
    "results": {str(k): v for k, v in all_results.items()},
    "statistics": {"sigmoid_params": sig_params, "linearity_ratio": round(ratio, 1),
                   "verdict": verdict,
                   "speed_r": round(speed_r, 4) if speed_r else None,
                   "speed_p": round(speed_p, 4) if speed_p else None},
}
json_path = os.path.join(args.out, "phase3_results.json")
with open(json_path, "w") as f:
    json.dump(out_json, f, indent=2)
print(f"  JSON → {json_path}")

# ── Summary TXT ───────────────────────────────────────────────────────────────
lines = [
    "=" * 62,
    "  EME PHASE 3 — SIMULATION SUMMARY",
    f"  {args.n} lineages × {args.gens} gens × {len(DELTA_E_LEVELS)} dE levels  |  seed={args.seed}",
    "=" * 62, "",
    f"  {'dE':>5}  {'%Locked':>9}  {'AvgLockGen':>12}  {'Deps@Lock':>10}  Species",
    f"  {'─'*5}  {'─'*9}  {'─'*12}  {'─'*10}  {'─'*35}",
]
for de in DELTA_E_LEVELS:
    r  = all_results[de]
    lg = f"{r['avg_lock_gen']:>8.0f}" if r["avg_lock_gen"] is not None else "     N/A"
    lines.append(f"  {de:>5.2f}  {r['pct_locked']:>8.1f}%  {lg}  "
                 f"{r['avg_deps_at_lock']:>10.1f}  {r['species_analog']}")
lines += [
    "",
    f"  Sigmoid dE*             : {sig_params.get('x0_threshold', 'N/A')}",
    f"  Linear/Sigmoid ratio    : {ratio:.0f}x",
    f"  VERDICT                 : {verdict}",
    f"  Lock-in speed r         : {round(speed_r,4) if speed_r else 'N/A'}",
    "",
    "  NEXT STEPS:",
    "  1. EltonTraits: https://figshare.com/collections/EltonTraits_1_0/3306933",
    "  2. AmphiBIO   : https://datadryad.org/stash/dataset/doi:10.5061/dryad.1mg8g",
    "     (NOT file_stream/67929 — that URL is a fossil paleontology dataset)",
    "  3. python phase2_data_pull.py",
    "  4. python cne_simulation_v04.py --real-de",
    "  5. Cite Cubo et al. 2026 (ScienceDirect) as adjacent — different mechanism",
    "=" * 62,
]
summary = "\n".join(lines)
print("\n" + summary)
txt_path = os.path.join(args.out, "phase3_summary.txt")
with open(txt_path, "w") as f:
    f.write(summary + "\n")
print(f"\n  TXT  → {txt_path}")

# ── Plot ──────────────────────────────────────────────────────────────────────
if not args.csv_only:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        x_s   = np.linspace(0.0, 1.1, 400)
        lin_y = np.polyval(lin_fit, x_s)
        colors = ["#2196F3","#4CAF50","#FF9800","#9C27B0","#F44336"]

        fig, axes = plt.subplots(1, 3, figsize=(17, 5))
        fig.suptitle("Epistatic-Metabolic Entanglement (EME) Hypothesis\n"
                     "Phase 3: CNE Dependency Accumulation — Daniel Sleiman",
                     fontsize=12, fontweight="bold")

        # Panel 1: sigmoid vs linear
        axes[0].plot(x_s, lin_y, "--", color="lightgray", lw=1.5, label="Linear", zorder=1)
        if sig_params:
            sy = sigmoid(x_s, sig_params["L"], sig_params["k"], sig_params["x0_threshold"])
            axes[0].plot(x_s, sy, "-", color="crimson", lw=2.5,
                         label=f"Sigmoid (dE*={sig_params['x0_threshold']:.3f})", zorder=2)
            axes[0].axvline(sig_params["x0_threshold"], color="gray", ls=":", alpha=0.7, lw=1.5)
        for de, pct, c in zip(DELTA_E_LEVELS, pct_locked_vals, colors):
            axes[0].scatter([de], [pct], s=100, color=c, zorder=5)
        axes[0].set_xlabel("ΔE magnitude"); axes[0].set_ylabel("% Lineages Locked-In")
        axes[0].set_title(f"Lock-In Rate\nSig/Lin ratio = {ratio:.2e}x")
        axes[0].legend(fontsize=8); axes[0].grid(True, alpha=0.3)
        axes[0].set_ylim(-5, 110); axes[0].set_xlim(-0.05, 1.15)

        # Panel 2: lock-in speed
        vde = [de for de, ag in zip(DELTA_E_LEVELS, avg_lock_gen_vals) if ag is not None]
        vag = [ag for ag in avg_lock_gen_vals if ag is not None]
        vc  = [colors[i] for i, ag in enumerate(avg_lock_gen_vals) if ag is not None]
        for de, ag, c in zip(vde, vag, vc):
            axes[1].scatter([de], [ag], s=100, color=c, zorder=5)
            axes[1].annotate(f"gen {ag:,.0f}", (de, ag), xytext=(0,-18),
                             textcoords="offset points", ha="center", fontsize=8, color="#444")
        if len(vde) >= 2:
            f2 = np.polyfit(vde, vag, 1)
            axes[1].plot(np.linspace(min(vde)-0.05, 1.05, 100),
                         np.polyval(f2, np.linspace(min(vde)-0.05, 1.05, 100)),
                         "--", color="steelblue", alpha=0.7, lw=1.5)
        axes[1].invert_yaxis()
        axes[1].set_xlabel("ΔE magnitude")
        axes[1].set_ylabel("Avg Lock-In Generation  (↓ = faster)")
        r_str = f"r={speed_r:.3f}" if speed_r else ""
        axes[1].set_title(f"Lock-In Speed vs ΔE\n{r_str}")
        axes[1].grid(True, alpha=0.3)

        # Panel 3: species table
        tdata = [
            ["Crocodilians",   "0.75", "3 cardiovascular\nstructures", "HIGH"],
            ["Naked mole-rat", "0.25", "Behavioral\noutsourcing",      "LOW"],
            ["Leatherback",    "0.50", "Gigantothermy\n+ CCHE",        "MODERATE"],
            ["Bluefin tuna",   "0.50", "Retia mirabilia",               "MODERATE"],
        ]
        axes[2].axis("off")
        tbl = axes[2].table(cellText=tdata,
                            colLabels=["Species","Est. ΔE","Bypass Type","Complexity"],
                            loc="center", cellLoc="left")
        tbl.auto_set_font_size(False); tbl.set_fontsize(8.5); tbl.scale(1.3, 2.5)
        for j in range(4):
            tbl[(0,j)].set_facecolor("#37474F")
            tbl[(0,j)].set_text_props(color="white", fontweight="bold")
        for i in range(1, 5):
            for j in range(4):
                tbl[(i,j)].set_facecolor("#fafafa" if i % 2 else "#f0f0f0")
        axes[2].set_title("Phase 1+2 Empirical Summary\n(all species: bypass, not deletion)",
                          fontweight="bold", fontsize=9)

        plt.tight_layout()
        png = os.path.join(args.out, "phase3_cne_simulation.png")
        plt.savefig(png, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  PNG  → {png}")
    except ImportError as e:
        print(f"  [!] Plot skipped: pip install matplotlib scipy")
    except Exception as e:
        print(f"  [!] Plot error: {e}")

print(f"\n  All outputs in: {os.path.abspath(args.out)}/\n  Done.\n")
