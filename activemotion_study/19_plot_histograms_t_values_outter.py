import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patheffects as path_effects
from pathlib import Path
import re

# === Setup ===
root_fldr = Path('/egor2/egor/MinMo_movements/activemotion_study')
deriv_fldr = root_fldr / 'derivatives'
group_analysis_dir = deriv_fldr / 'group_analysis'
fig_dir_grouped = group_analysis_dir / 'plots_tvalues_outter_grouped'
fig_dir_violin = group_analysis_dir / 'plots_tvalues_outter_violins'

group_analysis_dir.mkdir(exist_ok=True)
fig_dir_grouped.mkdir(parents=True, exist_ok=True)
fig_dir_violin.mkdir(parents=True, exist_ok=True)

# === Parameters ===
conditions = ["MinMo", "NoMinMo"]
movements = [
    "cough", "crosslegsleftontop", "crosslegsrightontop",
    "lefthandtorightthigh", "righthandtoleftthigh",
    "raiselefthip", "raiserighthip",
    "sayHellotheremum", "scratchleftcheek", "scratchrightcheek"
]

# === Load subjects ===
subjects = sorted([
    folder.name for folder in (deriv_fldr).iterdir()
    if folder.is_dir() and folder.name.startswith("sub-")
    and folder.name.endswith("_nii") and folder.name != "sub-dummydata_nii"
])

# === Step 1: Extract T-values ===
df_tvals = pd.DataFrame()

for subject in subjects:
    for cond in conditions:
        stats_file = deriv_fldr / subject / f"{subject}_task-mvts_cond-{cond}" / \
                     f"{subject}_task-mvts_cond-{cond}.results" / f"roistats_cond-{cond}_outter.csv"

        if not stats_file.exists():
            print(f"Missing file: {stats_file}")
            continue

        roistats = pd.read_csv(stats_file, delimiter="\t")
        roistats.columns = roistats.columns.str.strip()

        for movement in movements:
            # Match movement#X_Tstat
            regex = re.compile(fr"{movement}#\d+_Tstat")
            matching_rows = roistats[roistats['Sub-brick'].apply(lambda x: bool(regex.search(str(x))))]

            t_vals = matching_rows["Mean_1"].replace([float('inf'), float('-inf')], pd.NA).dropna()
            if not t_vals.empty:
                avg_t = t_vals.mean()
                df_tvals = pd.concat([
                    df_tvals,
                    pd.DataFrame([{
                        "subject": subject,
                        "condition": cond,
                        "movement": movement,
                        "t_value": avg_t
                    }])
                ], ignore_index=True)

# Save extracted T-values
tvals_path = group_analysis_dir / "df_t_values_outsidebrain.csv"
df_tvals.to_csv(tvals_path, index=False)
print(f"Saved T-values to: {tvals_path}")

# === Step 2: Plotting ===
for movement in sorted(df_tvals["movement"].unique()):
    data_minmo = df_tvals[(df_tvals["movement"] == movement) & (df_tvals["condition"] == "MinMo")]["t_value"].dropna()
    data_nominmo = df_tvals[(df_tvals["movement"] == movement) & (df_tvals["condition"] == "NoMinMo")]["t_value"].dropna()

    if data_minmo.empty and data_nominmo.empty:
        continue

    combined = pd.concat([data_minmo, data_nominmo])
    bin_edges = np.arange(combined.min(), combined.max() + 0.05, 0.05)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    bar_width = (bin_edges[1] - bin_edges[0]) * 0.4

    counts_minmo, _ = np.histogram(data_minmo, bins=bin_edges)
    counts_nominmo, _ = np.histogram(data_nominmo, bins=bin_edges)

    # --- Grouped Histogram ---
    plt.figure(figsize=(10, 6))
    plt.bar(bin_centers - bar_width / 2, counts_nominmo, width=bar_width, color='blue', label='NoMinMo')
    plt.bar(bin_centers + bar_width / 2, counts_minmo, width=bar_width, color='orange', label='MinMo')
    plt.plot(bin_centers, counts_nominmo, color='blue', lw=2,
             path_effects=[path_effects.withStroke(linewidth=3, foreground='black')])
    plt.plot(bin_centers, counts_minmo, color='orange', lw=2,
             path_effects=[path_effects.withStroke(linewidth=3, foreground='black')])

    plt.title(f"Distribution of T-values for {movement}")
    plt.xlabel("T-statistic")
    plt.ylabel("Count")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(fig_dir_grouped / f'grouped_tstats_{movement}.png', dpi=300)
    plt.close()
    print(f"Saved grouped bar plot: grouped_tstats_{movement}.png")

    # --- Violin Plot ---
    subset = df_tvals[df_tvals["movement"] == movement]
    plt.figure(figsize=(8, 6))
    sns.violinplot(data=subset, x="condition", y="t_value", palette=["blue", "orange"], inner=None)
    sns.stripplot(data=subset, x="condition", y="t_value", color="black", alpha=0.6, jitter=0.1)
    plt.title(f"T-Value Distribution: {movement}")
    plt.ylabel("T-statistic")
    plt.xlabel("")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(fig_dir_violin / f"violin_tstats_{movement}.png", dpi=300)
    plt.close()
    print(f"Saved violin plot: violin_tstats_{movement}.png")
