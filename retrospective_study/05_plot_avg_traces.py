import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
from scipy.stats import sem

# Constants
motion_param_labels = ['roll', 'pitch', 'yaw', 'dS', 'dL', 'dP']
datasets = {
    'Movie I': Path('derivatives_nndb'),
    'Movie II': Path('derivatives_btf')
}
bad_subjects_movie2 = ['03', '07', '24', '37', '39', '43']
run_info = pd.read_csv('run_lengths.csv')
valid_nndb_runs = run_info[(run_info['dataset'] == 'NNdb') & (run_info['n_trs'] >= 600)]
output_dir = Path("group_analysis/avg_traces/")
output_dir.mkdir(parents=True, exist_ok=True)

# Compute total TRs per subject for Movie I
nndb_trs = valid_nndb_runs.groupby('subject')['n_trs'].sum().reset_index()
nndb_trs['subject'] = nndb_trs['subject'].astype(str).str.zfill(2)
nndb_total_trs = dict(zip(nndb_trs['subject'], nndb_trs['n_trs']))

# Determine min length from Movie II
btf_tr_lengths = []
for subj in (datasets['Movie II']).iterdir():
    if subj.name.replace('sub-', '') in bad_subjects_movie2:
        continue
    dfile = subj / f"{subj.name}.results" / "dfile_rall_norm.1D"
    if dfile.exists():
        try:
            data = np.loadtxt(dfile, comments='#')
            btf_tr_lengths.append(data.shape[0])
        except Exception:
            pass
min_len_btf = min(btf_tr_lengths)

# ------------------- Collect and Average ------------------- #
traces = defaultdict(lambda: defaultdict(list))
included_movie1_subjects = set()

for label, base_path in datasets.items():
    for subject in sorted(base_path.iterdir()):
        subj_id = subject.name.replace('sub-', '').zfill(2)
        if label == 'Movie II' and subj_id in bad_subjects_movie2:
            continue
        if label == 'Movie I':
            if subj_id not in nndb_total_trs or nndb_total_trs[subj_id] < min_len_btf:
                continue
            included_movie1_subjects.add(subj_id)

        dfile = subject / f"{subject.name}.results" / "dfile_rall_norm.1D"
        if not dfile.exists():
            continue

        try:
            data = np.loadtxt(dfile, comments='#')
            if data.shape[0] < min_len_btf:
                continue
            data = data[:min_len_btf]
            for i, param in enumerate(motion_param_labels):
                traces[label][param].append(data[:, i])
        except Exception:
            continue

# Print the number of included Movie I participants
print(f"Included {len(included_movie1_subjects)} subjects from Movie I with ≥ {min_len_btf} TRs.")


# ------------------- Plot ------------------- #
for param in motion_param_labels:
    plt.figure(figsize=(12, 6))

    for label, color in zip(['Movie I', 'Movie II'], ['blue', 'orange']):
        series = traces[label][param]
        if not series:
            continue
        data = np.stack(series, axis=0)  # shape: (n_subjects, n_timepoints)
        mean_trace = np.mean(data, axis=0)
        stderr = sem(data, axis=0)
        plt.plot(mean_trace, label=label, color=color)
        plt.fill_between(np.arange(min_len_btf),
                         mean_trace - stderr,
                         mean_trace + stderr,
                         color=color, alpha=0.3)

    plt.title(f'Average {param} trace across time')
    plt.xlabel('Time (TR)')
    plt.ylabel('Motion (degrees/mm)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / f"{param}_avg_trace.png", dpi=300)
    plt.close()
