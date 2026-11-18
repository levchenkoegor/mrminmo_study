import numpy as np
import pandas as pd
from pathlib import Path
import warnings

from run_selection import bad_subjects_movie2, run_table, keep_valid

warnings.simplefilter("ignore")

motion_param_labels = ['roll', 'pitch', 'yaw', 'dS', 'dL', 'dP']
datasets = {
    'Movie I': Path('derivatives_nndb'),
    'Movie II': Path('derivatives_btf')
}

records = []

for label, base_path in datasets.items():
    for subject in sorted(base_path.iterdir()):
        subj_id = subject.name.replace('sub-', '').zfill(2)      # zero-padded, for lookups
        afni_subj_id = subject.name.replace('sub-', '', 1)       # raw, for motion_*/outcount filenames

        if label == 'Movie II' and subj_id in bad_subjects_movie2:
            continue

        results_path = subject / f"{subject.name}.results"
        if not results_path.exists():
            continue

        runs = run_table(label, subj_id, results_path)
        if not any(valid for _, _, valid in runs):
            continue
        dropped = [run_i for run_i, _, valid in runs if not valid]
        if dropped:
            print(f"{label} sub-{subj_id}: excluded short runs {dropped}")

        # dfile_rall_norm_downsampled
        dfile = results_path / "dfile_rall_norm_downsampled.1D"
        if dfile.exists():
            try:
                data = keep_valid(np.loadtxt(dfile, comments='#'), runs)

                for i, param in enumerate(motion_param_labels):
                    param_data = np.abs(data[:, i])
                    records.append({
                        'subject': subj_id,
                        'dataset': label,
                        'metric': param,
                        'source': 'dfile',
                        'mean': round(np.mean(param_data), 4),
                        'median': round(np.median(param_data), 4),
                        'max': round(np.max(param_data), 4),
                        'min': round(np.min(param_data), 4)
                    })

            except Exception as e:
                print(f"Error loading {dfile}: {e}")

        # mm_norm and mm_delt (one file per run)
        valid_runs = {run_i for run_i, _, valid in runs if valid}
        for source_type, suffix in [('norm', 'norm_downsampled'), ('delt', 'delt_downsampled')]:
            mm_data = []
            for file in sorted(results_path.glob(f'mm.r0[0-9]*_{suffix}')):
                run_num = int(file.name.split('.')[1][1:3])
                if run_num not in valid_runs:
                    continue
                try:
                    data = np.loadtxt(file, skiprows=2)
                    data = np.abs(data)

                    if data.ndim == 2 and data.shape[1] == 1:
                        data = data[:, 0]
                    elif data.ndim == 1:
                        pass
                    else:
                        print(f"Skipping {file}: Unexpected shape {data.shape}")
                        continue

                    mm_data.append(data)
                except Exception as e:
                    print(f"Error reading {file}: {e}")

            if mm_data:
                mm_data = np.concatenate(mm_data)
                records.append({
                    'subject': subj_id,
                    'dataset': label,
                    'metric': f'mm_{source_type}',
                    'source': f'mm_{source_type}',
                    'mean': round(np.mean(mm_data), 4),
                    'median': round(np.median(mm_data), 4),
                    'max': round(np.max(mm_data), 4),
                    'min': round(np.min(mm_data), 4)
                })

        # Enorm (motion_{afni_subj_id}_enorm_downsampled.1D, produced by 03_normalize_runs.py)
        enorm_file = results_path / f'motion_{afni_subj_id}_enorm_downsampled.1D'
        if enorm_file.exists():
            try:
                enorm_data = np.abs(keep_valid(np.loadtxt(enorm_file), runs))
                records.append({
                    'subject': subj_id,
                    'dataset': label,
                    'metric': 'enorm',
                    'source': 'enorm',
                    'mean': round(np.mean(enorm_data), 4),
                    'median': round(np.median(enorm_data), 4),
                    'max': round(np.max(enorm_data), 4),
                    'min': round(np.min(enorm_data), 4)
                })

            except Exception as e:
                print(f"Error loading {enorm_file}: {e}")
        else:
            print(f"Missing: {enorm_file.name} for {subject.name}")

        # Outlier fraction (outcount_rall_downsampled.1D, produced by 03_normalize_runs.py)
        outcount_file = results_path / 'outcount_rall_downsampled.1D'
        if outcount_file.exists():
            try:
                data = keep_valid(np.loadtxt(outcount_file), runs)
                records.append({
                    'subject': subj_id,
                    'dataset': label,
                    'metric': 'outlier_frac',
                    'source': 'outcount',
                    'mean': round(np.mean(data), 4),
                    'median': round(np.median(data), 4),
                    'max': round(np.max(data), 4),
                    'min': round(np.min(data), 4)
                })

            except Exception as e:
                print(f"Error loading {outcount_file}: {e}")
        else:
            print(f"Missing: {outcount_file.name} for {subject.name}")

# Save to csv file
df = pd.DataFrame(records)
df.to_csv("group_analysis/df_motion_param_stats.csv", index=False)
