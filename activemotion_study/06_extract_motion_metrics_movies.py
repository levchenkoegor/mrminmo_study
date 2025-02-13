import numpy as np
import pandas as pd
from pathlib import Path

# Function to load motion data

def load_motion_data(motion_file, skip_lines=0):
    """
    Load motion data from file, skipping specified number of lines.
    """
    if not motion_file.exists():
        print(f"Motion file not found: {motion_file.name}. Skipping...")
        return None

    with open(motion_file, 'r') as file:
        lines = file.readlines()[skip_lines:]
        motion_data = np.array([list(map(float, line.strip().split())) for line in lines])
    return motion_data

# Paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = Path(root_fldr / 'derivatives')

# Load subject list
sequence_file = Path(root_fldr / 'Sequences of conditions and runs.csv')
sequence_df = pd.read_csv(sequence_file)

subjects = sequence_df[sequence_df['Subj #'] != 'dummydata_nii']['Subj #']

# Results list
results = []

# Process each subject and condition
for subj_id in subjects:
    for condition in ['MinMo', 'NoMinMo']:
        cond_folder = Path(deriv_fldr / f'sub-{subj_id}/sub-{subj_id}_task-movies_cond-{condition}/sub-{subj_id}_task-movies_cond-{condition}.results')

        # Define metric files
        metric_files = {
            "enorm": (cond_folder / f"motion_{subj_id}_enorm.1D", 0),
            "mm": (cond_folder / "mm.r01", 2),  # Skip first 2 lines
            "mm_delt": (cond_folder / "mm.r01_delt", 2),  # Skip first 2 lines
            "outliers": (cond_folder / "outcount_rall.1D", 0),
            "dfile": (cond_folder / "dfile_rall.1D", 0),
        }

        # Process each metric
        for metric_name, (motion_file, skip_lines) in metric_files.items():
            motion_data = load_motion_data(motion_file, skip_lines)
            if motion_data is None:
                continue

            if metric_name == "dfile":
                # Extract six motion parameters
                motion_params = ["roll", "pitch", "yaw", "dS", "dL", "dP"]
                for col_idx, param in enumerate(motion_params):
                    avg = np.mean(motion_data[:, col_idx])
                    results.append({
                        "subject": subj_id,
                        "condition": condition,
                        "metric": param,
                        "trial": motion_data[:, col_idx].tolist(),
                        "N": len(motion_data[:, col_idx]),
                        "avg": avg,
                        "med": np.median(motion_data[:, col_idx]),
                        "max": np.max(motion_data[:, col_idx]),
                        "min": np.min(motion_data[:, col_idx])
                    })
            else:
                avg = np.mean(motion_data[:, 0])
                results.append({
                    "subject": subj_id,
                    "condition": condition,
                    "metric": metric_name,
                    "trial": motion_data[:, 0].tolist(),
                    "N": len(motion_data[:, 0]),
                    "avg": avg,
                    "med": np.median(motion_data[:, 0]),
                    "max": np.max(motion_data[:, 0]),
                    "min": np.min(motion_data[:, 0])
                })

# Save to CSV
df = pd.DataFrame(results)
(deriv_fldr / 'group_analysis').mkdir(parents=True, exist_ok=True)
df.to_csv(deriv_fldr / 'group_analysis'/ "df_motion_metrics_movies.csv", index=False)
print("Metrics saved to df_motion_metrics_movies.csv")
