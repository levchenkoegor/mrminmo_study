import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

# Setup
output_fldr = Path('/egor2/egor/MinMo_movements/retrospective_study/group_analysis')
(output_fldr / 'plots_motion_params').mkdir(parents=True)

datasets = {
    'BTF': Path('derivatives_btf'),
    'NNDB': Path('derivatives_nndb')
}
motion_param_labels = ['roll', 'pitch', 'yaw', 'dS', 'dL', 'dP']  # AFNI order
motion_param_colors = ['blue', 'green', 'red', 'purple', 'orange', 'brown']

# Collect data
displacement = defaultdict(list)
motion_params = defaultdict(lambda: defaultdict(list))  # dataset -> param -> values

for label, base_path in datasets.items():
    for subject in base_path.iterdir():
        results_path = subject / f"{subject.name}.results"
        if not results_path.exists():
            continue

        # ---- 1. Collect max displacement values ----
        for file in sorted(results_path.glob('mm.r0*_norm')):
            try:
                data = np.loadtxt(file, skiprows=2)
                displacement[label].extend(data)
            except Exception as e:
                print(f"Could not load {file}: {e}")

        # ---- 2. Collect 6 motion parameters ----
        dfile = results_path / 'dfile_rall_norm.1D'
        if dfile.exists():
            try:
                data = np.loadtxt(dfile, comments='#')
                for i, param in enumerate(motion_param_labels):
                    motion_params[label][param].extend(data[:, i])
            except Exception as e:
                print(f"Could not load {dfile}: {e}")

# ---- 3. Plot: Maximum displacement ----
plt.figure(figsize=(8, 5))
for label in datasets:
    plt.hist(displacement[label], bins=100, alpha=0.6, label=label, density=True)
plt.title("Histogram of Maximum Displacement")
plt.xlabel("Displacement (mm)")
plt.ylabel("Density")
plt.legend()
plt.tight_layout()
plt.savefig(output_fldr / "plots_motion_params/max_displacement_histogram.png")
plt.close()

# ---- 4. Plot: 6 motion parameters ----
for i, param in enumerate(motion_param_labels):
    plt.figure(figsize=(8, 5))
    for label in datasets:
        plt.hist(motion_params[label][param], bins=100, alpha=0.6, label=label, density=True)
    plt.title(f"Histogram of Motion Parameter: {param}")
    plt.xlabel("Displacement (mm or radians)")
    plt.ylabel("Density")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_fldr / 'plots_motion_params' / f"{param}_histogram.png")
    plt.close()
