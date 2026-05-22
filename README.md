# Epistatic-Metabolic Entanglement (EME) Project

**Hypothesis by Daniel Sleiman**  
AI: Claude Sonnet 4.6 + Perplexity Sonnet 4.6 Thinking  
Status: Phase 3 complete · Phase 2 quantitative pending

## Quick Start

```bash
pip install numpy matplotlib scipy
python simulation/cne_simulation_v04.py
```

```bash
# CSV/JSON only (no matplotlib):
python simulation/cne_simulation_v04.py --csv-only

# Full high-fidelity run (~90s):
python simulation/cne_simulation_v04.py --n 3000 --gens 8000

# After downloading EltonTraits + AmphiBIO:
python simulation/phase2_data_pull.py
python simulation/cne_simulation_v04.py --real-de
```

## Results

| ΔE   | Species Analog      | % Locked | Lock-In Gen |
|------|---------------------|----------|-------------|
| 0.10 | Partial fish        | 0%       | Never       |
| 0.25 | Naked mole-rat      | 0%       | Never       |
| 0.50 | Leatherback/tuna    | ~1–21%   | ~4,300–6,800|
| 0.75 | Croc ancestor       | ~78–99%  | ~3,300–3,900|
| 1.00 | Full endotherm      | ~100%    | ~1,900–2,000|

**Sigmoid dE* ≈ 0.55–0.69 · ~117–254M× better than linear · r=−0.993**

## Structure

```
eme_project/
├── simulation/
│   ├── cne_simulation_v04.py    # Phase 3 main model
│   └── phase2_data_pull.py      # Phase 2 BMR data pull
├── data/
│   └── species_bypass_table.csv # Phase 1 empirical bypass table
├── docs/
│   └── CONTROL_PACK.md          # Full claim registry + next steps
└── outputs/                     # CSV, JSON, PNG, TXT generated here
```

## ⚠️ AmphiBIO URL Note

`file_stream/67929` on Dryad = nectocaridid fossil paper (wrong).  
Correct: `https://datadryad.org/stash/dataset/doi:10.5061/dryad.1mg8g`
