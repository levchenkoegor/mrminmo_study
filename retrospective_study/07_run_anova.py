import pandas as pd
import pingouin as pg
from pathlib import Path

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="pingouin")

# Load the CSV
df = pd.read_csv("group_analysis/df_motion_param_stats.csv")

# Where to save results
output_dir = Path("group_analysis")
output_dir.mkdir(exist_ok=True)

# Store all ANOVA results here
all_results = []

# Store descriptive stats here
all_descriptives = []

# Loop through all combinations of source and param
for metric in ['mm_norm', 'mm_delt', 'dS', 'dL', 'dP', 'roll', 'pitch', 'yaw', 'enorm', 'outlier_frac']:
    for stat in ['mean', 'median', 'max']:
        df_sub = df[df['metric'] == metric].copy()
        df_avg = df_sub.groupby(['subject', 'dataset'])[stat].mean().reset_index()

        # Descriptive stats per dataset
        desc = df_avg.groupby('dataset')[stat].agg(['mean', 'std', 'median', 'max']).reset_index()
        desc['metric'] = metric
        desc['stat'] = stat
        all_descriptives.append(desc)

        # pivot and melt
        df_wide = df_avg.pivot_table(index='subject', columns='dataset', values=stat)
        df_wide = df_wide.reset_index()
        df_long = df_wide.melt(id_vars='subject', var_name='dataset', value_name='value')
        df_long = df_long.dropna(subset=['value'])

        # run ANOVA
        aov = pg.anova(dv='value', between='dataset', data=df_long, detailed=True)
        aov['metric'] = metric
        aov['stat'] = stat
        all_results.append(aov)

        print(f'\nResults for {metric} ({stat}):')
        print(aov.round(6))

# Combine and save all results
df_all = pd.concat(all_results, ignore_index=True)
df_all.round(6).to_csv(output_dir / "df_anova_motion_param_stats.csv", index=False)

# Save descriptive stats
df_descr = pd.concat(all_descriptives, ignore_index=True)
df_descr.round(2).to_csv(output_dir / "df_motion_param_descriptives.csv", index=False)