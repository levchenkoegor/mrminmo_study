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
for metric in ['mm_norm', 'mm_delt', 'dS', 'dL', 'dP', 'roll', 'pitch', 'yaw']:
        df_sub = df[(df['metric'] == metric)].copy()
        df_avg = df_sub.groupby(['subject', 'dataset'])['mean'].mean().reset_index()

        # Descriptive stats per dataset
        desc = df_avg.groupby('dataset')['mean'].agg(['mean', 'std', 'median', 'max']).reset_index()
        desc['metric'] = metric
        all_descriptives.append(desc)

        # pivot
        df_wide = df_avg.pivot_table(index='subject', columns=['dataset'], values='mean')
        df_wide = df_wide.reset_index()

        # melt into long format
        df_long = df_wide.melt(id_vars='subject', var_name='dataset', value_name='value')

        # run ANOVA
        aov = pg.anova(dv='value', between='dataset', data=df_long, detailed=True)

        # append data to then save to csv
        aov['metric'] = metric
        all_results.append(aov)

        # show the ANOVA table
        print(f'\nResults for {metric}:')
        print(aov.round(4))

# Combine and save all results
df_all = pd.concat(all_results, ignore_index=True)
df_all.round(4).to_csv(output_dir / "df_anova_motion_param_stats.csv", index=False)

# Save descriptive stats
df_descr = pd.concat(all_descriptives, ignore_index=True)
df_descr.round(2).to_csv(output_dir / "df_motion_param_descriptives.csv", index=False)