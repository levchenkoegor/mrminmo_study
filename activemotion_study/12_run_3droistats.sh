#!/bin/bash

# Setup environment
export FREESURFER_HOME=/tools/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh

export SUBJECTS_DIR=/data/elevchenko/MinMo_movements/activemotion_study/derivatives/freesurfer
export data_folder=/data/elevchenko/MinMo_movements/activemotion_study/derivatives

# Extract subject IDs dynamically
subjects=$(ls $SUBJECTS_DIR | grep -oP '^sub-24\d{4}[A-Z]{2}')

for subj in "sub-241031DC"; do #$subjects; do
  echo "Processing subject: $subj"

  for cond in "MinMo"; do # "NoMinMo"; do

    subj_preproc_outputs=${data_folder}/${subj}_nii/${subj}_nii_task-mvts_cond-${cond}/${subj}_nii_task-mvts_cond-${cond}.results

    # Define stat file
    stats_file=${subj_preproc_outputs}/stats_tent_48-88.${subj#sub-}_nii+orig.HEAD

    # Define ROI masks in EPI space
    lh_roi_mask=$SUBJECTS_DIR/${subj}_test/lh.aparc_epi_cond-${cond}.nii.gz
    rh_roi_mask=$SUBJECTS_DIR/${subj}_test/rh.aparc_epi_cond-${cond}.nii.gz

    # Extract ROI statistics for left hemisphere
    3dROIstats -mask $lh_roi_mask $stats_file > ${subj_preproc_outputs}/roistats_lh_cond-${cond}.csv

    # Extract ROI statistics for right hemisphere
    3dROIstats -mask $rh_roi_mask $stats_file > ${subj_preproc_outputs}/roistats_rh_cond-${cond}.csv

  done
done
