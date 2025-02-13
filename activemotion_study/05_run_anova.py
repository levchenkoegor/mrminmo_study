import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols
from pathlib import Path

# Load the dataset
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
file_path = Path(root_fldr / 'derivatives' / 'group_analysis' / 'df_motion_metrics_all.csv')
df = pd.read_csv(file_path)

# Define movement generalization mapping
movement_mapping = {
    'lefthandtorightthigh': 'handtothigh',
    'righthandtoleftthigh': 'handtothigh',
    'scratchleftcheek': 'scratchcheek',
    'scratchrightcheek': 'scratchcheek',
    'crosslegsleftontop': 'crosslegs',
    'crosslegsrightontop': 'crosslegs',
    'raiselefthip': 'raisehip',
    'raiserighthip': 'raisehip'
}

# Convert categorical variables
df['subject'] = df['subject'].astype('category')
df['condition'] = df['condition'].astype('category')
df['movement_type'] = df['movement'].replace(movement_mapping).astype('category')

# Ensure numerical variables are correctly formatted
df['value'] = pd.to_numeric(df['avg'], errors='coerce')  # The column holding actual movement values

# List of movement metrics to analyze
metrics = {'enorm': 'Head Movement Magnitude', 'mm_delt': 'Displacement', 'outliers': 'Number of Outlier Volumes'}

# Dictionary to store ANOVA results
anova_results = {}

# Run ANOVA for each movement metric
for metric, metric_label in metrics.items():
    df_subset = df[df['metric'] == metric].dropna()  # Filter dataset for the specific metric

    # Fit the model
    model = ols(f"value ~ C(condition) * C(movement_type) + C(subject)", data=df_subset).fit()

    # Run ANOVA
    anova_results[metric] = sm.stats.anova_lm(model, typ=2)

# Print ANOVA results for each metric
for metric, result in anova_results.items():
    print(f"\nANOVA Results for {metrics[metric]}:")
    print(result)
