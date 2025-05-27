import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.patheffects as path_effects
from pathlib import Path

# Define paths
root_fldr = Path('/egor2/egor/MinMo_movements/activemotion_study')
deriv_fldr = root_fldr / 'derivatives' / 'group_analysis'
fig_dir_grouped = deriv_fldr / 'plots_fvalues_grouped'
fig_dir_violin = deriv_fldr / 'plots_f_values_violins'

fig_dir_grouped.mkdir(parents=True, exist_ok=True)
fig_dir_violin.mkdir(parents=True, exist_ok=True)

# Load data
df = pd.read_csv(deriv_fldr / 'df_f_values_outsidebrain.csv')

# Loop through each movement (including "ALL")
for movement in sorted(df["movement"].unique()):
    # Extract condition data
    data_minmo = df[(df["movement"] == movement) & (df["condition"] == "MinMo")]["f_value"].replace([np.inf, -np.inf], np.nan).dropna()
    data_nominmo = df[(df["movement"] == movement) & (df["condition"] == "NoMinMo")]["f_value"].replace([np.inf, -np.inf], np.nan).dropna()

    # Skip if both are empty
    if data_minmo.empty and data_nominmo.empty:
        continue

    # Shared binning
    combined = pd.concat([data_nominmo, data_minmo])
    bin_edges = np.arange(combined.min(), combined.max() + 0.5, 0.5)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    bar_width = (bin_edges[1] - bin_edges[0]) * 0.4

    # Histogram counts
    counts_nominmo, _ = np.histogram(data_nominmo, bins=bin_edges)
    counts_minmo, _ = np.histogram(data_minmo, bins=bin_edges)

    # Grouped bar plot
    plt.figure(figsize=(10, 6))
    plt.bar(bin_centers - bar_width / 2, counts_nominmo, width=bar_width, color='blue', label='NoMinMo')
    plt.bar(bin_centers + bar_width / 2, counts_minmo, width=bar_width, color='orange', label='MinMo')

    plt.plot(bin_centers, counts_nominmo, color='blue', lw=2,
             path_effects=[path_effects.withStroke(linewidth=3, foreground='black')])
    plt.plot(bin_centers, counts_minmo, color='orange', lw=2,
             path_effects=[path_effects.withStroke(linewidth=3, foreground='black')])

    plt.title(f'Distribution of F-values for {movement}')
    plt.xlabel('F-statistic')
    plt.ylabel('Count')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(fig_dir_grouped / f'grouped_fstats_{movement}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved grouped bar plot: {fig_dir_grouped / f'grouped_fstats_{movement}.png'}")

    # Violin + strip plot
    subset = df[df["movement"] == movement]
    plt.figure(figsize=(8, 6))
    sns.violinplot(data=subset, x="condition", y="f_value", palette=["blue", "orange"], inner=None)
    sns.stripplot(data=subset, x="condition", y="f_value", color="black", alpha=0.6, jitter=0.1)

    plt.title(f"F-Value Distribution: {movement}")
    plt.ylabel("F-statistic")
    plt.xlabel("")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(fig_dir_violin / f"violin_fstats_{movement}.png", dpi=300)
    plt.close()
    print(f"Saved violin plot: {fig_dir_violin / f'violin_fstats_{movement}.png'}")
