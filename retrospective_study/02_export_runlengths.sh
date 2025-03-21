#!/bin/bash

###
# The script checks run lengths and durations, with added run index
# Outputs a CSV with:
# dataset,subject,filename,run_i,n_trs,run_length_minutes
###

export proj_folder=/data/elevchenko/MinMo_movements/retrospective_study
export output_folder=/egor/MinMo_movements/retrospective_study
output_csv="${proj_folder}/run_lengths.csv"

# Header
echo "dataset,subject,filename,run_i,n_trs,run_length_minutes" > "$output_csv"

# === NNDb ===
raw_data_folder_nndb=/data/ds002837
subjects_nndb=$(ls -d "$raw_data_folder_nndb"/sub-* | grep -oP 'sub-\K\d+' | sort -n)
TR_nndb=1.0  # seconds

for subj_id in $subjects_nndb; do
  func_folder="${raw_data_folder_nndb}/sub-${subj_id}/func"
  for run_file in "$func_folder"/*_bold.nii.gz; do
    if [ -f "$run_file" ]; then
      n_trs=$(3dinfo -nt "$run_file")
      run_length_minutes=$(echo "scale=2; ($n_trs * $TR_nndb) / 60" | bc)
      filename=$(basename "$run_file")
      run_i=$(echo "$filename" | grep -oP 'run-\K\d+')
      echo "NNdb,${subj_id},${filename},${run_i},${n_trs},${run_length_minutes}" >> "$output_csv"
    fi
  done
done

# === BTF: only sub-10 ===
subj_id=10
raw_data_folder_btf=/data/elevchenko/MovieProject2/bids_data
func_folder_btf="${raw_data_folder_btf}/sub-${subj_id}/ses-001/func"
TR_btf=1.5  # seconds

for run_file in "$func_folder_btf"/*_bold.nii.gz; do
  if [ -f "$run_file" ]; then
    n_trs=$(3dinfo -nt "$run_file")
    run_length_minutes=$(echo "scale=2; ($n_trs * $TR_btf) / 60" | bc)
    filename=$(basename "$run_file")
    run_i=$(echo "$filename" | grep -oP 'run-\K\d+')
    echo "BTF,${subj_id},${filename},${run_i},${n_trs},${run_length_minutes}" >> "$output_csv"
  fi
done

echo "Saved run info to: $output_csv"
