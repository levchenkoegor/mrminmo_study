import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
from run_selection import bad_subjects_movie2, run_table, keep_valid
from scipy.stats import gaussian_kde
import matplotlib.patheffects as path_effects


# ------------------- Setup ------------------- #
output_root = Path('/egor2/egor/MinMo_movements/retrospective_study/group_analysis')
overlap_dir = output_root / 'plots_motion_params'
grouped_dir = output_root / 'plots_motion_params_grouped'
normalised_dir = output_root / 'plots_motion_params_normalised'
overlap_dir.mkdir(parents=True, exist_ok=True)
grouped_dir.mkdir(parents=True, exist_ok=True)
normalised_dir.mkdir(parents=True, exist_ok=True)

datasets = {
    'Movie I': Path('derivatives_nndb'),
    'Movie II': Path('derivatives_btf')
}
DISPLAY = {'Movie I': 'Standard padding', 'Movie II': 'MR-MinMo'}
COLORS = {'Movie I': '#2a78d6', 'Movie II': '#eb6834'}  # validated categorical slots 1-2
motion_param_labels = ['roll', 'pitch', 'yaw', 'dS', 'dL', 'dP']


# ------------------- Data Collection ------------------- #
displacement = defaultdict(list)
motion_params = defaultdict(lambda: defaultdict(list))  # dataset -> param -> list of values
enorm_values = defaultdict(list)       # dataset -> list of enorm values
outlier_values = defaultdict(list)     # dataset -> list of outlier fraction values

for label, base_path in datasets.items():
    for subject in sorted(base_path.iterdir()):
        subj_id = subject.name.replace('sub-', '').zfill(2)      # zero-padded, for lookups
        afni_subj_id = subject.name.replace('sub-', '', 1)       # raw, for motion_*/outcount filenames

        if label == 'Movie II' and subj_id in bad_subjects_movie2:
            print(f"Skipping bad MovieProject2 subject: {subject.name}")
            continue

        results_path = subject / f"{subject.name}.results"
        if not results_path.exists():
            continue

        runs = run_table(label, subj_id, results_path)
        valid_runs = {run_i for run_i, _, valid in runs if valid}
        if not valid_runs:
            print(f"Skipping subject with no valid runs: sub-{subj_id}")
            continue

        # Max displacement
        for file in sorted(results_path.glob('mm.r0[0-9]*_norm_downsampled')):
            run_num = int(file.name.split('.')[1][1:3])
            if run_num not in valid_runs:
                continue
            try:
                data = np.loadtxt(file, skiprows=2)
                displacement[label].extend(np.abs(data))
            except Exception as e:
                print(f"Could not load {file}: {e}")

        # 6 motion parameters
        dfile = results_path / 'dfile_rall_norm_downsampled.1D'
        if dfile.exists():
            try:
                valid_data = keep_valid(np.loadtxt(dfile, comments='#'), runs)
                for i, param in enumerate(motion_param_labels):
                    motion_params[label][param].extend(np.abs(valid_data[:, i]))
            except Exception as e:
                print(f"Could not load {dfile}: {e}")

        # Enorm (motion_{afni_subj_id}_enorm_downsampled.1D, produced by 03_normalize_runs.py)
        enorm_file = results_path / f'motion_{afni_subj_id}_enorm_downsampled.1D'
        if enorm_file.exists():
            try:
                enorm_values[label].extend(np.abs(keep_valid(np.loadtxt(enorm_file), runs)))
            except Exception as e:
                print(f"Could not load {enorm_file}: {e}")
        else:
            print(f"Missing: {enorm_file.name} for {subject.name}")

        # Outlier fraction (outcount_rall_downsampled.1D, produced by 03_normalize_runs.py)
        outcount_file = results_path / 'outcount_rall_downsampled.1D'
        if outcount_file.exists():
            try:
                outlier_values[label].extend(keep_valid(np.loadtxt(outcount_file), runs))  # already non-negative
            except Exception as e:
                print(f"Could not load {outcount_file}: {e}")
        else:
            print(f"Missing: {outcount_file.name} for {subject.name}")


