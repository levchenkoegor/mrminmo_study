import numpy as np
import pandas as pd
import pingouin as pg
from pathlib import Path

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="pingouin")

# Load the CSV
df = pd.read_csv("group_analysis/df_motion_param_stats.csv", dtype={"subject": str})

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


# One-tailed Welch t-tests (NoMinMo > MinMo) on participant-wise summary stats.

metrics = ['dL', 'dP', 'dS', 'pitch', 'roll', 'yaw', 'mm_norm', 'mm_delt', 'enorm', 'outlier_frac']
outlier_rows = {('mm_delt', 'max'), ('enorm', 'max')}
rows = []
for metric in metrics:
    for stat in ['median', 'mean', 'max']:
        d = df[df.metric == metric].groupby(['dataset', 'subject'])[stat].mean()
        nominmo, minmo = d['Movie I'], d['Movie II']
        if (metric, stat) in outlier_rows:
            nominmo = nominmo.drop('54')
        t = pg.ttest(nominmo, minmo, correction=True, alternative='greater')
        n1, n2 = len(nominmo), len(minmo)
        diff = nominmo.mean() - minmo.mean()
        g_star = (1 - 3 / (4 * (n1 + n2) - 9)) * diff / np.sqrt((nominmo.var() + minmo.var()) / 2)
        rows.append({'metric': metric, 'stat': stat, 'n_nominmo': n1, 'n_minmo': n2,
                     't': t['T'].iloc[0], 'df': t['dof'].iloc[0], 'p_one_tailed': t['p-val'].iloc[0],
                     'hedges_g_star': g_star, 'pct_less_with_minmo': 100 * diff / nominmo.mean()})

res = pd.DataFrame(rows)
# Optional FDR (BH) across the six translation/rotation parameters, per summary statistic
six = res.metric.isin(['dL', 'dP', 'dS', 'pitch', 'roll', 'yaw'])
res['p_fdr_six'] = np.nan
for stat in ['median', 'mean', 'max']:
    m = six & (res.stat == stat)
    res.loc[m, 'p_fdr_six'] = pg.multicomp(res.loc[m, 'p_one_tailed'].values, method='fdr_bh')[1]

# Self-check: g* and Welch t share the mean difference, so their signs must agree.
# (Before sub-36's short run was dropped, this script reproduced draft 260625 Table 3 exactly.)
assert (np.sign(res['t']) == np.sign(res['hedges_g_star'])).all()

res.round(6).to_csv('group_analysis/df_welch_motion_param_stats.csv', index=False)
print(res.round(4).to_string(index=False))

# Manuscript Table 3: same layout and rounding as the draft table
names = {'dL': 'Translation: Left-Right', 'dP': 'Translation: Anterior-Posterior',
         'dS': 'Translation: Inferior-Superior', 'pitch': 'Rotation: Pitch', 'roll': 'Rotation: Roll',
         'yaw': 'Rotation: Yaw', 'mm_norm': 'Runwise maximum displacement',
         'mm_delt': 'Framewise maximum displacement', 'enorm': 'Euclidean norm framewise displacement',
         'outlier_frac': 'Outliers'}
table3 = pd.DataFrame({
    'Metric': res.metric.map(names).where(res.stat == 'median', ''),  # name once per group, as in the draft
    'Statistic': res.stat,
    't': res.t.map('{:.2f}'.format), 'df': res.df.map('{:.2f}'.format),
    'p value': res.p_one_tailed.map('{:.6f}'.format),
    "Hedges' g": res.hedges_g_star.map('{:.4f}'.format),
    '% less movement with MinMo': res.pct_less_with_minmo.map('{:.1f}%'.format)})
table3.to_csv(output_dir / 'table3_welch.csv', index=False)
