"""Participant and run inclusion shared by the stats (06) and plotting (04) scripts."""
from collections import defaultdict

import numpy as np
import pandas as pd

bad_subjects_movie2 = ['03', '07', '24', '37', '39', '43']  # based on the notes from the operator

MIN_RUN_SECONDS = 600   # runs shorter than 10 min are excluded in both datasets
DS_TR_SECONDS = 3       # TR after downsampling (03_normalize_runs.py)

run_info = pd.read_csv('run_lengths.csv')
valid_run_indices = defaultdict(list)  # NNdb subject -> runs with >= 600 raw TRs (TR = 1 s)
for _, row in run_info[(run_info['dataset'] == 'NNdb') & (run_info['n_trs'] >= 600)].iterrows():
    valid_run_indices[str(row['subject']).zfill(2)].append(int(row['run_i']))


def run_table(label, subj_id, results_path):
    """[(run_i, n_downsampled_trs, valid)] in the order runs are concatenated in the *_rall files.
    Movie I: runs >= 600 raw TRs per run_lengths.csv. Movie II: runs are predefined, but a
    participant-initiated pause splits a run (sub-36), so runs < 10 min are dropped too."""
    runs = []
    for mm_file in sorted(results_path.glob('mm.r0[0-9]_norm_downsampled')):
        run_i = int(mm_file.name[4:6])
        n_ds = len(np.loadtxt(mm_file, skiprows=2))
        if label == 'Movie I':
            valid = run_i in valid_run_indices[subj_id]
        else:
            valid = n_ds * DS_TR_SECONDS >= MIN_RUN_SECONDS
        runs.append((run_i, n_ds, valid))
    return runs


def keep_valid(data, runs):
    """Slice the concatenated (downsampled) per-TR data to valid runs only."""
    if sum(n for _, n, _ in runs) != len(data):
        raise ValueError(f"run lengths sum to {sum(n for _, n, _ in runs)}, data has {len(data)} rows")
    pieces, start = [], 0
    for _, n, valid in runs:
        if valid:
            pieces.append(data[start:start + n])
        start += n
    return np.concatenate(pieces, axis=0)
