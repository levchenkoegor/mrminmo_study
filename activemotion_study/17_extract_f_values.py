from pathlib import Path
import pandas as pd

# Paths
root_fldr = Path('/egor2/egor/MinMo_movements/activemotion_study')
deriv_fldr = root_fldr / 'derivatives'
group_analysis_dir = deriv_fldr / 'group_analysis'
group_analysis_dir.mkdir(exist_ok=True)

# Define movements and conditions
movements = [
    "cough", "crosslegsleftontop", "crosslegsrightontop",
    "lefthandtorightthigh", "righthandtoleftthigh",
    "raiselefthip", "raiserighthip",
    "sayHellotheremum", "scratchleftcheek", "scratchrightcheek"
]
conditions = ["MinMo", "NoMinMo"]

# Load subjects
subjects = sorted([folder.name for folder in deriv_fldr.iterdir()
            if folder.is_dir() and folder.name.startswith("sub-")
            and folder.name.endswith("_nii") and folder.name != "sub-dummydata_nii"])

# Initialize output
df_fvalues = pd.DataFrame()

for subject in subjects:
    print(f'{subject} processing...')
    for cond in conditions:
        stats_file = deriv_fldr / subject / f"{subject}_task-mvts_cond-{cond}" / \
                     f"{subject}_task-mvts_cond-{cond}.results" / f"roistats_cond-{cond}_outter.csv"

        if not stats_file.exists():
            print(f"Missing file: {stats_file}")
            continue

        roistats = pd.read_csv(stats_file, delimiter="\t")
        roistats.columns = roistats.columns.str.strip()

        # Extract Full_Fstat (row 0)
        f_row_full = roistats[roistats['Sub-brick'].str.contains(r"\[Full_Fstat\]", na=False)]
        if not f_row_full.empty:
            df_fvalues = pd.concat([
                df_fvalues,
                pd.DataFrame([{
                    "subject": subject,
                    "condition": cond,
                    "movement": "ALL",
                    "ROI": "outside_brain",
                    "f_value": f_row_full["Mean_1"].values[0]
                }])
            ], ignore_index=True)

        # Extract movement-wise Fstats
        for movement in movements:
            f_row = roistats[roistats['Sub-brick'].str.contains(fr"{movement}.*Fstat", regex=True, na=False)]
            if not f_row.empty:
                df_fvalues = pd.concat([
                    df_fvalues,
                    pd.DataFrame([{
                        "subject": subject,
                        "condition": cond,
                        "movement": movement,
                        "ROI": "outside_brain",
                        "f_value": f_row["Mean_1"].values[0]
                    }])
                ], ignore_index=True)

# Save results
output_fname = 'df_f_values_outsidebrain.csv'
df_fvalues.to_csv(group_analysis_dir / output_fname, index=False)
print(f'The file {output_fname} was saved')
