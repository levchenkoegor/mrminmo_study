#!/bin/bash

###
# The script does preprocessing using afni_proc.py function for both Movies dataset (NNdb and BackToTheFuture)
###

export proj_folder=/data/elevchenko/MinMo_movements/retrospective_study
max_jobs=8  # Set maximum number of parallel jobs

for dataset in "NNdb" "BTF"; do

  if [ "$dataset" == "NNdb" ]; then
    export raw_data_folder=/data/ds002837
    export data_deriv="$proj_folder"/derivatives_nndb
    subjects=$(ls -d "$raw_data_folder"/sub-* | grep -oP 'sub-\K\d+' | sort -n)
    #subjects="1 2" # just for a test
    n_trs_remove=8
  elif [ "$dataset" == "BTF" ]; then
    export raw_data_folder=/data/elevchenko/MovieProject2/bids_data
    export data_deriv="$proj_folder"/derivatives_btf
    subjects=$(ls -d "$raw_data_folder"/sub-* | grep -oP 'sub-\K\d+' | sort -n)
    #subjects="01 02" # just for a test
    n_trs_remove="8 16 16"
  fi


  for subj_id in $subjects; do
    (
      # Start timing
      start_time=$(date +%s)

      echo "Processing: dataset - ${dataset}, subject - ${subj_id}"
      subject_folder="$data_deriv"/sub-"$subj_id"
      mkdir -p "$subject_folder"
      script_path="$subject_folder"/proc.sub-"$subj_id"
      output_path="$subject_folder"/output.proc.sub-"$subj_id"
      results_path="$subject_folder"/sub-"$subj_id".results

      # Adjust paths to files, nndb didn't have a predefined pause so the number of runs can be basically anything
      if [ "$dataset" == "NNdb" ]; then
        dsets=("${raw_data_folder}"/sub-"${subj_id}"/func/*_bold.nii.gz)
        echo "${dsets[@]}"
      elif [ "$dataset" == "BTF" ]; then
        dsets=("${raw_data_folder}"/sub-"${subj_id}"/ses-001/func/*_bold.nii.gz)
        echo "${dsets[@]}"

        if [ "$subj_id" == "24" ]; then
            dsets=(
                "$raw_data_folder/sub-24/ses-001/func/sub-24_ses-001_task-backtothefuture_acq-beforepause_run-001_bold.nii.gz"
                "$raw_data_folder/sub-24/ses-001/func/sub-24_ses-001_task-backtothefuture_acq-afterpause_run-001_bold.nii.gz"
                "$raw_data_folder/sub-24/ses-001/func/sub-24_ses-001_task-backtothefuture_run-002_bold.nii.gz"
                "$raw_data_folder/sub-24/ses-001/func/sub-24_ses-001_task-backtothefuture_run-003_bold.nii.gz"
            )
            n_trs_remove="8 16 16 16"
        elif [ "$subj_id" == "36" ]; then
            dsets=(
                "$raw_data_folder/sub-36/ses-001/func/sub-36_ses-001_task-backtothefuture_acq-beforepause_run-001_bold.nii.gz"
                "$raw_data_folder/sub-36/ses-001/func/sub-36_ses-001_task-backtothefuture_acq-afterpause_run-001_bold.nii.gz"
                "$raw_data_folder/sub-36/ses-001/func/sub-36_ses-001_task-backtothefuture_run-002_bold.nii.gz"
                "$raw_data_folder/sub-36/ses-001/func/sub-36_ses-001_task-backtothefuture_run-003_bold.nii.gz"
            )
            n_trs_remove="8 16 16 16"
        fi
      fi


      afni_proc.py \
          -subj_id "$subj_id" \
          -script "$script_path" \
          -out_dir "$results_path" \
          -dsets "${dsets[@]}" \
          -blocks tcat volreg scale \
          -tcat_remove_first_trs $n_trs_remove \
          -volreg_align_to first \
          -volreg_opts_vr -twopass -twodup -maxdisp1D mm \
          -volreg_compute_tsnr yes \
          -remove_preproc_files \
          -html_review_style pythonic

      tcsh -xef "$script_path" 2>&1 | tee "$output_path"

      # End timing
      end_time=$(date +%s)

      # Calculate elapsed time
      elapsed_time=$((end_time - start_time))
      echo "Processing time for subject ${subj_id}: ${elapsed_time} seconds. Dataset - ${dataset}"
    ) & # Run in the background

    # Limit number of parallel jobs
    while [ "$(jobs -r | wc -l)" -ge "$max_jobs" ]; do
      sleep 1
    done

  done
done


# Useful links:
# https://github.com/lab-lab/nndb/blob/master/fMRI_preprocessing/preprocessing_functional_slice_timing.sh#L24C1-L24C74