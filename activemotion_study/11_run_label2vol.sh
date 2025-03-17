#!/bin/bash

# Setup FreeSurfer
export FREESURFER_HOME=/tools/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh

export SUBJECTS_DIR=/data/elevchenko/MinMo_movements/activemotion_study/derivatives/freesurfer
export data_folder=/data/elevchenko/MinMo_movements/activemotion_study/derivatives

# Extract subject IDs dynamically
subjects=$(ls $data_folder | grep -oP '^sub-24\d{4}[A-Z]{2}')

for subj in "sub-241031DC"; do #$subjects; do

    # fsaverage sereno to subject-wise space (right and left hemi)
    mkdir $SUBJECTS_DIR/${subj}_test/label
    mri_surf2surf --srcsubject fsaverage_sereno2022 \
                --trgsubject $subj \
                --hemi rh \
                --sval-annot $SUBJECTS_DIR/fsaverage_sereno2022/label/rh.aparc.annot \
                --tval $SUBJECTS_DIR/${subj}_test/label/rh.aparc.annot

    mri_surf2surf --srcsubject fsaverage_sereno2022 \
                --trgsubject $subj \
                --hemi lh \
                --sval-annot $SUBJECTS_DIR/fsaverage_sereno2022/label/lh.aparc.annot \
                --tval $SUBJECTS_DIR/${subj}_test/label/lh.aparc.annot


  for cond in "MinMo" "NoMinMo"; do

    subj_preproc_outputs=${data_folder}/${subj}_nii/${subj}_nii_task-mvts_cond-${cond}/${subj}_nii_task-mvts_cond-${cond}.results

    # Define required files for mri_labe2vol
    mov_file=${subj_preproc_outputs}/vr_base.nii.gz  # EPI motion reference
    reg_file=${subj_preproc_outputs}/${subj}_bbreg.dat    # Registration file

    # label2vol
    mri_label2vol --annot aparc \
                  --subject $subj \
                  --hemi lh \
                  --reg $reg_file \
                  --o $SUBJECTS_DIR/${subj}_test/lh.aparc_epi_cond-${cond}.nii.gz \
                  --temp $mov_file

    mri_label2vol --annot aparc \
                  --subject $subj \
                  --hemi rh \
                  --reg $reg_file \
                  --o $SUBJECTS_DIR/${subj}_test/rh.aparc_epi_cond-${cond}.nii.gz \
                  --temp $mov_file

  done
done


### Notes:
# Abbreviations: https://pages.ucsd.edu/~msereno/csurf/fsaverage-labels/CsurfMaps1-parcellation/Abbreviations-Table1.pdf
# Download Sereno (2022) fsaverage: https://pages.ucsd.edu/~msereno/csurf/

# H1.4
# mri_surf2surf - fsaverage to subjectwise space
# mri_label2vol - subjectwise space to EPI subjectspace

# H1.5
# mri_label2vol
# project out of cortex: lateralorbitofrontal, lateroccipital
