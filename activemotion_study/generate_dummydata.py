import os
import nibabel as nib
import numpy as np
from scipy.ndimage import affine_transform
from scipy.spatial.transform import Rotation as R
from pathlib import Path

# path to an existing epi file (doesn't matter which, just choose one)
nifti_path = '/data/elevchenko/MinMo_movements/activemotion_study/raw_data/241031DC_nii/20035_MinMo_test_20241031_120047_241031_115636_func-bold_cond-01_movt_run-01_20241031120048_4.nii'
save_path = '/data/elevchenko/MinMo_movements/activemotion_study/dummydata/dummydata_nii'
# load the epi
print('Reading file...')
img = nib.load(nifti_path)

# the list of timestamps where you expect movement
stim_path = Path('/data/elevchenko/MinMo_movements/activemotion_study/stimuli_tent')

# get all file paths in sorted order
file_paths = sorted(stim_path.glob('condition*.1D'))
# Read lines from each file and organize them into rows in a numpy array
data_lines = []
# Open each file, read its lines, and append each line across files
for line_idx in range(sum(1 for line in open(file_paths[0]))):  # Assuming all files have the same line count
    row = [np.loadtxt(file, skiprows=line_idx, max_rows=1) for file in file_paths]
    row = np.concatenate([arr.flatten() for arr in row])
    row = sorted([int(number) for number in row])
    data_lines.append(row)

no_mvmt_stamps = len(data_lines[0])


# get the data in the epi
data = img.get_fdata()
# get the affine transform
affine = img.affine

# choose an index from the epi you want to use as a dummy,
# maybe best to get one from your input epi where the participant isn't doing anything?
vol_idx = 13
# isolate a single volume from the dataset
single_vol = data[..., vol_idx]

# get the number of volumes that the original epi was
n = data.shape[-1]

# repeat your single volume to make a totally stationary epi across time
non_moving_epi = np.repeat(single_vol[..., np.newaxis], n, axis=3)

# Add tiny random noise to the stationary data
noise_mean = 0
noise_std = 0.5  # Adjust this value to control the noise level
non_moving_epi = non_moving_epi + np.random.normal(loc=noise_mean, scale=noise_std, size=non_moving_epi.shape)

# save the non-moving epi (3 runs - MinMo condition)
for run_i in [1, 2, 3]:
    print(f'Saving stationary dummy data, run-{run_i}')
    save_path_stationary = os.path.join(save_path, f'task-movt_stationary_dummy_{run_i}.nii')
    transformed_img = nib.Nifti1Image(non_moving_epi, affine)
    nib.save(transformed_img, save_path_stationary)

# Set random seed so you can reproduce the same random values on multiple runs
np.random.seed(42)

# make a copy of the non-moving epi to manipulate
epi_to_move = non_moving_epi

# Define movement parameters

# get some random values of rotation to add to the affine at each of the time stamps you start with
# I've made it so the rotation is -2 deg to 2 deg, but you'll probably need to have a mess with these.
rotation_angles = np.random.uniform(-2, 2, size=(no_mvmt_stamps, 3))
# translations generated the same way. I think this would be in mm? But might be the size of a voxel, not sure.
translations = np.random.uniform(-1, 1, size=(no_mvmt_stamps, 3))

# Apply transformation for each time point for 3 runs
for run_i, run in enumerate(data_lines[3:], 4):
    for ts_i, timestamp in enumerate(run):

        # Create a rotation matrix
        rotation = R.from_euler('xyz', rotation_angles[ts_i], degrees=True).as_matrix()

        # Create an affine transformation matrix including translation
        affine_transform_matrix = np.eye(4)
        affine_transform_matrix[:3, :3] = rotation
        affine_transform_matrix[:3, 3] = translations[ts_i]

        # Apply the transformation to the volume
        epi_to_move[..., timestamp] = affine_transform(
            # which timestamp to move
            epi_to_move[..., timestamp],
            # Rotation component
            affine_transform_matrix[:3, :3],
            # Translation component
            offset=affine_transform_matrix[:3, 3]
        )

    # save the moving version
    print(f'Saving moving dummy data, run-{run_i}')
    save_path_move = os.path.join(save_path, f'task-movt_moving_dummy_{run_i}.nii')
    transformed_img = nib.Nifti1Image(epi_to_move, affine_transform_matrix)
    nib.save(transformed_img, save_path_move)