# ------------------- Plotting Function ------------------- #
def plot_distributions(param_name, values_dict, unit_label, overlap_path, grouped_path):
    # Collect values
    all_vals = np.concatenate([np.array(values_dict[k]) for k in values_dict])
    bin_edges = np.linspace(0, np.percentile(all_vals, 99), 60)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    bar_width = (bin_edges[1] - bin_edges[0]) * 0.4

    # Histogram counts
    counts = {}
    for label in values_dict:
        counts[label], _ = np.histogram(values_dict[label], bins=bin_edges)

    # ---------- Overlapping Histogram + KDE ---------- #
    plt.figure(figsize=(10, 6))
    for label, color in ((k, COLORS[k]) for k in values_dict):
        data = np.array(values_dict[label])
        plt.hist(data, bins=bin_edges, alpha=0.5, color=color, label=f"{DISPLAY[label]} (hist)", edgecolor='black')
        kde = gaussian_kde(data)
        x_vals = np.linspace(bin_edges.min(), bin_edges.max(), 1000)
        bin_width = bin_edges[1] - bin_edges[0]
        plt.plot(
            x_vals,
            kde(x_vals) * len(data) * bin_width,
            color=color,
            lw=2,
            path_effects=[path_effects.withStroke(linewidth=3, foreground='black')]
        )

    plt.title(f'Distribution of {param_name}')
    plt.xlabel(unit_label)
    plt.ylabel('Count')
    plt.legend()
    plt.grid(True)
    plt.savefig(overlap_path / f"{param_name}_distribution.png", dpi=300, bbox_inches='tight')
    plt.close()

    # ---------- Grouped Bar Plot + Peak Lines ---------- #
    plt.figure(figsize=(10, 6))
    for idx, (label, color) in enumerate(((k, COLORS[k]) for k in values_dict)):
        shift = (-1 if idx == 0 else 1) * bar_width / 2
        plt.bar(bin_centers + shift, counts[label], width=bar_width, color=color, label=DISPLAY[label])

    # Connect peaks
    for label, color in ((k, COLORS[k]) for k in values_dict):
        plt.plot(bin_centers, counts[label], color=color, lw=2,
                 path_effects=[path_effects.withStroke(linewidth=3, foreground='black')])

    plt.title(f'Distribution of {param_name} metric', fontsize=22)
    plt.xlabel(unit_label, fontsize=18)
    plt.ylabel('Count', fontsize=18)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.legend(fontsize=16)
    plt.grid(True)
    plt.savefig(grouped_path / f"{param_name}_grouped_distribution.png", dpi=300, bbox_inches='tight')
    plt.close()

    # ---------- Normalised Grouped Plot (Density) ---------- #
    plt.figure(figsize=(10, 6))

    for idx, (label, color) in enumerate(((k, COLORS[k]) for k in values_dict)):
        shift = (-1 if idx == 0 else 1) * bar_width / 2
        norm_counts = counts[label] / np.sum(counts[label])
        plt.bar(bin_centers + shift, norm_counts, width=bar_width, color=color, label=DISPLAY[label])

    for label, color in ((k, COLORS[k]) for k in values_dict):
        norm_counts = counts[label] / np.sum(counts[label])
        plt.plot(bin_centers, norm_counts, color=color, lw=2,
                 path_effects=[path_effects.withStroke(linewidth=3, foreground='black')])

    plt.title(f'Distribution of {param_name} metric', fontsize=22)
    plt.xlabel(unit_label, fontsize=18)
    plt.ylabel('Density', fontsize=18)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.legend(fontsize=16)
    plt.grid(True)
    plt.savefig(normalised_dir / f"{param_name}_grouped_normalised.png", dpi=300, bbox_inches='tight')
    plt.close()


# ------------------- Plot All Metrics ------------------- #
# Max displacement
plot_distributions('MaxDisplacement', displacement, 'Millimetres',
                   overlap_path=overlap_dir, grouped_path=grouped_dir)

# 6 motion parameters
for param in motion_param_labels:
    unit = 'Degrees' if param in ['roll', 'pitch', 'yaw'] else 'Millimetres'
    plot_distributions(param, {ds: motion_params[ds][param] for ds in datasets},
                       unit_label=unit,
                       overlap_path=overlap_dir,
                       grouped_path=grouped_dir)

# NEW: Enorm
plot_distributions('Enorm', enorm_values, 'mm / TR',
                   overlap_path=overlap_dir, grouped_path=grouped_dir)

# NEW: Outlier fraction
plot_distributions('OutlierFraction', outlier_values, 'Fraction of voxels',
                   overlap_path=overlap_dir, grouped_path=grouped_dir)
