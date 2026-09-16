#!/usr/bin/env python3
"""Verify the single-letter building codes in `richtor_mappings.py` against the training data.

The API sends these codes straight to the ML model, so a code whose meaning is wrong makes the model
score a different building than the user described. This script re-derives the mapping from the data
and fails loudly if the file disagrees. It uses three independent signals:

  1. JOINT STRUCTURE (decisive) — the (foundation, roof, ground_floor) 3-way joint distribution of
     the DrivenData sample, read through the mapping under test, compared with the survey's own
     labelling. The mapping must be the best of all 86,400 per-column permutations.
  2. DAMAGE RANKING — the mean-damage ordering of the codes must equal the ordering of the survey
     categories. This is a physical check: worse construction must show worse damage in both files.
  3. MARGINAL SHARE — each code's share of buildings must be within a few points of its category's
     share. DrivenData covers 31 districts and the survey 11, so shares differ by up to ~4 points;
     this check is corroborative, not decisive.

Data prerequisites (git-LFS, not in the working tree — see README):
  * DrivenData "Richter's Predictor": train_values.csv + train_labels.csv
  * Nepal Building Structure Survey: training/csv_building_structure.csv
Point the script at them with --data-dir (default: ./data, then ~/HermesWork/resilienceai-ml-research/data).

Usage:
    python backend/scripts/verify_code_mappings.py [--data-dir /path/to/csvs]
Exit codes: 0 = all checks pass, 1 = a check failed, 2 = data not found.
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from richtor_mappings import RICHTER_DATASET_MAPPINGS as M  # noqa: E402

COLS = ["foundation_type", "roof_type", "ground_floor_type"]
SHARE_TOLERANCE = 5.0   # percentage points; two different district samples

# canonical survey category -> substring that identifies it in a mapping description
CANON = {
    "foundation_type": {
        "Mud mortar-Stone/Brick": "mud mortar - stone", "Bamboo/Timber": "bamboo / timber",
        "Cement-Stone/Brick": "cement - stone", "RC": "reinforced concrete",
        "Other": "other / unclassified"},
    "roof_type": {
        "Bamboo/Timber-Light roof": "light roof", "Bamboo/Timber-Heavy roof": "heavy roof",
        "RCC/RB/RBC": "reinforced concrete"},
    "ground_floor_type": {
        "Mud": "mud", "RC": "reinforced concrete", "Brick/Stone": "brick / stone",
        "Timber": "timber", "Other": "other / unclassified"},
}


def canonical(col: str, label: str):
    low = label.lower()
    hits = [c for c, needle in CANON[col].items() if needle in low]
    return hits[0] if len(hits) == 1 else None


def find_data(explicit: str | None):
    candidates = [explicit] if explicit else []
    candidates += ["./data", os.path.expanduser("~/HermesWork/resilienceai-ml-research/data")]
    for d in candidates:
        if d and all(os.path.exists(os.path.join(d, f)) for f in
                     ("train_values.csv", "train_labels.csv", "csv_building_structure.csv")):
            return d
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()
    data = find_data(args.data_dir)
    if data is None:
        print("data not found. Fetch the git-LFS files first (see module docstring) and pass "
              "--data-dir.", file=sys.stderr)
        return 2
    print(f"data dir: {data}\n")

    mapped = {c: {code: canonical(c, d["description"]) for code, d in M[c].items()} for c in COLS}
    print("mapping under test:")
    for c in COLS:
        print(f"  {c}: {mapped[c]}")

    dd = pd.read_csv(f"{data}/train_values.csv", usecols=["building_id"] + COLS).merge(
        pd.read_csv(f"{data}/train_labels.csv"), on="building_id")
    sv = pd.read_csv(f"{data}/csv_building_structure.csv", low_memory=False,
                     usecols=COLS + ["damage_grade"])
    sv["y"] = sv["damage_grade"].str.extract(r"(\d)").astype(float)
    dd["y"] = dd["damage_grade"]
    failures: list[str] = []

    print("\n[1/3] marginal share (corroborative)")
    for c in COLS:
        dd_m = 100 * dd[c].value_counts(normalize=True)
        sv_m = 100 * sv[c].value_counts(normalize=True)
        for code, cat in mapped[c].items():
            d, s = dd_m.get(code, 0.0), sv_m.get(cat, 0.0)
            ok = abs(d - s) <= SHARE_TOLERANCE
            if not ok:
                failures.append(f"share {c}/{code}: {d:.2f}% vs {s:.2f}%")
            print(f"   {c:18s} {code} -> {cat:24s} {d:6.2f}% vs {s:6.2f}%  "
                  f"{'ok' if ok else 'FAIL'}")

    print("\n[2/3] mean-damage ranking (physical check)")
    for c in COLS:
        dd_rank = [mapped[c][code] for code in dd.groupby(c).y.mean().sort_values().index]
        sv_rank = list(sv.groupby(c).y.mean().sort_values().index)
        ok = dd_rank == sv_rank
        if not ok:
            failures.append(f"rank {c}: {dd_rank} vs {sv_rank}")
        print(f"   {c:18s} dd={dd_rank}\n   {'':18s} sv={sv_rank}  {'ok' if ok else 'FAIL'}")

    print("\n[3/3] 3-way joint distribution (decisive)")
    cats = {c: sorted(sv[c].unique()) for c in COLS}
    sv_idx = {c: {v: i for i, v in enumerate(cats[c])} for c in COLS}
    arr = np.column_stack([sv[c].map(sv_idx[c]).to_numpy() for c in COLS])
    sv_joint = np.zeros(tuple(len(cats[c]) for c in COLS))
    np.add.at(sv_joint, tuple(arr.T), 1.0)
    sv_joint /= sv_joint.sum()

    codes = {c: sorted(dd[c].unique()) for c in COLS}
    dd_idx = {c: {v: i for i, v in enumerate(codes[c])} for c in COLS}
    arr = np.column_stack([dd[c].map(dd_idx[c]).to_numpy() for c in COLS])
    dd_joint = np.zeros(tuple(len(codes[c]) for c in COLS))
    np.add.at(dd_joint, tuple(arr.T), 1.0)
    dd_joint /= dd_joint.sum()

    ranked = []
    for pf in itertools.permutations(cats["foundation_type"], len(codes["foundation_type"])):
        for pr in itertools.permutations(cats["roof_type"], len(codes["roof_type"])):
            for pg in itertools.permutations(cats["ground_floor_type"], len(codes["ground_floor_type"])):
                idx = [[sv_idx[c][v] for v in p] for c, p in zip(COLS, (pf, pr, pg))]
                ranked.append((float(np.abs(sv_joint[np.ix_(*idx)] - dd_joint).sum() / 2), pf, pr, pg))
    ranked.sort(key=lambda t: t[0])
    print(f"   best distance {ranked[0][0]:.4f} (runner-up {ranked[1][0]:.4f}); "
          f"margin {100*(ranked[1][0]-ranked[0][0])/ranked[1][0]:.1f}%")
    winner = dict(zip(COLS, ranked[0][1:]))
    for c in COLS:
        want = [mapped[c][code] for code in codes[c]]
        got = list(winner[c])
        ok = want == got
        if not ok:
            failures.append(f"joint {c}: file {want} vs best {got}")
        print(f"   {c:18s} file={want}  best={got}  {'ok' if ok else 'FAIL'}")

    if failures:
        print(f"\nRESULT: {len(failures)} FAILURE(S)")
        for f in failures:
            print("  -", f)
        return 1
    print("\nRESULT: all checks pass — the codes in richtor_mappings.py match the training data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
