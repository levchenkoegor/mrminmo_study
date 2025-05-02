import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde

# Define paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = root_fldr / 'derivatives'
group_analysis_dir = deriv_fldr / 'group_analysis'
fig_dir_betas = group_analysis_dir / 'plots_bvalues'
fig_dir_tvals = group_analysis_dir / 'plots_tvalues'
fig_dir_betas.mkdir(parents=True, exist_ok=True)
fig_dir_tvals.mkdir(parents=True, exist_ok=True)

# Load extracted data
df = pd.read_csv(group_analysis_dir / 'df_b_t_values_selectedROIs.csv')

# Define plotting function
def plot_histograms(df, value_col, out_dir, label):
    for movement in df["movement"].unique():
        for roi in df["ROI"].unique():
            for hemi in df["hemi"].unique():
                # Filter data
                data_minmo = df[
                    (df["movement"] == movement) &
                    (df["condition"] == "MinMo") &
                    (df["ROI"] == roi) &
                    (df["hemi"] == hemi)
                ][value_col].replace([np.inf, -np.inf], np.nan).dropna()

                data_nominmo = df[
                    (df["movement"] == movement) &
                    (df["condition"] == "NoMinMo") &
                    (df["ROI"] == roi) &
                    (df["hemi"] == hemi)
                ][value_col].replace([np.inf, -np.inf], np.nan).dropna()

                if data_minmo.empty and data_nominmo.empty:
                    continue

                combined_series = pd.concat([data_nominmo, data_minmo])
                bin_edges = np.arange(combined_series.min(), combined_series.max() + 0.5, 0.5)

                # Plot histograms
                plt.figure(figsize=(10, 6))
                plt.hist(data_nominmo, bins=bin_edges, alpha=0.6, color='blue', label='NoMinMo', edgecolor='black')
                plt.hist(data_minmo, bins=bin_edges, alpha=0.6, color='orange', label='MinMo', edgecolor='black')

                # KDE smoothing
                x_vals = np.linspace(bin_edges.min(), bin_edges.max(), 1000)
                if len(data_nominmo) > 1:
                    kde_nominmo = gaussian_kde(data_nominmo)
                    plt.plot(x_vals, kde_nominmo(x_vals) * len(data_nominmo) * (bin_edges[1] - bin_edges[0]),
                             color='blue', lw=2)

                if len(data_minmo) > 1:
                    kde_minmo = gaussian_kde(data_minmo)
                    plt.plot(x_vals, kde_minmo(x_vals) * len(data_minmo) * (bin_edges[1] - bin_edges[0]),
                             color='orange', lw=2)

                plt.title(f"{label}: {movement} | ROI: {roi} | {hemi}")
                plt.xlabel(label)
                plt.ylabel("Count")
                plt.legend()
                plt.tight_layout()

                outname = f"histogram_{label}_{movement}_{roi}_{hemi}.png".replace("/", "-")
                plt.savefig(out_dir / outname, dpi=300)
                plt.close()

# Run plotting for both beta values and t-values
plot_histograms(df, 'beta_coef', fig_dir_betas, 'Beta Coefficient')
plot_histograms(df, 't_value', fig_dir_tvals, 'T-Value')

print("All histograms saved for beta coefficients and t-values.")