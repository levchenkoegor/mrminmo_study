import pingouin as pg
import pandas as pd
from pathlib import Path

# Testing hypothesis 1.2: less head position change evoked by each type of body movement when
# MinMo is used, compared to when standard cushions are used


# Paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = Path(root_fldr / 'derivatives')
stim_fldr = Path(root_fldr / 'stimuli')

# Read data
df_enorms = pd.read_csv(deriv_fldr / 'df_enorm_avgs.csv')

# Generalize movement types
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

# Create a new column for generalized movement types
df_enorms['movement_general'] = df_enorms['movement'].replace(movement_mapping)

# Perform the repeated measures ANOVA using the generalized movement column
anova_results = pg.rm_anova(
    dv='enorm_avg',
    within=['condition', 'movement_general'],
    subject='subject',
    data=df_enorms,
    detailed=True
)

print("\nRepeated Measures ANOVA Results:")
print(anova_results)