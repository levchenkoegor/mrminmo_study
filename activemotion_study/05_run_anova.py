import pandas as pd
import pingouin as pg
from pathlib import Path

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="pingouin")

# Load the dataset
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
file_path = Path(root_fldr / 'derivatives' / 'group_analysis' / 'df_motion_metrics_all.csv')
df = pd.read_csv(file_path)

# Add this before the loop
all_results = []

# Define movement grouping
movement_mapping = {
    'lefthandtorightthigh': 'HandToThigh',
    'righthandtoleftthigh': 'HandToThigh',
    'scratchleftcheek': 'ScratchCheek',
    'scratchrightcheek': 'ScratchCheek',
    'crosslegsleftontop': 'XLeg',
    'crosslegsrightontop': 'XLeg',
    'raiselefthip': 'RaiseHip',
    'raiserighthip': 'RaiseHip',
    'sayHellotheremum': 'Hello',
    'cough': 'cough'
}

for metric in ['enorm', 'mm', 'mm_delt', 'outliers', 'dS', 'dL', 'dP', 'roll', 'pitch', 'yaw']:
    # Subset and process the data
    df_metric = df[df['metric'] == metric].copy()
    df_metric['movement_type'] = df_metric['movement'].replace(movement_mapping)
    df_avg = df_metric.groupby(['subject', 'condition', 'movement_type'])['avg_abs'].mean().reset_index()

    # Pivot
    df_wide = df_avg.pivot_table(index='subject', columns=['condition', 'movement_type'], values='avg_abs')
    df_wide = df_wide.reset_index()

    # Flatten the MultiIndex columns (e.g., ('MinMo', 'Hello') -> 'MinMo_Hello')
    df_wide.columns = ['subject'] + [f'{c}_{m}' for c, m in df_wide.columns[1:]]

    # Melt into long format
    df_long = df_wide.melt(id_vars='subject', var_name='condition_movement', value_name='value')

    # Split the combined condition_movement column back into two
    df_long[['condition', 'movement']] = df_long['condition_movement'].str.split('_', expand=True)

    # drop the temporary column
    df_long = df_long.drop(columns='condition_movement')
    #df_long.to_csv(root_fldr / 'derivatives' / 'group_analysis' / 'forJASP_{metric}.csv', index=False)

    # run repeated measures ANOVA
    aov = pg.rm_anova(dv='value', within=['condition', 'movement'], subject='subject', data=df_long, detailed=True)

    # append data to then save to csv
    aov['metric'] = metric
    all_results.append(aov)

    # show the ANOVA table
    print(f'\nResults for {metric}:')
    print(aov)

# after the loop finishes
df_all = pd.concat(all_results, ignore_index=True)
df_all.round(4).to_csv(root_fldr / 'derivatives' / 'group_analysis' / 'anova_all_metrics.csv', index=False)
