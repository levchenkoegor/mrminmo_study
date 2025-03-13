#!/bin/bash

# Setup freesurfer for bbregister
export FREESURFER_HOME=/tools/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh
echo $(freesurfer --version)

export SUBJECTS_DIR=/data/elevchenko/MinMo_movements/activemotion_study/derivatives/freesurfer
export data_folder=/data/elevchenko/MinMo_movements/activemotion_study/derivatives

# Extract subject IDs dynamically, removing 'sub-' prefix and appending '_nii'
subjects=$(ls $data_folder | grep -oP '^sub-24\d{4}[A-Z]{2}')

for subj in "sub-241031DC"; do #$subjects; do
  for cond in "MinMo" "NoMinMo"; do

    subj_preproc_outputs=${data_folder}/${subj}_nii/${subj}_nii_task-mvts_cond-${cond}/${subj}_nii_task-mvts_cond-${cond}.results

    3dcalc -a ${subj_preproc_outputs}/vr_base+orig. -expr 'a' -prefix ${subj_preproc_outputs}/vr_base.nii.gz

    bbregister --s $subj \
               --mov ${subj_preproc_outputs}/vr_base.nii.gz \
               --reg ${subj_preproc_outputs}/${subj}_bbreg.dat \
               --T2
 done
done
