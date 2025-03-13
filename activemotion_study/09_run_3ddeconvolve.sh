#!/bin/bash


export data_folder=/data/elevchenko/MinMo_movements/activemotion_study/derivatives
export stim_folder=/data/elevchenko/MinMo_movements/activemotion_study/stimuli_tent

# Extract subject IDs dynamically, removing 'sub-' prefix and appending '_nii'
subjects=$(ls $data_folder | grep -oP '^sub-\K24\d{4}[A-Z]{2}' | sed 's/$/_nii/')
tr_counts=1515 # all runs (505, 505, 505)


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
        -iresp 1 ${subj_preproc_outputs}/iresp_cough_tent_48-88.nii.gz \
        -iresp 2 ${subj_preproc_outputs}/iresp_crosslegsleftontop_tent_48-88.nii.gz \
        -iresp 3 ${subj_preproc_outputs}/iresp_crosslegsrightontop_tent_48-88.nii.gz \
        -iresp 4 ${subj_preproc_outputs}/iresp_lefthandtorightthigh_tent_48-88.nii.gz \
        -iresp 5 ${subj_preproc_outputs}/iresp_righthandtoleftthigh_tent_48-88.nii.gz \
        -iresp 6 ${subj_preproc_outputs}/iresp_raiselefthip_tent_48-88.nii.gz \
        -iresp 7 ${subj_preproc_outputs}/iresp_raiserighthip_tent_48-88.nii.gz \
        -iresp 8 ${subj_preproc_outputs}/iresp_sayHellotheremum_tent_48-88.nii.gz \
        -iresp 9 ${subj_preproc_outputs}/iresp_scratchleftcheek_tent_48-88.nii.gz \
        -iresp 10 ${subj_preproc_outputs}/iresp_scratchrightcheek_tent_48-88.nii.gz \
        -gltsym 'SYM: +cough[0..5]' -glt_label 1 cough_overall \
        -gltsym 'SYM: +crosslegsleftontop[0..5]' -glt_label 2 crosslegsleftontop_overall \
        -gltsym 'SYM: +crosslegsrightontop[0..5]' -glt_label 3 crosslegsrightontop_overall \
        -gltsym 'SYM: +lefthandtorightthigh[0..5]' -glt_label 4 lefthandtorightthigh_overall \
        -gltsym 'SYM: +righthandtoleftthigh[0..5]' -glt_label 5 righthandtoleftthigh_overall \
        -gltsym 'SYM: +raiselefthip[0..5]' -glt_label 6 raiselefthip_overall \
        -gltsym 'SYM: +raiserighthip[0..5]' -glt_label 7 raiserighthip_overall \
        -gltsym 'SYM: +sayHellotheremum[0..5]' -glt_label 8 sayHellotheremum_overall \
        -gltsym 'SYM: +scratchleftcheek[0..5]' -glt_label 9 scratchleftcheek_overall \
        -gltsym 'SYM: +scratchrightcheek[0..5]' -glt_label 10 scratchrightcheek_overall \
        -fout -tout -x1D ${subj_preproc_outputs}/X_tent_48-88.xmat.1D -xjpeg ${subj_preproc_outputs}/X_tent_48-88.jpg \
        -fitts ${subj_preproc_outputs}/fitts_tent_48-88.${subj} \
        -errts ${subj_preproc_outputs}/errts_tent_48-88.${subj} \
        -bucket ${subj_preproc_outputs}/stats_tent_48-88.${subj}

    mv ${subj_preproc_outputs}/../sub-${subj}_task-mvts_cond-${cond}.REML_cmd ${subj_preproc_outputs}/sub-${subj}_task-mvts_cond-${cond}_tent_48-88.REML_cmd
  done
done

### Notes:
# 1 subj takes around 1.5 hours
