"""Participant-wise mean motion per dataset, one plot per metric (replaces the JMP dot plots).
Reads group_analysis/df_motion_param_stats.csv written by 06_extract_statistics.py."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

output_root = Path('group_analysis')
out_dir = output_root / 'plots_participant_means'
out_dir.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(output_root / 'df_motion_param_stats.csv', dtype={'subject': str})

DISPLAY = {'Movie II': 'MR-MinMo', 'Movie I': 'Standard padding'}   # left to right
COLORS = {'Movie I': '#2a78d6', 'Movie II': '#eb6834'}             # validated categorical slots 1-2
panels = [('mm_delt', 'Framewise displacement', 'mm'), ('mm_norm', 'Run-wise displacement', 'mm'),
          ('enorm', 'Euclidean norm framewise displacement', 'mm'),
          ('outlier_frac', 'Outlier fraction', 'fraction of voxels'),
          ('pitch', 'Pitch rotation', 'degrees'), ('roll', 'Roll rotation', 'degrees'),
          ('yaw', 'Yaw rotation', 'degrees'), ('dL', 'Left-Right translation', 'mm'),
          ('dP', 'Anterior-Posterior translation', 'mm'), ('dS', 'Inferior-Superior translation', 'mm')]

rng = np.random.default_rng(0)  # fixed jitter so reruns give the same figure
for metric, title, unit in panels:
    fig, ax = plt.subplots(figsize=(4.5, 5))
    for x, ds in enumerate(DISPLAY):
        vals = df[(df.metric == metric) & (df.dataset == ds)]['mean'].values
        ax.scatter(x + rng.uniform(-0.18, 0.18, len(vals)), vals, s=22, color=COLORS[ds],
                   edgecolor='white', linewidth=0.5, zorder=3)
        ax.hlines(np.median(vals), x - 0.28, x + 0.28, color='#0b0b0b', lw=2, zorder=4)  # median
    ax.set_xticks([0, 1], [f'{DISPLAY[ds]}\n(n = {((df.metric == metric) & (df.dataset == ds)).sum()})'
                           for ds in DISPLAY])
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylim(bottom=0)
    ax.set_title(title, fontsize=13)
    ax.set_ylabel(f'Participant mean ({unit})')
    ax.grid(True, axis='y', color='#e6e6e6', lw=0.8)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_dir / f'{metric}_participant_means.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
