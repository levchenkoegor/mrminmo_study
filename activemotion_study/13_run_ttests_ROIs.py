import pandas as pd
import scipy.stats as stats
import statsmodels.stats.multitest as smm
from pathlib import Path

# Paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = Path(root_fldr / 'derivatives')

# Find all folders matching the pattern 'sub-*_nii' except 'sub-dummydata_nii'
subjects = [folder.name for folder in deriv_fldr.iterdir()
            if folder.is_dir() and folder.name.startswith("sub-")
            and folder.name.endswith("_nii") and folder.name != "sub-dummydata_nii"]
subjects = ['sub-241031DC_nii']
conditions = ["MinMo", "NoMinMo"]
movements = ["cough", "crosslegsleftontop", "crosslegsrightontop", "lefthandtorightthigh",
             "righthandtoleftthigh", "raiselefthip", "raiserighthip",
             "sayHellotheremum", "scratchleftcheek", "scratchrightcheek"]

# Load csurf labels
roi_labels = pd.read_csv(root_fldr / "labels_csurfmaps.csv")
rois = ['3b_face', '3b_hand', '3b_foot', '3a_face', '3a_hand', '3a_foot']

# Create a mapping of ROI names to their corresponding column names in roistats files
roi_map = {roi: f"Mean_{roi_labels.loc[roi_labels['name'] == roi, 'id'].values[0]}"
           for roi in rois if not roi_labels.loc[roi_labels['name'] == roi, 'id'].empty}

df_betas_rois = pd.DataFrame()

for subject in subjects:
    for cond in conditions:
        for movement in movements:
            for hemi in ['rh' ,'lh']:
                subj_fldr = (deriv_fldr / subject / f'{subject}_task-mvts_cond-{cond}' / f'{subject}_task-mvts_cond-{cond}.results')

                # Load the ROI statistics
                roistats = pd.read_csv(subj_fldr  / f'roistats_{hemi}_cond-{cond}.csv', delimiter="\t")
                roistats.columns = roistats.columns.str.strip() # Clean column names by stripping whitespace and tabs

                # Pick target ROI (column)
                selected_columns = ['File', 'Sub-brick'] + [col for col in roi_map.values() if col in roistats.columns]
                roistats_targetrois = roistats[selected_columns]

                # Rename ROI columns from "Mean_*" to meaningful ROI names
                rename_dict = {roi_map[roi]: roi for roi in rois if roi_map[roi] in roistats.columns}
                roistats_targetrois = roistats_targetrois.copy().rename(columns=rename_dict)

                # Pick target condition (row)
                # Example: 158[scratchrightcheek_overall_GLT#0_Coef]
                pattern = fr".*{movement}.*GLT.*Coef.*"
                roistats_targetrois_mov = roistats_targetrois.loc[roistats_targetrois['Sub-brick'].str.contains(pattern, regex=True, na=False)]

                # Convert to long format and append to global DataFrame
                if not roistats_targetrois_mov.empty:
                    for _, row in roistats_targetrois_mov.iterrows():
                        for roi in rename_dict.values():  # Use meaningful ROI names
                            beta_value = row[roi]
                            new_row = pd.DataFrame([[subject, cond, movement, hemi, roi, beta_value]],
                                                   columns=["subject", "condition", "movement", "hemi", "ROI",
                                                            "beta_coef"])
                            df_betas_rois = pd.concat([df_betas_rois, new_row], ignore_index=True)


# Save to a separate csv file
df_betas_rois.to_csv(deriv_fldr / 'group_analysis' / 'df_betas_rois.csv', index=False)


# Run statistics and plot distributions for each movement, hemisphere and ROI:
# Initialize list for storing results
ttest_results = []

# Perform one-tailed paired t-tests for each ROI
for roi in rois:
    # Extract MinMo and NoMinMo beta values for each subject
    minmo_betas = df_betas_rois[(df_betas_rois["condition"] == "MinMo") & (df_betas_rois["ROI"] == roi)]
    nominmo_betas = df_betas_rois[(df_betas_rois["condition"] == "NoMinMo") & (df_betas_rois["ROI"] == roi)]

    # Ensure matching subjects
    common_subjects = set(minmo_betas["subject"]).intersection(set(nominmo_betas["subject"]))
    minmo_betas = minmo_betas[minmo_betas["subject"].isin(common_subjects)].sort_values("subject")
    nominmo_betas = nominmo_betas[nominmo_betas["subject"].isin(common_subjects)].sort_values("subject")
    
    # Extract beta values as NumPy arrays
    minmo_values = minmo_betas["beta_coef"].values
    nominmo_values = nominmo_betas["beta_coef"].values

    if len(minmo_values) > 1 and len(nominmo_values) > 1:  # Ensure enough data points
        # Perform one-tailed paired t-test (MinMo > NoMinMo)
        t_stat, p_val = stats.ttest_rel(minmo_values, nominmo_values, alternative='greater')

        # Store results
        ttest_results.append([roi, t_stat, p_val, len(common_subjects)])

# Convert results to a DataFrame
df_ttest_results = pd.DataFrame(ttest_results, columns=["ROI", "t_stat", "p_val", "n_subjects"])

# Correct p-values for multiple comparisons (FDR correction)
df_ttest_results["p_val_fdr"] = smm.multipletests(df_ttest_results["p_val"], method="fdr_bh")[1]

# Apply significance threshold (p < 0.01)
df_ttest_results = df_ttest_results.sort_values("p_val")
df_ttest_results["significant"] = df_ttest_results["p_val_fdr"] < 0.01

#
# # Display results
# import ace_tools as tools
# tools.display_dataframe_to_user(name="Paired t-test Results (MinMo > NoMinMo)", dataframe=df_ttest_results)
#
# Save to CSV
df_ttest_results.to_csv(deriv_fldr / 'group_analysis' / 'df_ttest_results_rois.csv', index=False)
