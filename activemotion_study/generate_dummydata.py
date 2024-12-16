import os
import nibabel as nib
import numpy as np
from scipy.ndimage import affine_transform
from scipy.spatial.transform import Rotation as R
from pathlib import Path

# Paths to data
nifti_path = '/data/elevchenko/MinMo_movements/activemotion_study/raw_data/241031DC_nii/20035_MinMo_test_20241031_120047_241031_115636_func-bold_cond-01_movt_run-01_20241031120048_4.nii'
save_path = '/data/elevchenko/MinMo_movements/activemotion_study/dummydata/dummydata_nii'
stim_path = Path('/data/elevchenko/MinMo_movements/activemotion_study/stimuli_tent')

# Load EPI data
print('Reading EPI file...')
img = nib.load(nifti_path)
data = img.get_fdata()
affine = img.affine
n = data.shape[-1]  # Number of volumes

# Prepare dummy stationary EPI
vol_idx = 13  # Select a volume where no motion occurred
single_vol = data[..., vol_idx]
non_moving_epi = np.repeat(single_vol[..., np.newaxis], n, axis=3)

# Add small random noise to stationary EPI
np.random.seed(42)  # For reproducibility
noise_mean = 0
noise_std = 0.5
non_moving_epi += np.random.normal(loc=noise_mean, scale=noise_std, size=non_moving_epi.shape)

# Save stationary dummy EPI for 3 runs
for run_i in range(1, 4):
    save_path_stationary = os.path.join(save_path, f'task-movt_stationary_dummy_{run_i}.nii')
    print(f'Saving stationary dummy data, run-{run_i}')
    nib.save(nib.Nifti1Image(non_moving_epi, affine), save_path_stationary)

# Load movement timestamps from .1D files
print('Loading movement timestamps...')
file_paths = sorted(stim_path.glob('condition*.1D'))
data_lines = []

n_spare_trs, tr_duration = 10, 0.8
spare_secs = int(n_spare_trs * tr_duration) # timing files don't take into account spare TRs
# (makes sense for AFNI but not for dummy data generation)

for line_idx in range(sum(1 for _ in open(file_paths[0]))):
    row = []
    for file in file_paths:
        try:
            value = np.loadtxt(file, skiprows=line_idx, max_rows=1)
            row.append(value.flatten())
        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue

    row = np.concatenate(row)
    row = sorted([int(number)+spare_secs for number in row])
    data_lines.append(row)

# Movement parameters
max_timestamps = max(len(run) for run in data_lines)
rotation_angles = np.random.uniform(-2, 2, size=(max_timestamps, 3))
translations = np.random.uniform(-1, 1, size=(max_timestamps, 3))

# Define window movements size
window_size = 5  # TR = 0.8 seconds (6 * 0.8 = 4.8)
window_volumes = int(window_size / tr_duration)  # Number of volumes in the window

for run_i, run_timestamps in enumerate(data_lines[3:], 4):
    # Reset epi_to_move for each run
    epi_to_move = non_moving_epi.copy()

    for ts_i, timestamp in enumerate(run_timestamps):
        # Convert timestamp (seconds) to TR index
        tr_index = int(round(timestamp / tr_duration))  # Round to nearest TR index

        for offset in range(window_volumes):
            vol_to_transform = tr_index + offset

            # Generate rotation and translation matrices
            rotation = R.from_euler('xyz', rotation_angles[ts_i], degrees=True).as_matrix()
            affine_transform_matrix = np.eye(4)
            affine_transform_matrix[:3, :3] = rotation
            affine_transform_matrix[:3, 3] = translations[ts_i]

            # Apply transformation
            epi_to_move[..., vol_to_transform] = affine_transform(
                non_moving_epi[..., vol_to_transform],
                matrix=affine_transform_matrix[:3, :3],
                offset=affine_transform_matrix[:3, 3],
                mode='constant',
                cval=0  # Fill missing data with 0
            )

    # Save transformed data
    save_path_move = os.path.join(save_path, f'task-movt_moving_dummy_{run_i}.nii')
    print(f'Saving moving dummy data, run-{run_i}')
    nib.save(nib.Nifti1Image(epi_to_move, affine), save_path_move)

print("Dummy data generation complete!")
