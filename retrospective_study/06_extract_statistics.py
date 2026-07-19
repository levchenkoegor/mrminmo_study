import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
import warnings

warnings.simplefilter("ignore")

motion_param_labels = ['roll', 'pitch', 'yaw', 'dS', 'dL', 'dP']
datasets = {
    'Movie I': Path('derivatives_nndb'),
    'Movie II': Path('derivatives_btf')
}
bad_subjects_movie2 = ['03', '07', '24', '37', '39', '43']
run_info = pd.read_csv('run_lengths.csv')
valid_nndb_runs = run_info[(run_info['dataset'] == 'NNdb') & (run_info['n_trs'] >= 600)]

# Dict: subject -> valid run indices
valid_run_indices = defaultdict(list)
for _, row in valid_nndb_runs.iterrows():
    subj = str(row['subject']).zfill(2)
    valid_run_indices[subj].append(int(row['run_i']))

records = []

for label, base_path in datasets.items():
    for subject in sorted(base_path.iterdir()):
        subj_id = subject.name.replace('sub-', '').zfill(2)      # zero-padded, for lookups
        afni_subj_id = subject.name.replace('sub-', '', 1)       # raw, for motion_*/outcount filenames

        if label == 'Movie II' and subj_id in bad_subjects_movie2:
            continue
        if label == 'Movie I' and subj_id not in valid_run_indices:
            continue

        results_path = subject / f"{subject.name}.results"
        if not results_path.exists():
            continue

        # dfile_rall_norm_downsampled
        dfile = results_path / "dfile_rall_norm_downsampled.1D"
        if dfile.exists():
            try:
                data = np.loadtxt(dfile, comments='#')
                if label == 'Movie I':
                    all_runs = run_info[
                        (run_info['dataset'] == 'NNdb') &
                        (run_info['subject'] == int(subj_id))
                    ].sort_values(by='run_i')

                    tr_start = 0
                    valid_trs = []
                    for _, row in all_runs.iterrows():
                        run_i = int(row['run_i'])

                        # Use downsampled TR count from mm_norm_downsampled file,
                        # not full-res count from run_lengths.csv, because dfile is
                        # already downsampled and slicing with full-res counts would
                        # mis-align all runs after the first.
                        mm_file = results_path / f'mm.r{str(run_i).zfill(2)}_norm_downsampled'
                        if not mm_file.exists():
                            print(f"Warning: missing {mm_file.name} for sub-{subj_id}, skipping run {run_i}")
                            continue
                        tr_count_ds = len(np.loadtxt(mm_file, skiprows=2))

                        if run_i in valid_run_indices[subj_id]:
                            end = tr_start + tr_count_ds
                            valid_trs.append(data[tr_start:end])
                        tr_start += tr_count_ds

                    if not valid_trs:
                        continue
                    data = np.concatenate(valid_trs, axis=0)

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

        # mm_norm and mm_delt
        for source_type, suffix in [('norm', 'norm_downsampled'), ('delt', 'delt_downsampled')]:
            mm_data = []
            for file in sorted(results_path.glob(f'mm.r0[0-9]*_{suffix}')):
                run_num = int(file.name.split('.')[1][1:3])
                if label == 'Movie I' and run_num not in valid_run_indices[subj_id]:
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

        # NEW: Enorm (motion_{afni_subj_id}_enorm_downsampled.1D, produced by 03_normalize_runs.py)
        enorm_file = results_path / f'motion_{afni_subj_id}_enorm_downsampled.1D'
        if enorm_file.exists():
            try:
                data = np.loadtxt(enorm_file)
                if label == 'Movie I':
                    all_runs = run_info[
                        (run_info['dataset'] == 'NNdb') &
                        (run_info['subject'] == int(subj_id))
                    ].sort_values(by='run_i')

                    tr_start = 0
                    valid_trs = []
                    for _, row in all_runs.iterrows():
                        run_i = int(row['run_i'])
                        mm_file = results_path / f'mm.r{str(run_i).zfill(2)}_norm_downsampled'
                        if not mm_file.exists():
                            print(f"Warning: missing {mm_file.name} for sub-{subj_id}, skipping run {run_i}")
                            continue
                        tr_count_ds = len(np.loadtxt(mm_file, skiprows=2))

                        if run_i in valid_run_indices[subj_id]:
                            end = tr_start + tr_count_ds
                            valid_trs.append(data[tr_start:end])
                        tr_start += tr_count_ds

                    if not valid_trs:
                        continue
                    data = np.concatenate(valid_trs, axis=0)

                enorm_data = np.abs(data)
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

        # NEW: Outlier fraction (outcount_rall_downsampled.1D, produced by 03_normalize_runs.py)
        outcount_file = results_path / 'outcount_rall_downsampled.1D'
        if outcount_file.exists():
            try:
                data = np.loadtxt(outcount_file)
                if label == 'Movie I':
                    all_runs = run_info[
                        (run_info['dataset'] == 'NNdb') &
                        (run_info['subject'] == int(subj_id))
                    ].sort_values(by='run_i')

                    tr_start = 0
                    valid_trs = []
                    for _, row in all_runs.iterrows():
                        run_i = int(row['run_i'])
                        mm_file = results_path / f'mm.r{str(run_i).zfill(2)}_norm_downsampled'
                        if not mm_file.exists():
                            print(f"Warning: missing {mm_file.name} for sub-{subj_id}, skipping run {run_i}")
                            continue
                        tr_count_ds = len(np.loadtxt(mm_file, skiprows=2))

                        if run_i in valid_run_indices[subj_id]:
                            end = tr_start + tr_count_ds
                            valid_trs.append(data[tr_start:end])
                        tr_start += tr_count_ds

                    if not valid_trs:
                        continue
                    data = np.concatenate(valid_trs, axis=0)

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