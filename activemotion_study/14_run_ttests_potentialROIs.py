from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import ttest_1samp
import statsmodels.stats.multitest as smm
import re
from collections import defaultdict

# Define paths
root = Path("/data/elevchenko/MinMo_movements/activemotion_study")
derivatives = root / "derivatives"
group_analysis_dir = derivatives / "group_analysis"
group_analysis_dir.mkdir(exist_ok=True)

subjects = [folder.name for folder in derivatives.iterdir()
            if folder.is_dir() and folder.name.startswith("sub-")
            and folder.name.endswith("_nii") and folder.name != "sub-dummydata_nii"]

# Load ROI labels
roi_labels_path = root / 'labels_csurfmaps.csv'
roi_labels = pd.read_csv(roi_labels_path)

# Define expected ROIs for movements
target_rois = ['3b_face', '3b_hand', '3b_foot', '3a_face', '3a_hand', '3a_foot',
               '1_face', '1_hand', '1_foot', '4_face', '4_hand', '4_foot']

# Match IDs for all ROIs (not just target ones)
roi_name_to_id = roi_labels.set_index("name")["id"].to_dict()

# Prepare output dataframe for subject-level
results_subject_level = []

# For collecting group-level data
group_voxels = defaultdict(list)

# Loop over hemispheres and conditions
for hemi in ['lh', 'rh']:
    for cond in ['MinMo']:
        for subj in subjects:
            subj_dir = derivatives / f"{subj}" / f"{subj}_task-mvts_cond-{cond}" / f"{subj}_task-mvts_cond-{cond}.results"

            voxel_file = subj_dir / f"voxels_masked_{hemi}_cond-{cond}.csv"
            label_file = subj_dir / f"voxels_labels_{hemi}_cond-{cond}.csv"

            # Load roistats just to extract sub-brick names
            roistats_path = subj_dir / f'roistats_{hemi}_cond-{cond}.csv'

            roistats_df = pd.read_csv(roistats_path, sep='\t')
            subbrick_names = roistats_df['Sub-brick'].tolist()

            # Filter only sub-brick names with *_GLT#0_Coef
            valid_indices = [i for i, name in enumerate(subbrick_names)
                             if re.search(r'overall_GLT#0_Coef', name)]

            # Load data
            voxel_data = pd.read_csv(voxel_file, delim_whitespace=True, header=None)
            label_data = pd.read_csv(label_file, delim_whitespace=True, header=None)

            roi_indices = label_data.iloc[:, -1].values
            betas = voxel_data.values[:, 3:]

            # For each unique ROI
            for roi_id in np.unique(roi_indices):
                roi_name = roi_labels[roi_labels["id"] == roi_id]["name"].values
                if roi_name.size == 0:
                    continue
                roi_name = roi_name[0]

                if roi_name not in target_rois:
                    continue

                mask = roi_indices == roi_id
                roi_betas = betas[mask]

                for col_idx in valid_indices:
                    movement = subbrick_names[col_idx]
                    betas_1d = roi_betas[:, col_idx]

                    # Subject-level t-test
                    t_stat, p_val = ttest_1samp(betas_1d, 0, alternative='greater')
                    results_subject_level.append({
                        "subject": subj,
                        "hemi": hemi,
                        "cond": cond,
                        "roi_name": roi_name,
                        "roi_id": roi_id,
                        "movement": movement,
                        "t_stat": t_stat,
                        "p_val": p_val,
                        "n_voxels": len(betas_1d)
                    })

                    # Group-level: collect voxels
                    key = (hemi, cond, roi_name, movement)
                    group_voxels[key].extend(betas_1d)

# Create subject-level results DataFrame
df_subject = pd.DataFrame(results_subject_level)
df_subject["p_fdr"] = smm.multipletests(df_subject["p_val"], method="fdr_bh")[1]
df_subject["significant"] = df_subject["p_fdr"] < 0.1
df_subject.to_csv(group_analysis_dir / "df_potentialROIs_subject_level_ttests.csv", index=False)


# Group-level t-tests
group_results = []
for (hemi, cond, roi_name, movement), values in group_voxels.items():
    values = np.array(values)
    if len(values) < 3:
        continue
    t_stat, p_val = ttest_1samp(values, 0, alternative='greater')
    group_results.append({
        "hemi": hemi,
        "cond": cond,
        "roi_name": roi_name,
        "movement": movement,
        "t_stat": t_stat,
        "p_val": p_val,
        "n_voxels": len(values)
    })

df_group = pd.DataFrame(group_results)
df_group["p_fdr"] = smm.multipletests(df_group["p_val"], method="fdr_bh")[1]
df_group["significant"] = df_group["p_fdr"] < 0.1
df_group.to_csv(group_analysis_dir / "df_potentialROIs_group_level_ttests.csv", index=False)
