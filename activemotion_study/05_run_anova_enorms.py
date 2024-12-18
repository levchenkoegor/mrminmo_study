import pingouin as pg
import pandas as pd
from pathlib import Path

# Testing hypothesis 1.2: check if have any difference movement-wise
# If so, then we will check if expected head movement associated with body movement types
# The exact associations are listed in Table 1 in prereg protocol

# Implement:
# concat unilateral trials: (right)lefthandtorighthigh -> handtothigh

# Paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = Path(root_fldr / 'derivatives')
stim_fldr = Path(root_fldr / 'stimuli')

# Read data
df_enorms = pd.read_csv(deriv_fldr / 'df_enorm_avgs.csv')

# Perform the repeated measures ANOVA
anova_results = pg.rm_anova(dv='enorm_avg', within=['condition', 'movement'], subject='subject', data=df_enorms, detailed=True)

# Display the results
print(anova_results)
