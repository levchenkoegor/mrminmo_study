#!/bin/bash

# Setup FreeSurfer
export FREESURFER_HOME=/tools/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh

export SUBJECTS_DIR=/egor2/egor/MinMo_movements/activemotion_study/derivatives/freesurfer
export data_folder=/egor2/egor/MinMo_movements/activemotion_study/derivatives

# Extract subject IDs dynamically
subjects=$(ls $data_folder | grep -oP '^sub-24\d{4}[A-Z]{2}')

for subj in $subjects; do

    # fsaverage sereno to subject-wise space (right and left hemi)
    mri_surf2surf --srcsubject fsaverage_sereno2022 \
                --trgsubject $subj \
                --hemi rh \
                --sval-annot $SUBJECTS_DIR/fsaverage_sereno2022/label/rh-CsurfMaps1.annot \
                --tval $SUBJECTS_DIR/${subj}/label/rh.aparc_s2s_sereno.annot

    mri_surf2surf --srcsubject fsaverage_sereno2022 \
                --trgsubject $subj \
                --hemi lh \
                --sval-annot $SUBJECTS_DIR/fsaverage_sereno2022/label/lh-CsurfMaps1.annot \
                --tval $SUBJECTS_DIR/${subj}/label/lh.aparc_s2s_sereno.annot


  for cond in "MinMo" "NoMinMo"; do

    subj_preproc_outputs=${data_folder}/${subj}_nii/${subj}_nii_task-mvts_cond-${cond}/${subj}_nii_task-mvts_cond-${cond}.results

    # Define required files for mri_labe2vol
    mov_file=${subj_preproc_outputs}/vr_base.nii.gz       # EPI motion reference
    reg_file=${subj_preproc_outputs}/${subj}_bbreg.dat    # Registration file

    # label2vol
    mri_label2vol --annot $SUBJECTS_DIR/${subj}/label/lh.aparc_s2s_sereno.annot \
                  --subject $subj \
                  --hemi lh \
                  --proj frac 0 0.8 0.2 \
                  --fillthresh 0.2 \
                  --reg $reg_file \
                  --o $SUBJECTS_DIR/${subj}/lh.aparc_epi_cond-${cond}.nii.gz \
                  --temp $mov_file

    mri_label2vol --annot $SUBJECTS_DIR/${subj}/label/rh.aparc_s2s_sereno.annot \
                  --subject $subj \
                  --hemi rh \
                  --proj frac 0 0.8 0.2 \
                  --fillthresh 0.2 \
                  --reg $reg_file \
                  --o $SUBJECTS_DIR/${subj}/rh.aparc_epi_cond-${cond}.nii.gz \
                  --temp $mov_file


    # label2vol (OUTSIDE OF THE BRAIN)
    mri_label2vol --annot $SUBJECTS_DIR/${subj}/label/lh.aparc_s2s_sereno.annot \
                  --subject $subj \
                  --hemi lh \
                  --proj frac 1 2.8 0.2 \
                  --fillthresh 0.2 \
                  --reg $reg_file \
                  --o $SUBJECTS_DIR/${subj}/lh.aparc_epi_cond-${cond}_outter.nii.gz \
                  --temp $mov_file

    mri_label2vol --annot $SUBJECTS_DIR/${subj}/label/rh.aparc_s2s_sereno.annot \
                  --subject $subj \
                  --hemi rh \
                  --proj frac 1 2.8 0.2 \
                  --fillthresh 0.2 \
                  --reg $reg_file \
                  --o $SUBJECTS_DIR/${subj}/rh.aparc_epi_cond-${cond}_outter.nii.gz \
                  --temp $mov_file

    # Symlink to vr_base.nii.gz
    ln -sf $mov_file $SUBJECTS_DIR/${subj}/vr_base_cond-${cond}.nii.gz

    ## Create a mask for spurious activity (outside the brain)
    lh_outter=$SUBJECTS_DIR/${subj}/lh.aparc_epi_cond-${cond}_outter.nii.gz
    rh_outter=$SUBJECTS_DIR/${subj}/rh.aparc_epi_cond-${cond}_outter.nii.gz
    brainmask=${subj_preproc_outputs}/brainmask_cond-${cond}.nii.gz
    nonbrain_mask=${subj_preproc_outputs}/nonbrain_mask_cond-${cond}.nii.gz
    combined_outter_mask=${subj_preproc_outputs}/mask_outsidebrain_raw_cond-${cond}.nii.gz
    final_mask=${subj_preproc_outputs}/mask_outsidebrain_clean_cond-${cond}.nii.gz

    # Create EPI-based brain mask
    3dAutomask -prefix $brainmask $mov_file -overwrite

    # Invert the brain mask
    3dcalc -a $brainmask -expr 'not(a)' -prefix $nonbrain_mask -overwrite

    # Combine LH and RH 'outter' projection masks
    3dcalc -a $lh_outter -b $rh_outter -expr 'max(step(a),step(b))' -prefix $combined_outter_mask -overwrite

    # Intersect outer projection with non-brain mask
    3dcalc -a $combined_outter_mask -b $nonbrain_mask -expr 'a*b' -prefix $final_mask -overwrite

    # Symlinks
    ln -sf $brainmask $SUBJECTS_DIR/${subj}/brainmask_cond-${cond}.nii.gz
    ln -sf $nonbrain_mask $SUBJECTS_DIR/${subj}/nonbrain_mask_cond-${cond}.nii.gz
    ln -sf $combined_outter_mask $SUBJECTS_DIR/${subj}/mask_outsidebrain_raw_cond-${cond}.nii.gz
    ln -sf $final_mask $SUBJECTS_DIR/${subj}/mask_outsidebrain_clean_cond-${cond}.nii.gz

  done
done


### Notes:
# Abbreviations: https://pages.ucsd.edu/~msereno/csurf/fsaverage-labels/CsurfMaps1-parcellation/Abbreviations-Table1.pdf
# Download Sereno (2022) fsaverage: https://pages.ucsd.edu/~msereno/csurf/
# Labels: https://pages.ucsd.edu/~msereno/csurf/fsaverage-labels/CsurfMaps1-parcellation/CsurfMaps1.ctab.txt

# H1.4
# mri_surf2surf - fsaverage to subjectwise space
# mri_label2vol - subjectwise space to EPI subjectspace

# H1.5
# mri_label2vol
# project out of cortex: lateralorbitofrontal, lateroccipital
