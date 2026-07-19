import os
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

# Valid NNDb runs (>= 600 TRs) -- same filter 04_plot_histograms.py and
# 06_extract_statistics.py apply, used below to restrict enorm_max/mean and
# outlier_frac_max/mean to valid runs only. The per-TR downsampled .1D files
# themselves are still written unfiltered (all runs), matching how dfile/mm
# files are handled -- filtering happens at the summary-stat step only.
run_info = pd.read_csv('run_lengths.csv')
valid_nndb_runs = run_info[(run_info['dataset'] == 'NNdb') & (run_info['n_trs'] >= 600)]
valid_run_indices = defaultdict(list)
for _, row in valid_nndb_runs.iterrows():
    valid_run_indices[str(row['subject']).zfill(2)].append(int(row['run_i']))

# Downsample function
def downsample_data(data, dataset_label):
    if dataset_label == 'derivatives_nndb':  # Movie I
        return data[::3]
    elif dataset_label == 'derivatives_btf':  # Movie II
        return data[::2]
    return data

# Define base folders to process
base_dirs = ['derivatives_btf', 'derivatives_nndb']
delta_summary = []

# Metric names for columns
motion_metrics = ['roll', 'pitch', 'yaw', 'dS', 'dL', 'dP']

for base_dir in base_dirs:
    print(f"\nProcessing dataset: {base_dir}")
    base_path = Path(base_dir)

    for subject in sorted(os.listdir(base_path)):
        # afni_proc.py's -subj_id value, embedded in filenames like motion_${subj_id}_enorm.1D.
        # This matches how 01_run_preprocessing.sh names subject_folder="sub-$subj_id", so the
        # directory name "subject" (e.g. "sub-01") strips down to the exact afni_subj_id.
        afni_subj_id = subject.replace('sub-', '', 1)
        subj_id_padded = afni_subj_id.zfill(2)  # for valid_run_indices lookup (NNDb only)

        full_tr_counts = []  # full-resolution TRs per run
        run_numbers = []     # run index (int) parallel to full_tr_counts, for NNDb valid-run filtering
        downsampled_tr_counts = []  # after downsampling

        print(f"Subject: {subject} from {base_dir}")
        results_path = base_path / f"{subject}" / f"{subject}.results"
        if not results_path.exists():
            print(f"No results ({results_path}) folder for {subject}")
            continue

        # Per-subject summary row, filled in incrementally across blocks below and
        # appended once at the end so a missing enorm/outcount file doesn't drop
        # the row entirely -- it just leaves those columns as NaN.
        subject_summary = {'dataset': base_dir, 'subject': subject}

        mm_files = sorted(
            f for f in results_path.glob('mm.r0*')
            if '_delt' not in f.name and '_norm' not in f.name
        )
        for mm_file in mm_files:
            try:
                with open(mm_file, 'r') as f:
                    header = [next(f) for _ in range(2)]
                data = np.loadtxt(mm_file, skiprows=2)

                if data.ndim != 1:
                    raise ValueError(f"Expected 1 column in {mm_file.name}")

                norm_data = data - data[0]

                # Save normalised (full resolution, before downsampling)
                norm_path = mm_file.with_name(mm_file.name + '_norm')
                with open(norm_path, 'w') as f:
                    f.writelines(header)
                    np.savetxt(f, norm_data, fmt='%.3f')
                print(f"Normalized: {mm_file.name} → {norm_path.name}")

                # Downsample and save
                norm_ds_data = downsample_data(norm_data, base_dir)
                norm_ds_path = mm_file.with_name(mm_file.name + '_norm_downsampled')
                with open(norm_ds_path, 'w') as f:
                    f.writelines(header)
                    np.savetxt(f, norm_ds_data, fmt='%.3f')
                print(f"Downsampled: {mm_file.name} → {norm_ds_path.name}")

                full_tr_counts.append(len(data))
                downsampled_tr_counts.append(len(norm_ds_data))
                run_numbers.append(int(mm_file.name.split('.')[1][1:3]))

            except Exception as e:
                print(f"Error processing {mm_file.name}: {e}")

        # Downsample delt files (no normalisation needed - already frame-to-frame differences)
        delt_files = sorted(
            f for f in results_path.glob('mm.r0*_delt')
            if '_norm' not in f.name
        )
        for delt_file in delt_files:
            try:
                with open(delt_file, 'r') as f:
                    header = [next(f) for _ in range(2)]
                data = np.loadtxt(delt_file, skiprows=2)

                if data.ndim != 1:
                    raise ValueError(f"Expected 1 column in {delt_file.name}")

                delt_ds_data = downsample_data(data, base_dir)
                delt_ds_path = delt_file.with_name(delt_file.name + '_downsampled')
                with open(delt_ds_path, 'w') as f:
                    f.writelines(header)
                    np.savetxt(f, delt_ds_data, fmt='%.3f')
                print(f"Downsampled: {delt_file.name} → {delt_ds_path.name}")

            except Exception as e:
                print(f"Error processing {delt_file.name}: {e}")

        # Normalize and downsample dfile_rall.1D
        dfile_path = results_path / 'dfile_rall.1D'
        if not dfile_path.exists():
            print(f"Missing: dfile_rall.1D")
            continue

        try:
            with open(dfile_path, 'r') as f:
                header = [line for line in f if line.startswith('#')]
            data = np.loadtxt(dfile_path)

            if data.ndim != 2 or data.shape[1] != 6:
                raise ValueError("Expected 6 columns in dfile_rall.1D")

            if sum(full_tr_counts) != data.shape[0]:
                raise ValueError(f"Mismatch: sum(TRs from mm.r0*) = {sum(full_tr_counts)}, "
                                 f"but dfile_rall.1D has {data.shape[0]} rows.")

            chunks = []
            norm_full_chunks = []
            delta_chunks = []
            start = 0
            for i, n_trs in enumerate(full_tr_counts):
                end = start + n_trs
                run_data = data[start:end, :]
                run_norm = run_data - run_data[0, :]
                run_norm_ds = downsample_data(run_norm, base_dir)

                # AFNI convention: backward difference per run, with the first TR's
                # derivative set to 0 (there is no earlier TR in the run to diff against).
                # Previously this was np.diff(run_norm_ds, axis=0) with no prepend, which
                # drops one row per run instead of zero-filling it -- that leaves delta_data
                # one row shorter than run_norm_ds/norm_data per run and out of alignment
                # with per-TR data (enorm, outlier fraction, raw signal).
                run_delta = np.diff(run_norm_ds, axis=0, prepend=run_norm_ds[[0]])

                delta_chunks.append(run_delta)
                norm_full_chunks.append(run_norm)
                chunks.append(run_norm_ds)

                start = end

            norm_data = np.vstack(chunks)
            delta_data = np.vstack(delta_chunks)

            # Save normalised full-resolution data (before downsampling)
            norm_full_path = dfile_path.with_name('dfile_rall_norm.1D')
            with open(norm_full_path, 'w') as f:
                f.writelines(header)
                np.savetxt(f, np.vstack(norm_full_chunks), fmt='%.4f')
            print(f"Normalized (full res): dfile_rall.1D → {norm_full_path.name}")

            # Save normalised downsampled data
            norm_path = dfile_path.with_name('dfile_rall_norm_downsampled.1D')
            with open(norm_path, 'w') as f:
                f.writelines(header)
                np.savetxt(f, norm_data, fmt='%.4f')
            print(f"Normalized (downsampled): dfile_rall.1D → {norm_path.name}")

            # Save delta data
            delta_path = dfile_path.with_name('dfile_rall_delta_downsampled.1D')
            with open(delta_path, 'w') as f:
                f.writelines(header)
                np.savetxt(f, delta_data, fmt='%.4f')
            print(f"Delta saved: {delta_path.name}")

            # Collect max per column for CSV
            delta_max = np.abs(delta_data).max(axis=0)
            subject_summary.update({
                f'{metric}_max': round(delta_max[i], 4) for i, metric in enumerate(motion_metrics)
            })

        except Exception as e:
            print(f"Error processing dfile_rall.1D: {e}")

        # --- Enorm ---
        # afni_proc.py computes motion parameter derivatives (and their Euclidean-norm
        # collapse) by default in the regress block, regardless of -regress_censor_motion --
        # that flag only controls whether enorm is *used* for censoring. So
        # motion_${afni_subj_id}_enorm.1D already exists in every subject's results folder;
        # this just extracts and downsamples it the same way the other metrics are handled.
        enorm_path = results_path / f'motion_{afni_subj_id}_enorm.1D'
        if not enorm_path.exists():
            print(f"Missing: {enorm_path.name} for {subject}")
        else:
            try:
                enorm_data = np.loadtxt(enorm_path)  # 1 column, full temporal resolution

                if sum(full_tr_counts) != len(enorm_data):
                    raise ValueError(f"Mismatch: sum(TRs)={sum(full_tr_counts)}, "
                                     f"{enorm_path.name} has {len(enorm_data)} rows")

                enorm_chunks = []
                enorm_chunks_valid = []
                start = 0
                for n_trs, run_num in zip(full_tr_counts, run_numbers):
                    end = start + n_trs
                    chunk_ds = downsample_data(enorm_data[start:end], base_dir)
                    enorm_chunks.append(chunk_ds)
                    if base_dir == 'derivatives_nndb':
                        if run_num in valid_run_indices[subj_id_padded]:
                            enorm_chunks_valid.append(chunk_ds)
                    else:
                        enorm_chunks_valid.append(chunk_ds)
                    start = end

                enorm_ds = np.concatenate(enorm_chunks)
                enorm_ds_path = enorm_path.with_name(f'motion_{afni_subj_id}_enorm_downsampled.1D')
                np.savetxt(enorm_ds_path, enorm_ds, fmt='%.4f')
                print(f"Downsampled: {enorm_path.name} → {enorm_ds_path.name}")

                if enorm_chunks_valid:
                    enorm_ds_valid = np.concatenate(enorm_chunks_valid)
                    subject_summary['enorm_max'] = round(float(enorm_ds_valid.max()), 4)
                    subject_summary['enorm_mean'] = round(float(enorm_ds_valid.mean()), 4)
                else:
                    print(f"No valid NNDb runs for enorm summary stats: {subject}")

            except Exception as e:
                print(f"Error processing {enorm_path.name}: {e}")

        # --- Outlier fraction ---
        # Generated automatically by afni_proc.py's built-in outcount QC step
        # (3dToutcount -fraction on the tcat data), independent of -regress_censor_outliers.
        outcount_path = results_path / 'outcount_rall.1D'
        if not outcount_path.exists():
            print(f"Missing: outcount_rall.1D for {subject}")
        else:
            try:
                outcount_data = np.loadtxt(outcount_path)

                if sum(full_tr_counts) != len(outcount_data):
                    raise ValueError(f"Mismatch: sum(TRs)={sum(full_tr_counts)}, "
                                     f"outcount_rall.1D has {len(outcount_data)} rows")

                # NOTE: assumes outcount.r$run.1D was concatenated by afni_proc.py in the
                # same run order as the mm.r0* files used to build full_tr_counts. Both are
                # numeric-sorted by run number, so this should hold, but it's worth spot
                # checking on subjects with non-standard run orderings (e.g. BTF sub-24/36,
                # which have custom dsets ordering in 01_run_preprocessing.sh).
                outcount_chunks = []
                outcount_chunks_valid = []
                start = 0
                for n_trs, run_num in zip(full_tr_counts, run_numbers):
                    end = start + n_trs
                    chunk_ds = downsample_data(outcount_data[start:end], base_dir)
                    outcount_chunks.append(chunk_ds)
                    if base_dir == 'derivatives_nndb':
                        if run_num in valid_run_indices[subj_id_padded]:
                            outcount_chunks_valid.append(chunk_ds)
                    else:
                        outcount_chunks_valid.append(chunk_ds)
                    start = end

                outcount_ds = np.concatenate(outcount_chunks)
                outcount_ds_path = outcount_path.with_name('outcount_rall_downsampled.1D')
                np.savetxt(outcount_ds_path, outcount_ds, fmt='%.4f')
                print(f"Downsampled: outcount_rall.1D → {outcount_ds_path.name}")

                if outcount_chunks_valid:
                    outcount_ds_valid = np.concatenate(outcount_chunks_valid)
                    subject_summary['outlier_frac_max'] = round(float(outcount_ds_valid.max()), 4)
                    subject_summary['outlier_frac_mean'] = round(float(outcount_ds_valid.mean()), 4)
                else:
                    print(f"No valid NNDb runs for outlier_frac summary stats: {subject}")

            except Exception as e:
                print(f"Error processing outcount_rall.1D: {e}")

        delta_summary.append(subject_summary)

# Save summary CSV
df_summary = pd.DataFrame(delta_summary)
df_summary.to_csv('group_analysis/delta_max_per_subject.csv', index=False)
print("\nSummary CSV saved: delta_max_per_subject.csv")