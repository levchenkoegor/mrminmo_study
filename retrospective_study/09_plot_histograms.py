import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import gaussian_kde
import matplotlib.patheffects as path_effects

# ------------------- Setup ------------------- #
output_root = Path('/egor2/egor/MinMo_movements/retrospective_study/group_analysis')
delta_csv = output_root / 'delta_max_per_subject.csv'
btf_path = Path('derivatives_btf')
nndb_path = Path('derivatives_nndb')

delta_plot_dir = output_root / 'plots_motion_params_delta'
delta_max_dir = output_root / 'plots_motion_params_delta_max'
delta_plot_dir.mkdir(parents=True, exist_ok=True)
delta_max_dir.mkdir(parents=True, exist_ok=True)

metrics = ['roll', 'pitch', 'yaw', 'dS', 'dL', 'dP']
unit_labels = {
    'roll': 'Degrees', 'pitch': 'Degrees', 'yaw': 'Degrees',
    'dS': 'Millimetres', 'dL': 'Millimetres', 'dP': 'Millimetres'
}
dataset_labels = {
    'derivatives_nndb': 'Movie I',
    'derivatives_btf': 'Movie II'
}
dataset_paths = {
    'derivatives_nndb': nndb_path,
    'derivatives_btf': btf_path
}

# ------------------- Plotting Function ------------------- #
def plot_normalised_hist(metric, data_dict, output_path, ylabel):
    all_vals = np.concatenate(list(data_dict.values()))
    bin_edges = np.linspace(0, np.percentile(all_vals, 99), 60)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    bar_width = (bin_edges[1] - bin_edges[0]) * 0.4

    plt.figure(figsize=(10, 6))

    for idx, (label, color) in enumerate(zip(data_dict, ['blue', 'orange'])):
        vals = np.array(data_dict[label])
        shift = (-1 if idx == 0 else 1) * bar_width / 2
        counts, _ = np.histogram(vals, bins=bin_edges)
        norm_counts = counts / np.sum(counts)

        plt.bar(bin_centers + shift, norm_counts, width=bar_width, color=color, alpha=0.6, label=label)
        plt.plot(bin_centers, norm_counts, color=color, lw=2,
                 path_effects=[path_effects.withStroke(linewidth=3, foreground='black')])

    plt.title(f'Normalised Delta Distribution of {metric}')
    plt.xlabel(ylabel)
    plt.ylabel('Density')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path / f'delta_{metric}_distribution_norm.png', dpi=300)
    plt.close()

# ------------------- Load Delta MAX Values (from CSV) ------------------- #
df = pd.read_csv(delta_csv)
data_max = {
    metric: {
        dataset_labels[k]: df[df['dataset'] == k][f'{metric}_max'].values
        for k in dataset_labels
    } for metric in metrics
}

# ------------------- Load TR-wise Delta from dfile_rall_delta_downsampled.1D ------------------- #
data_trwise = {metric: {'Movie I': [], 'Movie II': []} for metric in metrics}

for ds_key, ds_label in dataset_labels.items():
    base_path = dataset_paths[ds_key]
    for subj_dir in sorted(base_path.glob('sub-*')):
        dfile = subj_dir / f"{subj_dir.name}.results" / 'dfile_rall_delta_downsampled.1D'
        if dfile.exists():
            try:
                data = np.loadtxt(dfile, comments='#')
                for i, metric in enumerate(metrics):
                    data_trwise[metric][ds_label].extend(np.abs(data[:, i]))
            except Exception as e:
                print(f"Could not load {dfile}: {e}")

# ------------------- Plotting ------------------- #
for metric in metrics:
    unit = unit_labels[metric]

    # Plot TR-wise delta
    plot_normalised_hist(metric, data_trwise[metric], delta_plot_dir, unit)

    # Plot subject-wise max delta
    plot_normalised_hist(metric + '_max', data_max[metric], delta_max_dir, unit)
