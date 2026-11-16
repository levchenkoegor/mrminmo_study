import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon
from pathlib import Path
import numpy as np
import matplotlib.patheffects as path_effects

# Paths
root_fldr = Path('/egor2/egor/MinMo_movements/activemotion_study')
deriv_fldr = Path(root_fldr / 'derivatives' / 'group_analysis')

dummydata = 0

# Read movie-watching data
if dummydata == 1:
    df_mot_metrics = pd.read_csv(deriv_fldr / 'df_motion_metrics_movies_dummydata.csv')
else:
    df_mot_metrics = pd.read_csv(deriv_fldr / 'df_motion_metrics_movies.csv')

# Metrics to analyze
metrics_to_analyze = ['mm', 'mm_delt', 'enorm', 'outliers', 'roll', 'pitch', 'yaw', 'dS', 'dL', 'dP']

# ==== Volumewise distribution plots (volumes pooled across subjects) ====
for metric in metrics_to_analyze:
    print(f"\n--- Analyzing Metric: {metric} ---\n")

    # Separate data by condition and metric
    nominmo_data = df_mot_metrics[(df_mot_metrics['condition'] == 'NoMinMo') & (df_mot_metrics['metric'] == metric)]
    minmo_data = df_mot_metrics[(df_mot_metrics['condition'] == 'MinMo') & (df_mot_metrics['metric'] == metric)]

    # Convert stringified lists into actual arrays and concatenate
    nominmo_series = np.concatenate(nominmo_data['trial'].apply(eval).to_list())
    minmo_series = np.concatenate(minmo_data['trial'].apply(eval).to_list())

    # Apply absolute value to specific metrics
    if metric in ['dL', 'dP', 'dS', 'roll', 'pitch', 'yaw']:
        nominmo_series = np.abs(nominmo_series)
        minmo_series = np.abs(minmo_series)

    # Shared binning
    combined_series = np.concatenate([nominmo_series, minmo_series])
    bin_width = 0.1
    bin_edges = np.arange(combined_series.min(), combined_series.max() + bin_width, bin_width)
    bin_centers = bin_edges[:-1] + bin_width / 2

    # Histogram counts
    nominmo_counts, _ = np.histogram(nominmo_series, bins=bin_edges)
    minmo_counts, _ = np.histogram(minmo_series, bins=bin_edges)

    # --------- Save Grouped Histogram ---------
    plt.figure(figsize=(10, 6))
    bar_width = bin_width * 0.45
    plt.bar(bin_centers - bar_width / 2, nominmo_counts, width=bar_width, color='blue', label='NoMinMo')
    plt.bar(bin_centers + bar_width / 2, minmo_counts, width=bar_width, color='orange', label='MinMo')

    # Axis labels based on metric type
    if metric in ['mm', 'mm_delt', 'dS', 'dL', 'dP', 'enorm']:
        plt.xlabel('Millimetres', fontsize=18)
    elif metric in ['roll', 'pitch', 'yaw']:
        plt.xlabel('Degrees', fontsize=18)
    elif metric == 'outliers':
        plt.xlabel('Percentages', fontsize=18)
    else:
        plt.xlabel(metric)

    plt.title(f'Distribution of {metric} metric', fontsize=22)
    plt.ylabel('Count', fontsize=18)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.legend(fontsize=18)
    plt.grid(True)

    # Line connecting peaks of bars
    plt.plot(bin_centers, nominmo_counts, color='blue', lw=2,
             path_effects=[path_effects.withStroke(linewidth=3, foreground='black')])
    plt.plot(bin_centers, minmo_counts, color='orange', lw=2,
             path_effects=[path_effects.withStroke(linewidth=3, foreground='black')])

    # Save the grouped plot
    if dummydata == 1:
        plot_grouped_path = deriv_fldr / f'plots_movies_dummydata_grouped/distribution_{metric}_grouped.png'
    else:
        plot_grouped_path = deriv_fldr / f'plots_movies_grouped/distribution_{metric}_grouped.png'
    plot_grouped_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_grouped_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Grouped bar plot saved to {plot_grouped_path}")

# ==== Paired Wilcoxon signed-rank tests on subject-wise summaries (manuscript: 'Head motion during short movies') ====
# Input: subject-wise mean/median/max of absolute values from 06_extract_motion_metrics_movies.py.
# Subjects (n = 25) are the unit of analysis.
# Reported one-tailed (preregistered: MinMo < NoMinMo), two-tailed, and one-tailed in the opposite direction.
subj_fname = "df_motion_metrics_movies_subjectwise_dummydata.csv" if dummydata == 1 \
    else "df_motion_metrics_movies_subjectwise.csv"
df_subj = pd.read_csv(deriv_fldr / subj_fname)

wilcoxon_results = []
for metric in metrics_to_analyze:
    for stat_name in ['mean', 'median', 'max']:
        wide = (df_subj[(df_subj['metric'] == metric) & (df_subj['statistic'] == stat_name)]
                .pivot(index='subject', columns='device', values='value').dropna())
        minmo, nominmo = wide['MinMo'], wide['NoMinMo']
        w_two = wilcoxon(minmo, nominmo, alternative='two-sided')
        w_one = wilcoxon(minmo, nominmo, alternative='less')
        wilcoxon_results.append({
            'metric': metric, 'statistic': stat_name, 'n': len(wide),
            'MinMo_median': minmo.median(), 'NoMinMo_median': nominmo.median(),
            'MinMo_mean': minmo.mean(), 'NoMinMo_mean': nominmo.mean(),
            'pct_reduction_mean': (nominmo.mean() - minmo.mean()) / nominmo.mean() * 100,
            'n_MinMo_lower': int((minmo < nominmo).sum()),
            'W': w_two.statistic, 'p_two_tailed': w_two.pvalue, 'p_one_tailed': w_one.pvalue,
            # exploratory, not preregistered: MinMo > NoMinMo
            'p_one_tailed_greater': wilcoxon(minmo, nominmo, alternative='greater').pvalue,
        })
wilcoxon_results = pd.DataFrame(wilcoxon_results)

wilcoxon_fname = "wilcoxon_movies_subjectwise_dummydata.csv" if dummydata == 1 else "wilcoxon_movies_subjectwise.csv"
wilcoxon_results.to_csv(deriv_fldr / wilcoxon_fname, index=False)

pd.set_option('display.width', 250)
print(wilcoxon_results.to_string(index=False, float_format=lambda x: f'{x:.4g}'))
print(f'\nThe file {wilcoxon_fname} was saved')
