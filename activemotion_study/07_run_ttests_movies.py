import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind, shapiro, levene, mannwhitneyu
from statsmodels.stats.multitest import fdrcorrection
from pathlib import Path
import numpy as np

# Paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = Path(root_fldr / 'derivatives' / 'group_analysis')

# Read movie-watching data
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

    nominmo_series = np.concatenate(nominmo_data['trial'].apply(eval).values)
    minmo_series = np.concatenate(minmo_data['trial'].apply(eval).values)

    # Plot histograms
    plt.figure(figsize=(10, 6))
    plt.hist(nominmo_series, bins=60, alpha=0.6, color='blue', label='NoMinMo', edgecolor='black')
    plt.hist(minmo_series, bins=60, alpha=0.6, color='orange', label='MinMo', edgecolor='black')
    plt.title(f'Distribution of {metric}')
    plt.xlabel(metric)
    plt.ylabel('Count')
    plt.legend()
    plt.grid(True)

    # Save the plot
    plot_output_path = deriv_fldr / f'plots_movies/distribution_{metric}_nominmo_vs_minmo.png'
    plot_output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Plot saved to {plot_output_path}")

    # Normality test (Shapiro-Wilk)
    shapiro_nominmo = shapiro(nominmo_series)
    shapiro_minmo = shapiro(minmo_series)

    # Variance equality test (Levene's test)
    levene_test = levene(nominmo_series, minmo_series)

    # Select appropriate test based on normality and variance
    if shapiro_nominmo.pvalue > 0.05 and shapiro_minmo.pvalue > 0.05 and levene_test.pvalue > 0.05:
        t_test = ttest_ind(minmo_series, nominmo_series, alternative='less')
        test_name = "One-tailed T-test (MinMo < NoMinMo)"
    else:
        u_test = mannwhitneyu(minmo_series, nominmo_series, alternative='less')
        test_name = "One-tailed Mann-Whitney U (MinMo < NoMinMo)"

    test_pvalue = test_result.pvalue
    p_values.append(test_pvalue)

    # Append descriptive statistics and test results
    descriptive_results.append({
        "metric": metric,
        "NoMinMo_mean": np.mean(nominmo_series),
        "NoMinMo_std": np.std(nominmo_series),
        "MinMo_mean": np.mean(minmo_series),
        "MinMo_std": np.std(minmo_series),
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
df_results.to_csv(deriv_fldr / "descriptive_statistics_movies_with_fdr.csv", index=False)

print("Descriptive statistics and FDR-corrected test results saved to descriptive_statistics_movies_with_fdr.csv")
