import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import ttest_ind, shapiro, levene, mannwhitneyu
from statsmodels.stats.multitest import fdrcorrection
from pathlib import Path

# Paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = Path(root_fldr / 'derivatives' / 'group_analysis')
stim_fldr = Path(root_fldr / 'stimuli')

# Read data
df_mot_metrics = pd.read_csv(deriv_fldr / 'df_motion_metrics_all.csv')

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

    for statistic in ['max', 'min', 'avg']:
        # Extract statistic
        nominmo_series = nominmo_data[statistic]
        minmo_series = minmo_data[statistic]

        # Plot histograms
        plt.figure(figsize=(10, 6))
        plt.hist(nominmo_series, bins=60, alpha=0.6, color='blue', label='NoMinMo', edgecolor='black')
        plt.hist(minmo_series, bins=60, alpha=0.6, color='orange', label='MinMo', edgecolor='black')
        plt.title(f'Distribution of {statistic} for {metric}')
        if metric in ['mm', 'mm_delt', 'dS', 'dL', 'dP', 'enorm']:
            plt.xlabel('Millimetres')
        elif metric in ['roll', 'pitch', 'yaw']:
            plt.xlabel('Degrees')
        elif metric in ['outliers']:
            plt.xlabel('Percentages')

        plt.ylabel('Count')
        plt.legend()
        plt.grid(True)

        # Save the plot
        plot_output_path = deriv_fldr / f'plots/distribution_{metric}_{statistic}_nominmo_vs_minmo.png'
        plot_output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(plot_output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Plot saved to {plot_output_path}")

        if metric in ['enorm', 'mm_delt', 'outliers']:
            # Plot histograms
            plt.figure(figsize=(10, 6))
            plt.hist(np.log1p(nominmo_series), bins=60, alpha=0.6, color='blue', label='NoMinMo', edgecolor='black')
            plt.hist(np.log1p(minmo_series), bins=60, alpha=0.6, color='orange', label='MinMo', edgecolor='black')
            plt.title(f'Distribution of {statistic} for {metric}, log transformed')
            if metric in ['mm', 'mm_delt', 'dS', 'dL', 'dP', 'enorm']:
                plt.xlabel('Millimetres')
            elif metric in ['roll', 'pitch', 'yaw']:
                plt.xlabel('Degrees')
            elif metric in ['outliers']:
                plt.xlabel('Percentages')

            plt.ylabel('Count')
            plt.legend()
            plt.grid(True)

            # Save the plot
            plot_output_path = deriv_fldr / f'plots/distribution_{metric}_{statistic}_log_transformed_nominmo_vs_minmo.png'
            plot_output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(plot_output_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Plot saved to {plot_output_path}")

    # Descriptive statistics
    nominmo_stats = nominmo_series.describe()
    minmo_stats = minmo_series.describe()

    # Calculate additional descriptive statistics
    nominmo_additional_stats = {
        "median": nominmo_series.median(),
        "min": nominmo_series.min(),
        "max": nominmo_series.max()
    }
    minmo_additional_stats = {
        "median": minmo_series.median(),
        "min": minmo_series.min(),
        "max": minmo_series.max()
    }

    # Check normality with the Shapiro-Wilk test
    shapiro_nominmo = shapiro(nominmo_series)
    shapiro_minmo = shapiro(minmo_series)

    # Check equality of variances with Levene's test
    levene_test = levene(nominmo_series, minmo_series)

    # Perform hypothesis test based on assumptions
    if shapiro_nominmo.pvalue > 0.05 and shapiro_minmo.pvalue > 0.05 and levene_test.pvalue > 0.05:
        t_test = ttest_ind(nominmo_series, minmo_series)
        test_name = "T-test"
        test_pvalue = t_test.pvalue
    else:
        u_test = mannwhitneyu(nominmo_series, minmo_series)
        test_name = "Mann-Whitney U"
        test_pvalue = u_test.pvalue

    # Append p-value for FDR correction
    p_values.append(test_pvalue)

    # Append descriptive statistics and test results
    descriptive_results.append({
        "metric": metric,
        "NoMinMo_mean": nominmo_stats["mean"],
        "NoMinMo_std": nominmo_stats["std"],
        "NoMinMo_median": nominmo_additional_stats["median"],
        "NoMinMo_min": nominmo_additional_stats["min"],
        "NoMinMo_max": nominmo_additional_stats["max"],
        "MinMo_mean": minmo_stats["mean"],
        "MinMo_std": minmo_stats["std"],
        "MinMo_median": minmo_additional_stats["median"],
        "MinMo_min": nominmo_additional_stats["min"],
        "MinMo_max": nominmo_additional_stats["max"],
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
df_results.to_csv(deriv_fldr / "descriptive_statistics_results_with_fdr.csv", index=False)

print("Descriptive statistics and FDR-corrected test results saved to descriptive_statistics_results_with_fdr.csv")
