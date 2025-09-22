import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
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
motion_param_labels = ['roll', 'pitch', 'yaw', 'dS', 'dL', 'dP']
bad_subjects_movie2 = ['03', '07', '24', '37', '39', '43']  # based on the notes from the operator

# Load run length data and filter NNDB runs with >= 600 TRs
run_info = pd.read_csv('run_lengths.csv')
valid_nndb_runs = run_info[(run_info['dataset'] == 'NNdb') & (run_info['n_trs'] >= 600)]

# Convert to a dict: subject_id -> list of valid run indices (1-based)
valid_run_indices = defaultdict(list)
valid_run_lengths = defaultdict(list)
for _, row in valid_nndb_runs.iterrows():
    subj = str(row['subject']).zfill(2)
    valid_run_indices[subj].append(int(row['run_i']))
    valid_run_lengths[subj].append(int(row['n_trs']))


# ------------------- Data Collection ------------------- #
displacement = defaultdict(list)
displacement_delt = defaultdict(list)  # New: delta motion
motion_params = defaultdict(lambda: defaultdict(list))  # dataset -> param -> list of values

for label, base_path in datasets.items():
    for subject in sorted(base_path.iterdir()):
        subj_id = subject.name.replace('sub-', '').zfill(2)
        if label == 'Movie II' and subj_id in bad_subjects_movie2:
            print(f"Skipping bad MovieProject2 subject: {subject.name}")
            continue

        results_path = subject / f"{subject.name}.results"
        if not results_path.exists():
            continue

        if label == 'Movie I':
            if subj_id not in valid_run_indices:
                print(f"Skipping subject with no valid runs: sub-{subj_id}")
                continue

        # Max displacement
        for file in sorted(results_path.glob('mm.r0[0-9]*_norm_downsampled')):
            run_num = int(file.name.split('.')[1][1:3])
            if label == 'Movie I' and run_num not in valid_run_indices[subj_id]:
                continue
            if '_delt' in file.name or '_norm_norm' in file.name:
                continue
            try:
                data = np.loadtxt(file, skiprows=2)
                displacement[label].extend(np.abs(data))
            except Exception as e:
                print(f"Could not load {file}: {e}")

        # Delta displacement
        for file in results_path.glob('mm.r0*_delt'):
            run_num = int(file.name.split('.')[1][1:3])
            if label == 'Movie I' and run_num not in valid_run_indices[subj_id]:
                continue
            if '_norm' in file.name:
                continue
            try:
                data = np.loadtxt(file, skiprows=2)
                displacement_delt[label].extend(np.abs(data))
            except Exception as e:
                print(f"Could not load {file}: {e}")

        # 6 motion parameters
        dfile = results_path / 'dfile_rall_norm_downsampled.1D'
        if dfile.exists():
            try:
                data = np.loadtxt(dfile, comments='#')

                if label == 'Movie I':
                    # Get all run lengths (valid and invalid) for this subject
                    all_runs = run_info[
                        (run_info['dataset'] == 'NNdb') & (run_info['subject'] == int(subj_id))].sort_values(by='run_i')

                    valid_runs = valid_run_indices[subj_id]
                    valid_tr_slices = []
                    tr_start = 0

                    for _, row in all_runs.iterrows():
                        tr_count = int(row['n_trs'])
                        run_i = int(row['run_i'])

                        if run_i in valid_runs:
                            valid_tr_slices.append((tr_start, tr_start + tr_count))
                        else:
                            print(f"Skipping sub-{subj_id} run-{str(run_i).zfill(2)} with {tr_count} TRs")

                        tr_start += tr_count

                    # Concatenate only the TRs from valid runs
                    valid_data = np.concatenate([data[start:end] for start, end in valid_tr_slices], axis=0)
                else:
                    valid_data = data

                for i, param in enumerate(motion_param_labels):
                    motion_params[label][param].extend(np.abs(valid_data[:, i]))

            except Exception as e:
                print(f"Could not load {dfile}: {e}")


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
    for label, color in zip(values_dict, ['blue', 'orange']):
        data = np.array(values_dict[label])
        plt.hist(data, bins=bin_edges, alpha=0.5, color=color, label=f"{label} (hist)", edgecolor='black')
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
    for idx, (label, color) in enumerate(zip(values_dict, ['blue', 'orange'])):
        shift = (-1 if idx == 0 else 1) * bar_width / 2
        plt.bar(bin_centers + shift, counts[label], width=bar_width, color=color, label=label)

    # Connect peaks
    for label, color in zip(values_dict, ['blue', 'orange']):
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

    for idx, (label, color) in enumerate(zip(values_dict, ['blue', 'orange'])):
        shift = (-1 if idx == 0 else 1) * bar_width / 2
        norm_counts = counts[label] / np.sum(counts[label])
        plt.bar(bin_centers + shift, norm_counts, width=bar_width, color=color, label=label)

    for label, color in zip(values_dict, ['blue', 'orange']):
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
# Delta displacement
# plot_distributions('MaxDisplacement_Delta', displacement_delt, 'Millimetres',
#                    overlap_path=overlap_dir, grouped_path=grouped_dir)

# 6 motion parameters
for param in motion_param_labels:
    unit = 'Degrees' if param in ['roll', 'pitch', 'yaw'] else 'Millimetres'
    plot_distributions(param, {ds: motion_params[ds][param] for ds in datasets},
                       unit_label=unit,
                       overlap_path=overlap_dir,
                       grouped_path=grouped_dir)
