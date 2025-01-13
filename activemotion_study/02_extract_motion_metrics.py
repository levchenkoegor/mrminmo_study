import numpy as np
import pandas as pd
from pathlib import Path

# Function to load motion and timing data
def load_motion_and_timing(motion_file, timing_file):
    """
    Load motion data and timing data from files, skipping header lines in motion files.
    """
    # Check if the motion file exists
    if not motion_file.exists():
        print(f"Motion file not found: {motion_file.name}. Skipping...")
        return None, None

    # Load motion data, skipping header lines
    with open(motion_file, 'r') as file:
        motion_data = np.array([float(line.strip()) for line in file if not line.startswith('#')])

    # Load timing data
    if not timing_file.exists():
        print(f"Timing file not found: {timing_file}. Skipping...")
        return None, None
    with open(timing_file, 'r') as file:
        timing_content = file.readlines()

    return motion_data, timing_content


# Function to adjust timing for global run lengths
def adjust_timing_for_global(onset_times, run_lengths, sampling_interval=0.8):
    adjusted_timings = []
    cumulative_time = 0
    for run_idx, run_onsets in enumerate(onset_times):
        run_adjusted = [(onset + cumulative_time) for onset in run_onsets]
        adjusted_timings.extend(run_adjusted)
        cumulative_time += run_lengths[run_idx] * sampling_interval
    return adjusted_timings


# Function to extract trials and averages for a metric
def get_post_onset_metrics(motion_data, onset_times, sampling_interval=0.8, post_onset_duration=5):
    trials, averages = [], []
    post_onset_duration_idx = int(post_onset_duration / sampling_interval)

    for onset in onset_times:
        onset_idx = int(onset / sampling_interval)
        end_idx = onset_idx + post_onset_duration_idx
        trial = motion_data[onset_idx:end_idx]
        avg = np.mean(trial)
        trials.append(trial)
        averages.append(avg)

    return trials, averages


# Paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = Path(root_fldr / 'derivatives')
stim_fldr = Path(root_fldr / 'stimuli')

run_lengths = [505, 505, 505]  # Run lengths

# Load subject and condition sequences
sequence_file = Path(root_fldr / 'Sequences of conditions and runs.csv')
sequence_df = pd.read_csv(sequence_file)

dummydata = 0

# Exclude dummy data
if dummydata == 1:
    subjects = sequence_df[sequence_df['Subj #'] == 'dummydata_nii']['Subj #']
else:
    subjects = sequence_df[sequence_df['Subj #'] != 'dummydata_nii']['Subj #']

# Results list
results = []

# Process each subject and condition
for subj_id in subjects:
    condition_sequence = sequence_df.loc[sequence_df['Subj #'] == subj_id, 'Conditions'].values[0].split(' ')

    for cond_i, cond_name in enumerate(condition_sequence):
        cond_folder = Path(deriv_fldr / f'sub-{subj_id}/sub-{subj_id}_task-mvts_cond-{cond_name}/sub-{subj_id}_task-mvts_cond-{cond_name}.results')

        # Define metric files
        metric_files = {
            "enorm": cond_folder / f"motion_{subj_id}_enorm.1D",
            "mm": cond_folder / "mm",
            "mm_delt": cond_folder / "mm_delt",
            "outliers": cond_folder / "outcount_rall.1D",
        }

        for movement_type in ['cough', 'crosslegsleftontop', 'crosslegsrightontop', 'raiselefthip', 'raiserighthip', 'lefthandtorightthigh',
                              'righthandtoleftthigh', 'sayHellotheremum', 'scratchleftcheek', 'scratchrightcheek']:

            # Timing file
            timing_file = stim_fldr / f'condition-{movement_type}_run-all.1D'

            # Parse timing data
            _, timing_content = load_motion_and_timing(metric_files["enorm"], timing_file)
            if timing_content is None:
                continue

            # Split and adjust timing content
            if cond_i == 0:
                timing_content = timing_content[:3]
            elif cond_i == 1:
                timing_content = timing_content[3:]

            onset_times = []
            for line in timing_content:
                trials = line.strip().split()
                run_onsets = [float(trial.split(':')[0]) for trial in trials]
                onset_times.append(run_onsets)

            onset_times = adjust_timing_for_global(onset_times, run_lengths)

            # Process each metric
            for metric_name, motion_file in metric_files.items():

                motion_data, _ = load_motion_and_timing(motion_file, timing_file)
                # skip mm and mm_delt for now since it has only 505 data points (just one run)
                if motion_data is None or metric_name in ['mm', 'mm_delt']:
                    continue

                trials, averages = get_post_onset_metrics(motion_data, onset_times)

                # Append results
                for trial, avg in zip(trials, averages):
                    results.append({
                        "subject": subj_id,
                        "condition": cond_name,
                        "movement": movement_type,
                        "metric": metric_name,
                        "trial": trial.tolist(),
                        "avg": avg,
                    })

# Save to CSV
df = pd.DataFrame(results)
if dummydata == 1:
    df.to_csv(deriv_fldr / "df_motion_metrics_all_dummydata.csv", index=False)
else:
    df.to_csv(deriv_fldr / "df_motion_metrics_all.csv", index=False)

print("Metrics saved to df_motion_metrics_all.csv")
