#!/bin/bash

# Setup freesurfer and directories
export FREESURFER_HOME=/tools/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh
echo $(freesurfer --version)

export SUBJECTS_DIR=/data/elevchenko/MinMo_movements/activemotion_study/derivatives/freesurfer
export data_folder=/data/elevchenko/MinMo_movements/activemotion_study/raw_data

# Extract subject IDs dynamically from the bids_data folder
subjects=$(ls $data_folder | grep -oP '^24\d{4}[A-Z]{2}(?=_nii)')
bad_subjects=("241115CP" "241119EX" "241122ZY")


# Check if folder SUBJECTS_DIR exists
if [ -d "$SUBJECTS_DIR" ]; then
    echo "SUBJECTS_DIR exists..."
else
    echo "SUBJECTS_DIR doesn't exist. Creating one now..."
    mkdir -p "$SUBJECTS_DIR"
fi


# Run
for subj_id in $subjects; do

    for bad_subj in "${bad_subjects[@]}"; do
        if [[ "$subj_id" == "$bad_subj" ]]; then
            echo "Skipping bad subject: $subj_id"
            continue 2
        fi
    done

    input_mprages=($data_folder/${subj_id}_nii/*MPRAGE*.nii.gz)
    echo "Processing subject: $subj_id"
    recon-all \
        $(printf -- "-i %s " "${input_mprages[@]}") \
        -s sub-"$subj_id" \
        -all
done
