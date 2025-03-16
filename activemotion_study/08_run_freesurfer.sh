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

    # Skip if the subject is in either the bad or done list
    if [[ " ${bad_subjects[*]} " =~ " ${subj_id} " ]] || [[ " ${done_subjects[*]} " =~ " ${subj_id} " ]]; then
        echo "Skipping subject: $subj_id (bad or already processed)"
        continue
    fi

    input_mprages=($data_folder/${subj_id}_nii/*MPRAGE*.nii.gz)
    echo "Processing subject: $subj_id"
    recon-all \
        $(printf -- "-i %s " "${input_mprages[@]}") \
        -s sub-"$subj_id" \
        -all
done
