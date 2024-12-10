#!/bin/bash

# running on dummy data?
export dummydata=1

# Paths
if [[ "$dummydata" -eq 1 ]]; then
  echo "Running the pipeline on DUMMY DATA! dummydata=$dummydata"
  export data_folder=/data/elevchenko/MinMo_movements/activemotion_study/dummydata

  # Read the sequence_runs_dummy into an array
  mapfile -t excel_states_sequences < sequence_runs_dummy.txt
  # Read the sequence_conditions_dummy into an array
  mapfile -t conditions_sequences < sequence_conditions_dummy.txt
else
  export data_folder=/data/elevchenko/MinMo_movements/activemotion_study/raw_data

  # Read the sequence_runs.txt into an array
  mapfile -t excel_states_sequences < sequence_runs.txt
  # Read the sequence_conditions.txt into an array
  mapfile -t conditions_sequences < sequence_conditions.txt
fi

export stim_folder=/data/elevchenko/MinMo_movements/activemotion_study/stimuli_tent
export n_trs_remove=10

# Initialize subject counter
export subject_index=0

echo "Make sure that the order of subjects aligned with sequence of runs in sequence_excel_states.txt file"
echo $(ls "$data_folder" | grep '_nii$')

# Function to slice specific rows from a .1D file
# This function limits to 3 rows per condition
slice_1D_file() {
    input_file="$1"
    output_file="$2"
    rows=("${!3}") # Rows to extract
    start_index="$4" # Starting index (0 for first 3 rows, 3 for the next 3 rows)

    # Empty the output file before adding rows
    : > "$output_file"

    # Extract 3 rows based on the start_index
    for ((i=0; i<3; i++)); do
        row_index=$((start_index + i))
        sed -n "${rows[$row_index]}p" "$input_file" >> "$output_file"
    done
}


