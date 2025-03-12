#!/bin/bash

export data_folder=/data/elevchenko/MinMo_movements/activemotion_study/derivatives
export stim_folder=/data/elevchenko/MinMo_movements/activemotion_study/stimuli_tent

# Extract subject IDs dynamically, removing 'sub-' prefix and appending '_nii'
subjects=$(ls $data_folder | grep -oP '^sub-\K24\d{4}[A-Z]{2}' | sed 's/$/_nii/')
tr_counts=1515 # all runs (505, 505, 505)

# 1 subj takes around 1.5 hours
for subj in "241031DC_nii"; do #$subjects; do
  for cond in "MinMo" "NoMinMo"; do

    subj_preproc_outputs=${data_folder}/sub-${subj}/sub-${subj}_task-mvts_cond-${cond}/sub-${subj}_task-mvts_cond-${cond}.results

    # compute de-meaned motion parameters (for use in regression)
    1d_tool.py -infile ${subj_preproc_outputs}/dfile_rall.1D \
               -set_run_lengths $tr_counts \
               -demean -write ${subj_preproc_outputs}/motion_demean.1D

    # compute motion parameter derivatives (for use in regression)
    1d_tool.py -infile ${subj_preproc_outputs}/dfile_rall.1D \
               -set_run_lengths $tr_counts \
               -derivative -demean -write ${subj_preproc_outputs}/motion_deriv.1D

    # convert motion parameters for per-run regression
    1d_tool.py -infile ${subj_preproc_outputs}/motion_demean.1D \
               -set_run_lengths 505 505 505 \
               -split_into_pad_runs ${subj_preproc_outputs}/mot_demean

    1d_tool.py -infile ${subj_preproc_outputs}/motion_deriv.1D \
               -set_run_lengths 505 505 505 \
               -split_into_pad_runs ${subj_preproc_outputs}/mot_deriv

    # run regression
    3dDeconvolve -input ${subj_preproc_outputs}/pb03.$subj.r*.scale+orig.HEAD \
        -ortvec ${subj_preproc_outputs}/mot_demean.r01.1D mot_demean_r01 \
        -ortvec ${subj_preproc_outputs}/mot_demean.r02.1D mot_demean_r02 \
        -ortvec ${subj_preproc_outputs}/mot_demean.r03.1D mot_demean_r03 \
        -ortvec ${subj_preproc_outputs}/mot_deriv.r01.1D mot_deriv_r01 \
        -ortvec ${subj_preproc_outputs}/mot_deriv.r02.1D mot_deriv_r02 \
        -ortvec ${subj_preproc_outputs}/mot_deriv.r03.1D mot_deriv_r03 \
        -polort A -float \
        -num_stimts 10 \
        -local_times \
        -stim_label 1 cough \
        -stim_label 2 crosslegsleftontop \
        -stim_label 3 crosslegsrightontop \
        -stim_label 4 lefthandtorightthigh \
        -stim_label 5 righthandtoleftthigh \
        -stim_label 6 raiselefthip \
        -stim_label 7 raiserighthip \
        -stim_label 8 sayHellotheremum \
        -stim_label 9 scratchleftcheek \
        -stim_label 10 scratchrightcheek \
        -stim_times 1 ${stim_folder}/subjectwise/condition-cough_sub-${subj}_cond-${cond}_runs-*.1D 'TENT(4.8, 8.8, 6)' \
        -stim_times 2 ${stim_folder}/subjectwise/condition-crosslegsleftontop_sub-${subj}_cond-${cond}_runs-*.1D 'TENT(4.8, 8.8, 6)' \
        -stim_times 3 ${stim_folder}/subjectwise/condition-crosslegsrightontop_sub-${subj}_cond-${cond}_runs-*.1D 'TENT(4.8, 8.8, 6)' \
        -stim_times 4 ${stim_folder}/subjectwise/condition-lefthandtorightthigh_sub-${subj}_cond-${cond}_runs-*.1D 'TENT(4.8, 8.8, 6)' \
        -stim_times 5 ${stim_folder}/subjectwise/condition-righthandtoleftthigh_sub-${subj}_cond-${cond}_runs-*.1D 'TENT(4.8, 8.8, 6)' \
        -stim_times 6 ${stim_folder}/subjectwise/condition-raiselefthip_sub-${subj}_cond-${cond}_runs-*.1D 'TENT(4.8, 8.8, 6)' \
        -stim_times 7 ${stim_folder}/subjectwise/condition-raiserighthip_sub-${subj}_cond-${cond}_runs-*.1D 'TENT(4.8, 8.8, 6)' \
        -stim_times 8 ${stim_folder}/subjectwise/condition-sayHellotheremum_sub-${subj}_cond-${cond}_runs-*.1D 'TENT(4.8, 8.8, 6)' \
        -stim_times 9 ${stim_folder}/subjectwise/condition-scratchleftcheek_sub-${subj}_cond-${cond}_runs-*.1D 'TENT(4.8, 8.8, 6)' \
        -stim_times 10 ${stim_folder}/subjectwise/condition-scratchrightcheek_sub-${subj}_cond-${cond}_runs-*.1D 'TENT(4.8, 8.8, 6)' \
        -fout -tout -x1D ${subj_preproc_outputs}/X.xmat.1D -xjpeg ${subj_preproc_outputs}/X.jpg \
        -fitts ${subj_preproc_outputs}/fitts.${subj} \
        -errts ${subj_preproc_outputs}/errts.${subj} \
        -bucket ${subj_preproc_outputs}/stats.${subj}

  done
done
