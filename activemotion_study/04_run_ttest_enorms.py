import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind, shapiro, levene, mannwhitneyu
from pathlib import Path

# Testing hypothesis 1.1:
# Significantly less head position change in the MinMo condition relative to the NoMinMo condition

# Paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = Path(root_fldr / 'derivatives')
stim_fldr = Path(root_fldr / 'stimuli')

# Read data
df_enorms = pd.read_csv(deriv_fldr / 'df_enorm_avgs.csv')

# Separate data for MinMo and NoMinMo
nominmo_series = df_enorms[df_enorms['condition'] == 'NoMinMo']['enorm_avg']
minmo_series = df_enorms[df_enorms['condition'] == 'MinMo']['enorm_avg']

# Plot histograms using matplotlib
plt.figure(figsize=(10, 6))

# Histogram for NoMinMo
plt.hist(nominmo_series, bins=30, alpha=0.6, color='blue', label='NoMinMo', edgecolor='black')
# Histogram for MinMo
plt.hist(minmo_series, bins=30, alpha=0.6, color='orange', label='MinMo', edgecolor='black')

# Add title and labels
plt.title('Distribution of Averages: NoMinMo vs MinMo')
plt.xlabel('Average of 5 seconds post-onset')
plt.ylabel('Count')

# Add legend and grid
plt.legend()
plt.grid(True)

output_path = 'distribution_enorms_nominmo_vs_minmo.png'
plt.savefig(Path(deriv_fldr / output_path), dpi=300, bbox_inches='tight')
print(f"Plot saved to {output_path}")

# Print descriptive statistics
print("NoMinMo Series Statistics:")
print(nominmo_series.describe())

print("\nMinMo Series Statistics:")
print(minmo_series.describe())


# Check normality with the Shapiro-Wilk test
shapiro_nominmo = shapiro(nominmo_series)
shapiro_minmo = shapiro(minmo_series)

print(f"\nShapiro-Wilk test for NoMinMo normality p-value: {shapiro_nominmo.pvalue}")
if shapiro_nominmo.pvalue > 0.05:
    print("The NoMinMo series appears to follow a normal distribution (p > 0.05).")
else:
    print("The NoMinMo series does not follow a normal distribution (p <= 0.05).")

print(f"\nShapiro-Wilk test for MinMo normality p-value: {shapiro_minmo.pvalue}")
if shapiro_minmo.pvalue > 0.05:
    print("The MinMo series appears to follow a normal distribution (p > 0.05).")
else:
    print("The MinMo series does not follow a normal distribution (p <= 0.05).")

# Check equality of variances with Levene's test
levene_test = levene(nominmo_series, minmo_series)
print(f"\nLevene's test for equal variances p-value: {levene_test.pvalue}")
if levene_test.pvalue > 0.05:
    print("The variances between NoMinMo and MinMo appear equal (p > 0.05).")
else:
    print("The variances between NoMinMo and MinMo are not equal (p <= 0.05).")

# Perform t-test if normality and equal variance assumptions hold
if shapiro_nominmo.pvalue > 0.05 and shapiro_minmo.pvalue > 0.05 and levene_test.pvalue > 0.05:
    t_test = ttest_ind(nominmo_series, minmo_series)
    print(f"\nT-test p-value: {t_test.pvalue}")
    if t_test.pvalue < 0.05:
        print("There is a significant difference between NoMinMo and MinMo averages (p < 0.05).")
    else:
        print("There is no significant difference between NoMinMo and MinMo averages (p >= 0.05).")
else:
    # If assumptions are violated, perform a non-parametric test
    u_test = mannwhitneyu(nominmo_series, minmo_series)
    print(f"\nMann-Whitney U test p-value: {u_test.pvalue}")
    if u_test.pvalue < 0.05:
        print("There is a significant difference between NoMinMo and MinMo distributions (p < 0.05).")
    else:
        print("There is no significant difference between NoMinMo and MinMo distributions (p >= 0.05).")
