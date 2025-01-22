import pandas as pd
import matplotlib.pyplot as plt
import os
from scipy.stats import ttest_ind, shapiro, levene, mannwhitneyu
from pathlib import Path

# Paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = Path(root_fldr / 'derivatives')
stim_fldr = Path(root_fldr / 'stimuli')

# Read data
df_mot_metrics = pd.read_csv(deriv_fldr / 'df_motion_metrics_all.csv')

# Metrics to analyze
metrics_to_analyze = ['enorm', 'outliers']  # Add 'mm', 'mm_delt' when ready

# Loop through each metric
for metric in metrics_to_analyze:
    print(f"\n--- Analyzing Metric: {metric} ---\n")

    # Separate data by condition and metric
    nominmo_data = df_mot_metrics[(df_mot_metrics['condition'] == 'NoMinMo') & (df_mot_metrics['metric'] == metric)]
    minmo_data = df_mot_metrics[(df_mot_metrics['condition'] == 'MinMo') & (df_mot_metrics['metric'] == metric)]

    # Extract averages
    nominmo_series = nominmo_data['avg']
    minmo_series = minmo_data['avg']

    # Plot histograms
    plt.figure(figsize=(10, 6))
    plt.hist(nominmo_series, bins=30, alpha=0.6, color='blue', label='NoMinMo', edgecolor='black')
    plt.hist(minmo_series, bins=30, alpha=0.6, color='orange', label='MinMo', edgecolor='black')
    plt.title(f'Distribution of Averages for {metric.capitalize()}: NoMinMo vs MinMo')
    plt.xlabel('Framewise displacement (mm)')
    plt.ylabel('Count')
    plt.legend()
    plt.grid(True)

    # Make sure save folder exists
    os.makedirs(deriv_fldr / 'plots', exist_ok=True)

    # Save the plot
    output_path = f'distribution_{metric}_nominmo_vs_minmo.png'
    plt.savefig(Path(deriv_fldr / 'plots' / output_path), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Plot saved to {output_path}")

    # Descriptive statistics
    print(f"NoMinMo {metric.capitalize()} Series Statistics:")
    print(nominmo_series.describe())

    print(f"\nMinMo {metric.capitalize()} Series Statistics:")
    print(minmo_series.describe())

    # Check normality with the Shapiro-Wilk test
    shapiro_nominmo = shapiro(nominmo_series)
    shapiro_minmo = shapiro(minmo_series)

    print(f"\nShapiro-Wilk test for NoMinMo {metric} normality p-value: {shapiro_nominmo.pvalue}")
    print(f"Shapiro-Wilk test for MinMo {metric} normality p-value: {shapiro_minmo.pvalue}")

    # Check equality of variances with Levene's test
    levene_test = levene(nominmo_series, minmo_series)
    print(f"\nLevene's test for equal variances of {metric} p-value: {levene_test.pvalue}")

    # Perform hypothesis test based on assumptions
    if shapiro_nominmo.pvalue > 0.05 and shapiro_minmo.pvalue > 0.05 and levene_test.pvalue > 0.05:
        t_test = ttest_ind(nominmo_series, minmo_series)
        print(f"\nT-test for {metric} p-value: {t_test.pvalue}")
        if t_test.pvalue < 0.05:
            print(f"There is a significant difference between NoMinMo and MinMo for {metric} (p < 0.05).")
        else:
            print(f"There is no significant difference between NoMinMo and MinMo for {metric} (p >= 0.05).")
    else:
        u_test = mannwhitneyu(nominmo_series, minmo_series)
        print(f"\nMann-Whitney U test for {metric} p-value: {u_test.pvalue}")
        if u_test.pvalue < 0.05:
            print(f"There is a significant difference between NoMinMo and MinMo distributions for {metric} (p < 0.05).")
        else:
            print(
                f"There is no significant difference between NoMinMo and MinMo distributions for {metric} (p >= 0.05).")
