#!/bin/bash

# Setup FreeSurfer
export FREESURFER_HOME=/tools/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh

export SUBJECTS_DIR=/data/elevchenko/MinMo_movements/activemotion_study/derivatives/freesurfer
export data_folder=/data/elevchenko/MinMo_movements/activemotion_study/derivatives

# Extract subject IDs dynamically
subjects=$(ls $data_folder | grep -oP '^sub-24\d{4}[A-Z]{2}')

# List of ROI labels
roi_labels=("ROI1" "ROI2" "ROI3") # need to adjust

for subj in "sub-241031DC"; do #$subjects; do
  for cond in "MinMo" "NoMinMo"; do

    subj_preproc_outputs=${data_folder}/${subj}_nii/${subj}_nii_task-mvts_cond-${cond}/${subj}_nii_task-mvts_cond-${cond}.results

    # Define required files
    mov_file=${subj_preproc_outputs}/vr_base+orig.nii.gz  # EPI motion reference
    reg_file=${subj_preproc_outputs}/${subj}_bbreg.dat    # Registration file

    # Create subject-specific ROI masks in EPI space
    for roi in "${roi_labels[@]}"; do
      mri_label2vol --label $SUBJECTS_DIR/$subj/label/lh.${roi}.label \
                    --subject $subj \
                    --reg $reg_file \
                    --hemi lh \
                    --fillthresh 0.3 \
                    --proj frac 0 1 0.1 \
                    --o ${subj_preproc_outputs}/${roi}_lh.nii.gz \
                    --temp $mov_file

      mri_label2vol --label $SUBJECTS_DIR/$subj/label/rh.${roi}.label \
                    --subject $subj \
                    --reg $reg_file \
                    --hemi rh \
                    --fillthresh 0.3 \
                    --proj frac 0 1 0.1 \
                    --o ${subj_preproc_outputs}/${roi}_rh.nii.gz \
                    --temp $mov_file

    done
  done
done


### Notes:
# Abbreviations: https://pages.ucsd.edu/~msereno/csurf/fsaverage-labels/CsurfMaps1-parcellation/Abbreviations-Table1.pdf
# Download parcellations: wget -r -np -nH https://pages.ucsd.edu/~msereno/csurf/fsaverage-labels/CsurfMaps1-parcellation/
#