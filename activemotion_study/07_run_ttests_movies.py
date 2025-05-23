import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind, shapiro, levene, mannwhitneyu, gaussian_kde
from statsmodels.stats.multitest import fdrcorrection
from pathlib import Path
import numpy as np

# Paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
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
    bin_edges = np.arange(combined_series.min(), combined_series.max() + 0.1, 0.1)

    # Plot histograms
    plt.figure(figsize=(10, 6))
    plt.hist(nominmo_series, bins=bin_edges, alpha=0.6, color='blue', label='NoMinMo', edgecolor='black')
    plt.hist(minmo_series, bins=bin_edges, alpha=0.6, color='orange', label='MinMo', edgecolor='black')
    plt.title(f'Distribution of {metric}')
    plt.xlabel(metric)
    plt.ylabel('Count')
    plt.legend()
    plt.grid(True)

    # KDE smoothing (skip smoothing for dummydata)
    kde_nominmo = gaussian_kde(nominmo_series)
    kde_minmo = gaussian_kde(minmo_series)

    x_vals = np.linspace(bin_edges.min(), bin_edges.max(), 1000)
    plt.plot(x_vals, kde_nominmo(x_vals) * len(nominmo_series) * (bin_edges[1] - bin_edges[0]), color='blue', lw=2)
    plt.plot(x_vals, kde_minmo(x_vals) * len(minmo_series) * (bin_edges[1] - bin_edges[0]), color='orange', lw=2)

    # Save the plot
    if dummydata == 1:
        plot_output_path = deriv_fldr / f'plots_movies_dummydata/distribution_{metric}_nominmo_vs_minmo.png'
    else:
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

print("Descriptive statistics and FDR-corrected test results saved to descriptive_statistics_movies_with_fdr.csv")
