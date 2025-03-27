import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import numpy as np

# Define paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = root_fldr / 'derivatives'
group_analysis_dir = deriv_fldr / 'group_analysis'
fig_dir = group_analysis_dir / 'plots_beta_coeffs'
fig_dir.mkdir(parents=True, exist_ok=True)

# Load extracted betas
df_betas_rois = pd.read_csv(group_analysis_dir / 'df_betas_selectedROIs.csv')

# Loop over combinations
for movement in df_betas_rois["movement"].unique():
    for roi in df_betas_rois["ROI"].unique():
        for hemi in df_betas_rois["hemi"].unique():
            # Filter data
            data_minmo = df_betas_rois[
                (df_betas_rois["movement"] == movement) &
                (df_betas_rois["condition"] == "MinMo") &
                (df_betas_rois["ROI"] == roi) &
                (df_betas_rois["hemi"] == hemi)
            ]["beta_coef"].replace([np.inf, -np.inf], np.nan).dropna()

            data_nominmo = df_betas_rois[
                (df_betas_rois["movement"] == movement) &
                (df_betas_rois["condition"] == "NoMinMo") &
                (df_betas_rois["ROI"] == roi) &
                (df_betas_rois["hemi"] == hemi)
            ]["beta_coef"].replace([np.inf, -np.inf], np.nan).dropna()

            # Skip empty plots
            if data_minmo.empty and data_nominmo.empty:
                continue

            # Use shared bins across both conditions
            combined = pd.concat([data_minmo, data_nominmo])
            bins = np.histogram_bin_edges(combined, bins=20)
            bin_centers = 0.5 * (bins[:-1] + bins[1:])

            # Compute % hist for each condition
            counts_minmo, _ = np.histogram(data_minmo, bins=bins)
            perc_minmo = 100 * counts_minmo / counts_minmo.sum() if counts_minmo.sum() > 0 else np.zeros_like(counts_minmo)

            counts_nominmo, _ = np.histogram(data_nominmo, bins=bins)
            perc_nominmo = 100 * counts_nominmo / counts_nominmo.sum() if counts_nominmo.sum() > 0 else np.zeros_like(counts_nominmo)

            # Plot
            plt.figure(figsize=(8, 5))
            plt.bar(bin_centers - 0.2, perc_minmo, width=0.4, label="MinMo",
                    color="tab:blue", alpha=0.7, edgecolor='black')
            plt.bar(bin_centers + 0.2, perc_nominmo, width=0.4, label="NoMinMo",
                    color="tab:orange", alpha=0.7, edgecolor='black')

            plt.title(f"Beta Coefficient: {movement} | ROI: {roi} | {hemi}")
            plt.xlabel("Beta Coefficient")
            plt.ylabel("Percentage (%)")
            plt.legend()
            plt.tight_layout()

            outname = f"histogram_{movement}_{roi}_{hemi}.png".replace("/", "-")
            plt.savefig(fig_dir / outname, dpi=300)
            plt.close()

print("All histograms saved.")
