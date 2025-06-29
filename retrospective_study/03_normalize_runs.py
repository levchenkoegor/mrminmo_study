import os
import numpy as np
from pathlib import Path

# Downsample function
def downsample_data(data, dataset_label):
    if dataset_label == 'derivatives_nndb':  # Movie I
        return data[::3]
    elif dataset_label == 'derivatives_btf':  # Movie II
        return data[::2]
    return data

# Define base folders to process
base_dirs = ['derivatives_btf', 'derivatives_nndb']

for base_dir in base_dirs:
    print(f"\nProcessing dataset: {base_dir}")
    base_path = Path(base_dir)

    for subject in sorted(os.listdir(base_path)):

        full_tr_counts = [] # to keep track of full-resolution data (not downsampled)

        print(f"Subject: {subject} from {base_dir}")
        results_path = base_path / f"{subject}" / f"{subject}.results"
        if not results_path.exists():
            print(f"No results ({results_path}) folder for {subject}")
            continue

        # Detect and sort all mm.r0* files
        mm_files = sorted(
            f for f in results_path.glob('mm.r0*')
            if '_delt' not in f.name and '_norm' not in f.name
        )
        tr_counts = []

        for mm_file in mm_files:
            try:
                with open(mm_file, 'r') as f:
                    header = [next(f) for _ in range(2)]
                data = np.loadtxt(mm_file, skiprows=2)

                if data.ndim != 1:
                    raise ValueError(f"Expected 1 column in {mm_file.name}")

                norm_data = data - data[0]
                norm_data = downsample_data(norm_data, base_dir)  # downsampling

                norm_path = mm_file.with_name(mm_file.name + '_norm_downsampled')
                with open(norm_path, 'w') as f:
                    f.writelines(header)
                    np.savetxt(f, norm_data, fmt='%.3f')

                full_tr_counts.append(len(data))  # full-resolution count
                tr_counts.append(len(norm_data))  # downsampled count

                print(f"Normalized: {mm_file.name} → {norm_path.name}")

            except Exception as e:
                print(f"Error processing {mm_file.name}: {e}")

        # Normalize and downsample dfile_rall.1D using inferred TR counts
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

            # Normalize each run segment
            chunks = []
            start = 0
            for n_trs in full_tr_counts:
                end = start + n_trs
                run_data = data[start:end, :]
                run_norm = run_data - run_data[0, :]
                chunks.append(run_norm)
                start = end

            norm_data = np.vstack(chunks)
            norm_data = downsample_data(norm_data, base_dir)
            out_path = dfile_path.with_name('dfile_rall_norm_downsampled.1D')
            with open(out_path, 'w') as f:
                f.writelines(header)
                np.savetxt(f, norm_data, fmt='%.4f')
            print(f"Normalized: dfile_rall.1D → {out_path.name}")

        except Exception as e:
            print(f"Error processing dfile_rall.1D: {e}")
