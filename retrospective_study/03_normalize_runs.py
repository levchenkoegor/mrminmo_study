import os
import numpy as np
from pathlib import Path

# Define base folders to process
base_dirs = ['derivatives_btf', 'derivatives_nndb']

for base_dir in base_dirs:
    print(f"\nProcessing dataset: {base_dir}")
    base_path = Path(base_dir)

    for subject in ["01", "1"]: #os.listdir(base_path):

        print(f"Subject: {subject}")
        results_path = base_path / f"sub-{subject}" / f"sub-{subject}.results"
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
                norm_path = mm_file.with_name(mm_file.name + '_norm')
                with open(norm_path, 'w') as f:
                    f.writelines(header)
                    np.savetxt(f, norm_data, fmt='%.3f')

                tr_counts.append(len(data))
                print(f"Normalized: {mm_file.name} → {norm_path.name}")

            except Exception as e:
                print(f"Error processing {mm_file.name}: {e}")

        # Normalize dfile_rall.1D using inferred TR counts
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

            if sum(tr_counts) != data.shape[0]:
                raise ValueError(f"Mismatch: sum(TRs from mm.r0*) = {sum(tr_counts)}, "
                                 f"but dfile_rall.1D has {data.shape[0]} rows.")

            # Normalize each run segment
            chunks = []
            start = 0
            for n_trs in tr_counts:
                end = start + n_trs
                run_data = data[start:end, :]
                run_norm = run_data - run_data[0, :]
                chunks.append(run_norm)
                start = end

            norm_data = np.vstack(chunks)
            out_path = dfile_path.with_name('dfile_rall_norm.1D')
            with open(out_path, 'w') as f:
                f.writelines(header)
                np.savetxt(f, norm_data, fmt='%.4f')
            print(f"Normalized: dfile_rall.1D → {out_path.name}")

        except Exception as e:
            print(f"Error processing dfile_rall.1D: {e}")
