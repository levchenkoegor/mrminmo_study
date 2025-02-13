#!/bin/bash

# Setup freesurfer and directories
export FREESURFER_HOME=/tools/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh

export SUBJECTS_DIR=/data/elevchenko/MinMo_movements/activemotion_study/derivatives/freesurfer
export data_folder=/data/elevchenko/MinMo_movements/activemotion_study/raw_data/

# Extract subject IDs dynamically from the bids_data folder
subjects=$(ls $data_folder | grep -oP '^24\d{4}[A-Z]{2}(?=_nii)')
bad_subjects=("241115CP_nii" "241119EX_nii" "241122ZY_nii")


# Check if folder SUBJECTS_DIR exists
if [ -d "$SUBJECTS_DIR" ]; then
    echo "SUBJECTS_DIR exists..."
else
    echo "SUBJECTS_DIR doesn't exist. Creating one now..."
    mkdir -p "$SUBJECTS_DIR"
fi

subjects="241031DC_nii 241031JC_nii"
# Run
for subj_id in $subjects; do

    # Check if the subject ID is in the list of bad subjects
    if [[ " ${bad_subjects[@]} " =~ " ${subj_id} " ]]; then
        echo "Skipping bad subject: $subj_id"
        subject_index=$((subject_index + 1))
        continue
    fi

    echo "Processing subject: $subject_id"
    input_mprages="$data_folder/${subj_id}/*MPRAGE*.nii.gz"


    echo $(freesurfer --version)
    echo "$subj_id freesurfer processing..."

    recon-all \
        $(printf -- "-i %s " $input_mprages) \
        -s sub-"$subj_id" \
        -all
done

