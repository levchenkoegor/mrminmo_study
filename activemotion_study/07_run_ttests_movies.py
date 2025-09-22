import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind, shapiro, levene, mannwhitneyu, gaussian_kde
from statsmodels.stats.multitest import fdrcorrection
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

# Initialize a results list for descriptive statistics and p-values
descriptive_results = []
p_values = []

# Loop through each metric
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

    # KDE (optional, not plotted here)
    kde_nominmo = gaussian_kde(nominmo_series)
    kde_minmo = gaussian_kde(minmo_series)
    x_vals = np.linspace(bin_edges.min(), bin_edges.max(), 1000)

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

    # Normality test (Shapiro-Wilk)
    shapiro_nominmo = shapiro(nominmo_series)
    shapiro_minmo = shapiro(minmo_series)

    # Variance equality test (Levene's test)
    levene_test = levene(nominmo_series, minmo_series)

    # Select appropriate test based on normality and variance
    if shapiro_nominmo.pvalue > 0.05 and shapiro_minmo.pvalue > 0.05 and levene_test.pvalue > 0.05:
        t_test = ttest_ind(minmo_series, nominmo_series, alternative='less')
        test_name = "One-tailed T-test (MinMo < NoMinMo)"
        test_pvalue = t_test.pvalue
    else:
        u_test = mannwhitneyu(minmo_series, nominmo_series, alternative='less')
        test_name = "One-tailed Mann-Whitney U (MinMo < NoMinMo)"
        test_pvalue = u_test.pvalue

    # Append p-value for FDR correction
    p_values.append(test_pvalue)

    # Append descriptive statistics and test results
    descriptive_results.append({
        "metric": metric,
        "NoMinMo_mean": np.mean(nominmo_series),
        "NoMinMo_std": np.std(nominmo_series),
        "NoMinMo_median": np.median(nominmo_series),
        "NoMinMo_min": np.min(nominmo_series),
        "NoMinMo_max": np.max(nominmo_series),
        "MinMo_mean": np.mean(minmo_series),
        "MinMo_std": np.std(minmo_series),
        "MinMo_median": np.median(minmo_series),
        "MinMo_min": np.min(minmo_series),
        "MinMo_max": np.max(minmo_series),
        "normality_NoMinMo_p": shapiro_nominmo.pvalue,
        "normality_MinMo_p": shapiro_minmo.pvalue,
        "levene_p": levene_test.pvalue,
        "test": test_name,
        "test_pvalue": test_pvalue,
        "significant": False  # Placeholder, will be updated after FDR correction
    })

# Apply FDR correction
_, corrected_p_values = fdrcorrection(p_values, alpha=0.05)
for i, corrected_p in enumerate(corrected_p_values):
    descriptive_results[i]["corrected_pvalue"] = corrected_p
    descriptive_results[i]["significant"] = corrected_p < 0.05

# Convert results to a DataFrame and save as CSV
df_results = pd.DataFrame(descriptive_results).round(4)

if dummydata == 1:
    df_results.to_csv(deriv_fldr / "descriptive_statistics_movies_dummydata_with_fdr.csv", index=False)
else:
    df_results.to_csv(deriv_fldr / "descriptive_statistics_movies_with_fdr.csv", index=False)

print("Descriptive statistics and FDR-corrected test results saved.")

#
# # ==== ANOVA ====
# import pingouin as pg
#
# anova_results = []
# for metric in metrics_to_analyze:
#     # Filter and aggregate
#     df_metric = df_mot_metrics[df_mot_metrics['metric'] == metric].copy()
#     df_avg = df_metric.groupby(['subject', 'condition'])['avg_abs'].mean().reset_index()
#
#     # Run repeated measures ANOVA
#     aov = pg.rm_anova(dv='avg_abs', within='condition', subject='subject', data=df_avg, detailed=True, effsize='n2')
#
#     # Track metric
#     aov['metric'] = metric
#     anova_results.append(aov)
#
#     print(f'\nResults for {metric}:')
#     print(aov)
#
# # Save
# df_all = pd.concat(anova_results, ignore_index=True)
# df_all.round(4).to_csv(root_fldr / 'derivatives' / 'group_analysis' / 'df_anova_all_metrics_movies.csv', index=False)
