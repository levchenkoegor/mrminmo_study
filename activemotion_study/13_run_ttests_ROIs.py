import pandas as pd
import scipy.stats as stats
from pathlib import Path

# Paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = Path(root_fldr / 'derivatives')

# Find all folders matching the pattern 'sub-*_nii' except 'sub-dummydata_nii'
subjects = [folder.name for folder in deriv_fldr.iterdir()
            if folder.is_dir() and folder.name.startswith("sub-")
            and folder.name.endswith("_nii") and folder.name != "sub-dummydata_nii"]
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

print(roi_map)


for subject in subjects:
    for movement in movements:
        for roi in rois:
            subj_fldr = (deriv_fldr / subject / f'{subject}_task-mvts_cond-{cond}' / f'{subject}_task-mvts_cond-{cond}.results')

            # Load the ROI statistics
            lh_nominmo = pd.read_csv(subj_fldr / "roistats_lh_cond-NoMinMo.csv")
            rh_nominmo = pd.read_csv(subj_fldr / "roistats_rh_cond-NoMinMo.csv")
            lh_minmo = pd.read_csv(subj_fldr / "roistats_lh_cond-MinMo.csv")
            rh_minmo = pd.read_csv(subj_fldr / "roistats_rh_cond-MinMo.csv")

            # Pick target ROI (column)
            lh_nominmo_rois = lh_nominmo[roi_map.values]
            rh_nominmo_rois = rh_nominmo[roi_map.values]
            lh_minmo_rois = lh_minmo[roi_map.values]
            rh_minmo_rois = rh_minmo[roi_map.values]

            # Pick target condition (row)
            # 158[scratchrightcheek_overall_GLT#0_Coef]
            # f'*{movement}GLT*Coef'

            # Append to global dataframe with all subjects
            # Columns: subject, condition (MinMo, NoMinMo), movement, hemi (rh, lh),  ROI, beta_coef
            # df_betas_rois


# Save to a separate csv file
#df_betas_rois.to_csv(deriv_fldr / 'group_analysis', index=False)

# Run statistics and plot distributions for each movement, hemisphere and ROI:
# ...
