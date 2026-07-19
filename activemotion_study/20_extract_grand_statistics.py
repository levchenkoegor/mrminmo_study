import pandas as pd
import numpy as np
import ast

# Load the dataset
df = pd.read_csv('/egor2/egor/MinMo_movements/activemotion_study/derivatives/group_analysis/df_motion_metrics_all.csv')

# Parse string-encoded lists
df['trial'] = df['trial'].apply(ast.literal_eval)

# Get unique metrics
unique_metrics = df['metric'].unique()

# Prepare results
results = []

for metric in unique_metrics:
    for condition in ['MinMo', 'NoMinMo']:
        avg_abs_metric = df[(df['metric'] == metric) & (df['condition'] == condition)]['avg_abs']
        results.append({
            'metric': metric,
            'condition': condition,
            'mean': np.mean(avg_abs_metric),
            'std': np.std(avg_abs_metric),
            'median': np.median(avg_abs_metric),
            'max': np.max(avg_abs_metric)
        })

# Save or display
df_metrics_stats = pd.DataFrame(results).round(2)
print(df_metrics_stats)

df_metrics_stats.to_csv('/egor2/egor/MinMo_movements/activemotion_study/derivatives/group_analysis/df_motion_descriptive_stats.csv')
