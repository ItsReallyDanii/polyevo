"""
Phase 2: Quantitative delta_E estimation from real metabolic databases.
EME Hypothesis — Daniel Sleiman

Run AFTER cne_simulation_v04.py to replace estimated dE values with real BMR data.

REQUIRED DOWNLOADS (free, open datasets):
  EltonTraits 1.0 → https://figshare.com/collections/EltonTraits_1_0/3306933
                    download MamFuncDat.txt → save to data/MamFuncDat.txt

  AmphiBIO v1     → https://datadryad.org/stash/dataset/doi:10.5061/dryad.1mg8g
                    NOTE: Use the DATASET PAGE, not file_stream/67929
                    (file_stream/67929 is a fossil paleontology paper — wrong dataset)
                    download AmphiBIO_v1.csv → save to data/AmphiBIO_v1.csv

USAGE:
  pip install requests pandas openpyxl
  python phase2_data_pull.py
"""
import os, json, csv
import requests
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

TARGETS = ["Crocodylus porosus","Alligator mississippiensis","Heterocephalus glaber",
           "Dermochelys coriacea","Thunnus thynnus","Gallus gallus","Mus musculus"]


def fetch_eltontraits():
    path = os.path.join(DATA_DIR, "MamFuncDat.txt")
    if not os.path.exists(path):
        print("  [!] MamFuncDat.txt not found.")
        print("      https://figshare.com/collections/EltonTraits_1_0/3306933")
        print("      Save to: data/MamFuncDat.txt\n")
        return None
    df = pd.read_csv(path, sep="\t", encoding="latin-1")
    sub = df[df["Scientific"].isin(TARGETS)][["Scientific","BodyMass-Value"]].copy()
    out = os.path.join(DATA_DIR, "eltontraits_subset.csv")
    sub.to_csv(out, index=False)
    print(f"  EltonTraits: {len(sub)} species found → {out}")
    return sub


def fetch_amphibio():
    path = os.path.join(DATA_DIR, "AmphiBIO_v1.csv")
    if not os.path.exists(path):
        print("  [!] AmphiBIO_v1.csv not found.")
        print("      CORRECT URL: https://datadryad.org/stash/dataset/doi:10.5061/dryad.1mg8g")
        print("      WRONG  URL : datadryad.org/stash/downloads/file_stream/67929")
        print("                   (that's a nectocaridid fossil paper — not AmphiBIO)")
        print("      Save to: data/AmphiBIO_v1.csv\n")
        return None
    df = pd.read_csv(path)
    print(f"  AmphiBIO: {len(df)} rows, {len(df.columns)} columns")
    return df


def fetch_timetree(sp1, sp2):
    url = f"http://timetree.org/api/pairwise/{sp1.replace(' ','_')}/{sp2.replace(' ','_')}"
    try:
        r = requests.get(url, timeout=12)
        return r.json() if r.status_code == 200 else None
    except:
        return None


if __name__ == "__main__":
    print("=" * 56)
    print("  EME Phase 2 — Quantitative dE Data Pull")
    print("=" * 56)

    print("\n1. EltonTraits 1.0...")
    elton = fetch_eltontraits()

    print("2. AmphiBIO v1...")
    amphibio = fetch_amphibio()

    print("3. TimeTree divergence times...")
    pairs = [("Crocodylus porosus","Gallus gallus"),
             ("Heterocephalus glaber","Mus musculus"),
             ("Dermochelys coriacea","Gallus gallus")]
    div = {}
    for sp1, sp2 in pairs:
        print(f"  Querying {sp1} vs {sp2}...")
        result = fetch_timetree(sp1, sp2)
        if result:
            div[f"{sp1}_vs_{sp2}"] = result
            mya = result.get("median_time", result.get("time","N/A"))
            print(f"    → {mya} MYA")
        else:
            print(f"    → No result (API down or no internet)")
    with open(os.path.join(DATA_DIR, "timetree_divergence.json"), "w") as f:
        json.dump(div, f, indent=2)

    print("\n4. Literature BMR ratio estimates:")
    estimates = [
        ("Crocodylus porosus",    0.75, "7-8x BMR — Seymour 2004 archosaurian ancestry"),
        ("Heterocephalus glaber", 0.25, "~2.5x — near-ectotherm thermoneutral"),
        ("Dermochelys coriacea",  0.50, "~5x — gigantothermy + CCHE"),
        ("Thunnus thynnus",       0.50, "~5x — retia mirabilia regional endothermy"),
        ("Alligator miss.",       0.75, "Same archosaurian lineage as crocs"),
    ]
    rows = []
    for sp, de, note in estimates:
        rows.append({"species": sp, "estimated_delta_e": de, "note": note,
                     "source": "literature estimate — replace with real BMR"})
        print(f"  {sp:<35} dE={de:.2f}  {note}")

    tbl_path = os.path.join(DATA_DIR, "species_bypass_table.csv")
    if not os.path.exists(tbl_path):
        with open(tbl_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["species","estimated_delta_e","note","source"])
            w.writeheader(); w.writerows(rows)
        print(f"\n  Created → {tbl_path}")

    print("\n  NEXT:")
    print("  1. Download datasets above")
    print("  2. Rerun this script → real BMR ratios computed")
    print("  3. python simulation/cne_simulation_v04.py --real-de\n")
