import os
import nibabel as nib
import numpy as np
from scipy.ndimage import affine_transform
from scipy.spatial.transform import Rotation as R

# Paths
nifti_path = '/data/elevchenko/MinMo_movements/activemotion_study/raw_data/241031DC_nii/20035_MinMo_test_20241031_120047_241031_115636_func-bold_cond-01_film_run-01_20241031120048_16.nii.gz'
save_path = '/data/elevchenko/MinMo_movements/activemotion_study/dummydata/dummydata_nii'

# Load EPI
print('Reading EPI file...')
img = nib.load(nifti_path)
data = img.get_fdata()
affine = img.affine
n_vols = data.shape[-1]

# Create stationary base
vol_idx = 13
single_vol = data[..., vol_idx]
non_moving_epi = np.repeat(single_vol[..., np.newaxis], n_vols, axis=3)

# Add noise
np.random.seed(42)
non_moving_epi += np.random.normal(loc=0, scale=0.5, size=non_moving_epi.shape)

# Save stationary dummy movie
nib.save(nib.Nifti1Image(non_moving_epi, affine), os.path.join(save_path, 'task-film_stationary_dummy_1.nii'))

# --- Simulate low-frequency involuntary motion ---
# Sparse motion events (e.g., every ~20 TRs)
tr_duration = 0.8
motion_every_n_trs = 20
window_size_secs = 4
window_vols = int(window_size_secs / tr_duration)

# Generate motion timestamps
motion_timestamps = list(range(10, n_vols - window_vols, motion_every_n_trs))
rotation_angles = np.random.uniform(-2, 2, size=(len(motion_timestamps), 3))
translations = np.random.uniform(-1, 1, size=(len(motion_timestamps), 3))

epi_to_move = non_moving_epi.copy()

for i, tr_start in enumerate(motion_timestamps):
    for offset in range(window_vols):
        vol_idx = tr_start + offset
        if vol_idx >= n_vols:
            continue

        # Apply motion
        rot = R.from_euler('xyz', rotation_angles[i], degrees=True).as_matrix()
        aff_mat = np.eye(4)
        aff_mat[:3, :3] = rot
        aff_mat[:3, 3] = translations[i]

        epi_to_move[..., vol_idx] = affine_transform(
            non_moving_epi[..., vol_idx],
            matrix=aff_mat[:3, :3],
            offset=aff_mat[:3, 3],
            mode='constant',
            cval=0
        )

# Save moving dummy data
nib.save(nib.Nifti1Image(epi_to_move, affine), os.path.join(save_path, 'task-film_moving_dummy_2.nii'))

print("Dummy passive movie data generation complete!")
