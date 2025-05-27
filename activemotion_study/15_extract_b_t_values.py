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
hemis = ["lh", "rh"]

# Load subjects
subjects = sorted([folder.name for folder in deriv_fldr.iterdir()
            if folder.is_dir() and folder.name.startswith("sub-")
            and folder.name.endswith("_nii") and folder.name != "sub-dummydata_nii"])

# Load ROI labels
roi_labels = pd.read_csv(root_fldr / "labels_csurfmaps.csv")
rois = ['3b_face', '3b_hand', '3b_foot', '3a_face', '3a_hand', '3a_foot',
        '1_face', '1_hand', '1_foot', '4_face', '4_hand', '4_foot']
roi_map = {roi: f"Mean_{roi_labels.loc[roi_labels['name'] == roi, 'id'].values[0]}"
           for roi in rois if not roi_labels.loc[roi_labels['name'] == roi, 'id'].empty}

# Define relevant ROIs for each movement
movement_roi_map = {
    "cough": ['3b_face', '3a_face', '1_face', '4_face'],
    "sayHellotheremum": ['3b_face', '3a_face', '1_face', '4_face'],
    "scratchleftcheek": ['3b_hand', '3a_hand', '1_hand', '4_hand'],
    "scratchrightcheek": ['3b_hand', '3a_hand', '1_hand', '4_hand'],
    "lefthandtorightthigh": ['3b_hand', '3a_hand', '1_hand', '4_hand'],
    "righthandtoleftthigh": ['3b_hand', '3a_hand', '1_hand', '4_hand'],
    "crosslegsleftontop": ['3b_foot', '3a_foot', '1_foot', '4_foot'],
    "crosslegsrightontop": ['3b_foot', '3a_foot', '1_foot', '4_foot'],
    "raiselefthip": ['3b_foot', '3a_foot', '1_foot', '4_foot'],
    "raiserighthip": ['3b_foot', '3a_foot', '1_foot', '4_foot'],
}

# Collect all beta and t-values
df_b_t_values_rois = pd.DataFrame()

for subject in subjects:
    print(f'{subject} processing...')
    for cond in conditions:
        for movement in movements:
            for hemi in hemis:
                subj_fldr = (deriv_fldr / subject / f'{subject}_task-mvts_cond-{cond}' /
                             f'{subject}_task-mvts_cond-{cond}.results')

                stats_file = subj_fldr / f'roistats_{hemi}_cond-{cond}.csv'

                if not stats_file.exists():
                    print(f"Missing file: {stats_file}")
                    continue

                roistats = pd.read_csv(stats_file, delimiter="\t")
                roistats.columns = roistats.columns.str.strip()

                selected_columns = ['File', 'Sub-brick'] + [col for col in roi_map.values() if col in roistats.columns]
                roistats_targetrois = roistats[selected_columns]

                rename_dict = {roi_map[roi]: roi for roi in rois if roi_map[roi] in roistats.columns}
                roistats_targetrois = roistats_targetrois.rename(columns=rename_dict)

                # Match betas
                beta_rows = roistats_targetrois[roistats_targetrois['Sub-brick'].str.contains(fr".*{movement}.*overall.*Coef.*", regex=True, na=False)]
                # Match t-values
                tval_rows = roistats_targetrois[roistats_targetrois['Sub-brick'].str.contains(fr".*{movement}.*overall.*Tstat.*", regex=True, na=False)]

                if not beta_rows.empty:
                    for _, row in beta_rows.iterrows():
                        for roi in movement_roi_map[movement]:
                            if roi in row:
                                beta_value = row[roi]
                                t_value = None

                                # Try to match a corresponding t-value row (assuming same ROI column and same order)
                                if not tval_rows.empty:
                                    t_row = tval_rows.iloc[0]  # assuming 1-to-1 match
                                    if roi in t_row:
                                        t_value = t_row[roi]

                                df_b_t_values_rois = pd.concat([
                                    df_b_t_values_rois,
                                    pd.DataFrame([{
                                        "subject": subject,
                                        "condition": cond,
                                        "movement": movement,
                                        "hemi": hemi,
                                        "ROI": roi,
                                        "beta_coef": beta_value,
                                        "t_value": t_value
                                    }])
                                ], ignore_index=True)

# Save results
output_fname = 'df_b_t_values_selectedROIs.csv'
df_b_t_values_rois.to_csv(group_analysis_dir / output_fname, index=False)
print(f'The file {output_fname} was saved')