# Run AFNI
for subject_dir in $(ls "$data_folder" | grep '_nii$'); do

    # Extract subject ID from the directory name (240827EL_nii, for example)
    subject_id=$(basename "$subject_dir")
    echo "Processing subject: $subject_id"

    # Get the conditions for the current subject
    current_conditions=(${conditions_sequences[$subject_index]})

    # Get the run sequence for the current subject
    current_excel_states_sequence=(${excel_states_sequences[$subject_index]})

    export cond_i=1

    for cond in "${current_conditions[@]}"; do
        export tasks=("mvts" "movies")

        for task in "${tasks[@]}"; do

            # Outputs paths
            subject_folder="$data_folder"/../derivatives/sub-"$subject_id"/sub-"$subject_dir"_task-"$task"_cond-"$cond"
            script_path="$subject_folder"/proc.sub-"$subject_id"_task-"$task"_cond-"$cond"
            output_path="$subject_folder"/output.proc.sub-"$subject_id"_task-"$task"_cond-"$cond"
            results_path="$subject_folder"/sub-"$subject_id"_task-"$task"_cond-"$cond".results

            # Check if the folder exists
            if [ ! -d "$subject_folder" ]; then
                mkdir -p "$subject_folder"
                echo "Created folder: $subject_folder"
            else
                echo "Folder already exists: $subject_folder"
            fi

            # Define temporary .1D filenames for each condition
            if [ "$cond_i" -eq 1 ]; then
                # First condition: Use the first 3 elements of the sequence
                first_three=("${current_excel_states_sequence[@]:0:3}")
                run_sequence_str=$(IFS=_; echo "${first_three[*]}")
                echo "Processing runs: $run_sequence_str"
            else
                # Second condition: Use the last 3 elements of the sequence
                last_three=("${current_excel_states_sequence[@]: -3}")
                run_sequence_str=$(IFS=_; echo "${last_three[*]}")
                echo "Processing runs: $run_sequence_str"
            fi

            # Filenames for timings files
            cough_temp_file="$stim_folder/subjectwise/condition-cough_sub-${subject_id}_cond-${cond}_runs-${run_sequence_str}.1D"
            crosslegsleftontop_temp_file="$stim_folder/subjectwise/condition-crosslegsleftontop_sub-${subject_id}_cond-${cond}_runs-${run_sequence_str}.1D"
            crosslegsrightontop_temp_file="$stim_folder/subjectwise/condition-crosslegsrightontop_sub-${subject_id}_cond-${cond}_runs-${run_sequence_str}.1D"
            raiselefthip_temp_file="$stim_folder/subjectwise/condition-raiselefthip_sub-${subject_id}_cond-${cond}_runs-${run_sequence_str}.1D"
            raiserighthip_temp_file="$stim_folder/subjectwise/condition-raiserighthip_sub-${subject_id}_cond-${cond}_runs-${run_sequence_str}.1D"
            righthandtoleftthigh_temp_file="$stim_folder/subjectwise/condition-righthandtoleftthigh_sub-${subject_id}_cond-${cond}_runs-${run_sequence_str}.1D"
            lefthandtorightthigh_temp_file="$stim_folder/subjectwise/condition-lefthandtorightthigh_sub-${subject_id}_cond-${cond}_runs-${run_sequence_str}.1D"
            sayHellotheremum_temp_file="$stim_folder/subjectwise/condition-sayHellotheremum_sub-${subject_id}_cond-${cond}_runs-${run_sequence_str}.1D"
            scratchleftcheek_temp_file="$stim_folder/subjectwise/condition-scratchleftcheek_sub-${subject_id}_cond-${cond}_runs-${run_sequence_str}.1D"
            scratchrightcheek_temp_file="$stim_folder/subjectwise/condition-scratchrightcheek_sub-${subject_id}_cond-${cond}_runs-${run_sequence_str}.1D"

            # Pick correct run files based on condition number and map them using the filename postfix
            if [ "$cond_i" -eq 1 ] && [ "$dummydata" -eq 0 ]; then
                export run1=4
                export run2=8
                export run3=12
                export movie=16
                export phasereverse=6
                export mprage=2

                # First condition: Extract the first 3 rows
                slice_1D_file "$stim_folder/condition-cough_run-all.1D" "$cough_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-crosslegsleftontop_run-all.1D" "$crosslegsleftontop_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-crosslegsrightontop_run-all.1D" "$crosslegsrightontop_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-raiselefthip_run-all.1D" "$raiselefthip_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-raiserighthip_run-all.1D" "$raiserighthip_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-righthandtoleftthigh_run-all.1D" "$righthandtoleftthigh_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-lefthandtorightthigh_run-all.1D" "$lefthandtorightthigh_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-sayHellotheremum_run-all.1D" "$sayHellotheremum_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-scratchleftcheek_run-all.1D" "$scratchleftcheek_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-scratchrightcheek_run-all.1D" "$scratchrightcheek_temp_file" current_excel_states_sequence[@] 0
            elif [ "$cond_i" -eq 2 ] && [ "$dummydata" -eq 0 ]; then
                export run1=22
                export run2=26
                export run3=30
                export movie=34
                export phasereverse=24
                export mprage=20

                # Second condition: Extract the next 3 rows (starting at index 3)
                slice_1D_file "$stim_folder/condition-cough_run-all.1D" "$cough_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-crosslegsleftontop_run-all.1D" "$crosslegsleftontop_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-crosslegsrightontop_run-all.1D" "$crosslegsrightontop_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-raiselefthip_run-all.1D" "$raiselefthip_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-raiserighthip_run-all.1D" "$raiserighthip_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-righthandtoleftthigh_run-all.1D" "$righthandtoleftthigh_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-lefthandtorightthigh_run-all.1D" "$lefthandtorightthigh_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-sayHellotheremum_run-all.1D" "$sayHellotheremum_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-scratchleftcheek_run-all.1D" "$scratchleftcheek_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-scratchrightcheek_run-all.1D" "$scratchrightcheek_temp_file" current_excel_states_sequence[@] 3
            elif [ "$cond_i" -eq 1 ] && [ "$dummydata" -eq 1 ]; then
                # make dummy data in orig
                3drefit -space ORIG "$data_folder"/"$subject_id"/task-movt_stationary_dummy_1.nii
                3drefit -space ORIG "$data_folder"/"$subject_id"/task-movt_stationary_dummy_2.nii
                3drefit -space ORIG "$data_folder"/"$subject_id"/task-movt_stationary_dummy_3.nii
                3drefit -view orig "$data_folder"/"$subject_id"/task-movt_stationary_dummy_1.nii
                3drefit -view orig "$data_folder"/"$subject_id"/task-movt_stationary_dummy_2.nii
                3drefit -view orig "$data_folder"/"$subject_id"/task-movt_stationary_dummy_3.nii

                # make dummy data with 0.8s TR
                3drefit -TR 0.8 "$data_folder"/"$subject_id"/task-movt_stationary_dummy_1.nii
                3drefit -TR 0.8 "$data_folder"/"$subject_id"/task-movt_stationary_dummy_2.nii
                3drefit -TR 0.8 "$data_folder"/"$subject_id"/task-movt_stationary_dummy_3.nii

                export run1=1
                export run2=2
                export run3=3
                #export movie=24
                export phasereverse=7
                export mprage=2

                # First condition: Extract the first 3 rows
                slice_1D_file "$stim_folder/condition-cough_run-all.1D" "$cough_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-crosslegsleftontop_run-all.1D" "$crosslegsleftontop_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-crosslegsrightontop_run-all.1D" "$crosslegsrightontop_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-raiselefthip_run-all.1D" "$raiselefthip_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-raiserighthip_run-all.1D" "$raiserighthip_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-righthandtoleftthigh_run-all.1D" "$righthandtoleftthigh_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-lefthandtorightthigh_run-all.1D" "$lefthandtorightthigh_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-sayHellotheremum_run-all.1D" "$sayHellotheremum_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-scratchleftcheek_run-all.1D" "$scratchleftcheek_temp_file" current_excel_states_sequence[@] 0
                slice_1D_file "$stim_folder/condition-scratchrightcheek_run-all.1D" "$scratchrightcheek_temp_file" current_excel_states_sequence[@] 0
            elif [ "$cond_i" -eq 2 ] && [ "$dummydata" -eq 1 ]; then
                # make dummy data in orig
                3drefit -space ORIG "$data_folder"/"$subject_id"/task-movt_moving_dummy_4.nii
                3drefit -space ORIG "$data_folder"/"$subject_id"/task-movt_moving_dummy_5.nii
                3drefit -space ORIG "$data_folder"/"$subject_id"/task-movt_moving_dummy_6.nii
                3drefit -view orig "$data_folder"/"$subject_id"/task-movt_moving_dummy_4.nii
                3drefit -view orig "$data_folder"/"$subject_id"/task-movt_moving_dummy_5.nii
                3drefit -view orig "$data_folder"/"$subject_id"/task-movt_moving_dummy_6.nii

                # make dummy data with 0.8s TR
                3drefit -TR 0.8 "$data_folder"/"$subject_id"/task-movt_moving_dummy_4.nii
                3drefit -TR 0.8 "$data_folder"/"$subject_id"/task-movt_moving_dummy_5.nii
                3drefit -TR 0.8 "$data_folder"/"$subject_id"/task-movt_moving_dummy_6.nii

                export run1=4
                export run2=5
                export run3=6
                #export movie=24
                export phasereverse=7
                export mprage=2

                # Second condition: Extract the next 3 rows (starting at index 3)
                slice_1D_file "$stim_folder/condition-cough_run-all.1D" "$cough_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-crosslegsleftontop_run-all.1D" "$crosslegsleftontop_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-crosslegsrightontop_run-all.1D" "$crosslegsrightontop_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-raiselefthip_run-all.1D" "$raiselefthip_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-raiserighthip_run-all.1D" "$raiserighthip_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-righthandtoleftthigh_run-all.1D" "$righthandtoleftthigh_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-lefthandtorightthigh_run-all.1D" "$lefthandtorightthigh_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-sayHellotheremum_run-all.1D" "$sayHellotheremum_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-scratchleftcheek_run-all.1D" "$scratchleftcheek_temp_file" current_excel_states_sequence[@] 3
                slice_1D_file "$stim_folder/condition-scratchrightcheek_run-all.1D" "$scratchrightcheek_temp_file" current_excel_states_sequence[@] 3
            fi

            # afni proc py for movements task
            if [ "$task" = "mvts" ]; then
              afni_proc.py \
                  -subj_id "$subject_id" \
                  -script "$script_path" \
                  -out_dir "$results_path" \
                  -dsets "$data_folder"/"$subject_id"/*movt*_"$run1".nii \
                         "$data_folder"/"$subject_id"/*movt*_"$run2".nii \
                         "$data_folder"/"$subject_id"/*movt*_"$run3".nii \
                  -blip_reverse_dset "$data_folder"/"$subject_id"/*PErev*_"$phasereverse".nii \
                  -blocks tcat align tlrc volreg blur scale regress \
                  -radial_correlate_blocks volreg regress \
                  -tlrc_base MNI152_2009_template.nii.gz \
                  -tcat_remove_first_trs "$n_trs_remove" \
                  -copy_anat "$data_folder"/"$subject_id"/*MPRAGE*_"$mprage".nii \
                  -volreg_align_to first \
                  -volreg_opts_vr -twopass -twodup -maxdisp1D mm \
                  -volreg_compute_tsnr yes \
                  -remove_preproc_files \
                  -blur_size 4 \
                  -regress_motion_per_run \
                  -regress_run_clustsim no \
                  -regress_show_df_info yes \
                  -regress_reml_exec \
                  -regress_opts_3dD -num_stimts 10 -local_times \
                      -stim_label 1 cough \
                      -stim_label 2 crosslegsleftontop \
                      -stim_label 3 crosslegsrightontop \
                      -stim_label 4 raiselefthip \
                      -stim_label 5 raiserighthip \
                      -stim_label 6 righthandtoleftthigh \
                      -stim_label 7 lefthandtorightthigh \
                      -stim_label 8 sayHellotheremum \
                      -stim_label 9 scratchleftcheek \
                      -stim_label 10 scratchrightcheek \
                      -stim_times 1 "$cough_temp_file" 'TENT(0, 3.2, 5)' \
                      -stim_times 2 "$crosslegsleftontop_temp_file" 'TENT(0, 3.2, 5)' \
                      -stim_times 3 "$crosslegsrightontop_temp_file" 'TENT(0, 3.2, 5)' \
                      -stim_times 4 "$raiselefthip_temp_file" 'TENT(0, 3.2, 5)' \
                      -stim_times 5 "$raiserighthip_temp_file" 'TENT(0, 3.2, 5)' \
                      -stim_times 6 "$righthandtoleftthigh_temp_file" 'TENT(0, 3.2, 5)' \
                      -stim_times 7 "$lefthandtorightthigh_temp_file" 'TENT(0, 3.2, 5)' \
                      -stim_times 8 "$sayHellotheremum_temp_file" 'TENT(0, 3.2, 5)' \
                      -stim_times 9 "$scratchleftcheek_temp_file" 'TENT(0, 3.2, 5)' \
                      -stim_times 10 "$scratchrightcheek_temp_file" 'TENT(0, 3.2, 5)' \
                      -gltsym 'SYM: cough crosslegsleftontop crosslegsrightontop raiselefthip raiserighthip righthandtoleftthigh lefthandtorightthigh sayHellotheremum scratchleftcheek scratchrightcheek' \
                      -glt_label 1 'mvts_avg' \
                  -html_review_style pythonic

              tcsh -xef "$script_path" 2>&1 | tee "$output_path"

              # 3dDeconvolve with TENT again but diff func parameters (copied from afni proc py output)
              tcsh 3dDeconvolve -input "$results_path"/pb04."$subject_id".r*.scale+orig.HEAD \
                  -ortvec mot_demean.r01.1D mot_demean_r01 \
                  -ortvec mot_demean.r02.1D mot_demean_r02 \
                  -ortvec mot_demean.r03.1D mot_demean_r03 \
                  -polort 3 -float \
                  -num_stimts 0 \
                  -num_stimts 10 \
                  -local_times \
                  -stim_label 1 cough \
                  -stim_label 2 crosslegsleftontop \
                  -stim_label 3 crosslegsrightontop \
                  -stim_label 4 raiselefthip \
                  -stim_label 5 raiserighthip \
                  -stim_label 6 righthandtoleftthigh \
                  -stim_label 7 lefthandtorightthigh \
                  -stim_label 8 sayHellotheremum \
                  -stim_label 9 scratchleftcheek \
                  -stim_label 10 scratchrightcheek \
                  -stim_times 1 "$cough_temp_file" 'TENT(4.8, 8.8, 6)' \
                  -stim_times 2 "$crosslegsleftontop_temp_file" 'TENT(4.8, 8.8, 6)' \
                  -stim_times 3 "$crosslegsrightontop_temp_file" 'TENT(4.8, 8.8, 6)' \
                  -stim_times 4 "$raiselefthip_temp_file" 'TENT(4.8, 8.8, 6)' \
                  -stim_times 5 "$raiserighthip_temp_file" 'TENT(4.8, 8.8, 6)' \
                  -stim_times 6 "$righthandtoleftthigh_temp_file" 'TENT(4.8, 8.8, 6)' \
                  -stim_times 7 "$lefthandtorightthigh_temp_file" 'TENT(4.8, 8.8, 6)' \
                  -stim_times 8 "$sayHellotheremum_temp_file" 'TENT(4.8, 8.8, 6)' \
                  -stim_times 9 "$scratchleftcheek_temp_file" 'TENT(4.8, 8.8, 6)' \
                  -stim_times 10 "$scratchrightcheek_temp_file" 'TENT(4.8, 8.8, 6)' \
                  -gltsym 'SYM: cough crosslegsleftontop crosslegsrightontop raiselefthip raiserighthip righthandtoleftthigh lefthandtorightthigh sayHellotheremum scratchleftcheek scratchrightcheek' \
                  -glt_label 1 'mvts_avg' \
                  -fout -tout -x1D "$results_path"/X_tent48-88.xmat.1D -xjpeg "$results_path"/X_48-88.jpg \
                  -fitts "$results_path"/fitts_48-88."$subject_id" \
                  -errts "$results_path"/errts_48-88."$subject_id" \
                  -bucket "$results_path"/stats_48-88."$subject_id"

              # -- use 3dTproject to project out regression matrix --
              #    (make errts like 3dDeconvolve, but more quickly)
              tcsh 3dTproject -polort 0 -input "$results_path"/pb04."$subject_id".r*.scale+orig.HEAD \
                         -ort X_48-88.xmat.1D -prefix "$results_path"/errts_48-88."$subject_id".tproject

            # afni proc py for movie-watching task
            elif [ "$task" = "movies" ]; then
              afni_proc.py \
                  -subj_id "$subject_id" \
                  -script "$script_path"  \
                  -out_dir "$results_path" \
                  -dsets "$data_folder"/"$subject_id"/*film*_"$movie".nii \
                  -blip_reverse_dset "$data_folder"/"$subject_id"/*PErev*_"$phasereverse".nii \
                  -blocks tcat align tlrc volreg blur scale regress \
                  -radial_correlate_blocks volreg regress \
                  -tlrc_base MNI152_2009_template.nii.gz \
                  -tcat_remove_first_trs "$n_trs_remove" \
                  -copy_anat "$data_folder"/"$subject_id"/*MPRAGE*_"$mprage".nii \
                  -volreg_align_to first \
                  -volreg_opts_vr -twopass -twodup -maxdisp1D mm \
                  -volreg_compute_tsnr yes \
                  -html_review_style pythonic

              tcsh -xef "$script_path" 2>&1 | tee "$output_path"
            fi

        done
        cond_i=$((cond_i + 1))
    done
    subject_index=$((subject_index + 1))
done

# Some links:
# https://discuss.afni.nimh.nih.gov/t/tent-models-and-3dremlfit/2594
