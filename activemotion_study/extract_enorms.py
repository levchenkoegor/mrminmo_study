import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import ttest_ind, shapiro, levene
import matplotlib.pyplot as plt
import seaborn as sns

# Function to load enorm data and timing data
def load_enorm_and_timing(subj_id, cond_i, cond_name, movement_type, timing_file):
    # Load enorm file for the subject and condition
    enorm_file = Path(deriv_fldr / f'sub-{subj_id}/sub-{subj_id}_task-mvts_cond-{cond_name}/sub-{subj_id}_task-mvts_cond-{cond_name}.results/motion_{subj_id}_enorm.1D')

    # Check if the enorm file exists
    if not enorm_file.exists():
        print(f"Enorm file not found for {subj_id} condition {cond_name}. Skipping...")
        return None, None

    enorm_data = np.loadtxt(enorm_file)

    # Load timing data (onsets only, split by runs)
    with open(timing_file, 'r') as file:
        timing_content = file.readlines()

    # Split timing content based on the condition
    # Pick first 3 runs for cond 1 and last 3 runs for cond 2
    if cond_i == 0:
        timing_content = timing_content[:3]
    elif cond_i == 1:
        timing_content = timing_content[3:]

    # Parse timing data and organize onsets by runs
    onset_times = []
    for line in timing_content:
        trials = line.strip().split()
        run_onset_times = [float(trial.split(':')[0]) for trial in trials]  # Extract only the onset times
        onset_times.append(run_onset_times)  # Append onsets for each run

    return enorm_data, onset_times

# Function to adjust timings for global time by adding cumulative run lengths
def adjust_timing_for_global(onset_times, run_lengths, sampling_interval=0.8):
    adjusted_timings = []
    cumulative_time = 0
    for run_idx, run_onsets in enumerate(onset_times):
        run_adjusted = [(onset + cumulative_time) for onset in run_onsets]  # Adjust the onsets for global time
        adjusted_timings.extend(run_adjusted)  # Append adjusted onsets for each run
        cumulative_time += run_lengths[run_idx] * sampling_interval  # Convert run lengths to time in seconds
    return adjusted_timings

# Function to get the enorm_trial and average of 5 seconds after each onset
def get_post_onset_average(enorm_data, onset_times, sampling_interval=0.8, post_onset_duration=5):
    enorm_trials = []
    averages = []
    post_onset_duration_idx = int(post_onset_duration / sampling_interval)

    for onset in onset_times:
        onset_idx = int(onset / sampling_interval)
        end_idx = onset_idx + post_onset_duration_idx
        enorm_trial = enorm_data[onset_idx:end_idx]
        avg = np.mean(enorm_trial)
        enorm_trials.append(enorm_trial)  # Store each trial
        averages.append(avg)  # Store the average

    return enorm_trials, averages

# Paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = Path(root_fldr / 'derivatives')
stim_fldr = Path(root_fldr / 'stimuli')

run_lengths = [505, 505, 505]

# Load sequences of conditions and runs from CSV
sequence_file = Path(root_fldr / 'Sequences of conditions and runs.csv')
sequence_df = pd.read_csv(sequence_file)

subjects = sequence_df['Subj #']

# List to store results
results = []

# Data loading and averaging for each subject and condition
for subj_id in subjects:
    condition_sequence = sequence_df.loc[sequence_df['Subj #'] == subj_id, 'Conditions'].values[0].split(' ')

    for cond_i, cond_name in enumerate(condition_sequence):
        # Define path
        data_file = Path(deriv_fldr / f'sub-{subj_id}/sub-{subj_id}_task-mvts_cond-{cond_name}/sub-{subj_id}_task-mvts_cond-{cond_name}.results/motion_{subj_id}_enorm.1D')
        # Check if preproc outputs exist
        if not data_file.exists():
            print(f"Warning: Data file {data_file.stem} does not exist for sub-{subj_id}, condition-{cond_name}")
            continue

        for movement_type in ['cough', 'crosslegsleftontop', 'crosslegsrightontop', 'raiselefthip', 'raiserighthip', 'lefthandtorightthigh',
                              'righthandtoleftthigh', 'sayHellotheremum', 'scratchleftcheek', 'scratchrightcheek']:

            # Define the timing file path for this movement type
            timing_file = Path(stim_fldr / f'condition-{movement_type}_run-all.1D')

            # Load enorm and timing data
            enorm_data, onset_times = load_enorm_and_timing(subj_id, cond_i, cond_name, movement_type, timing_file)

            # If enorm or timing data is missing, skip to the next iteration
            if enorm_data is None or onset_times is None:
                continue

            # Adjust onset times for global timing
            onset_times = adjust_timing_for_global(onset_times, run_lengths)

            # Get post-onset averages for the current movement
            enorm_trials, post_onset_averages = get_post_onset_average(enorm_data, onset_times)

            # Append results to the list
            for enorm_trial, avg in zip(enorm_trials, post_onset_averages):
                results.append({
                    'subject': subj_id,
                    'condition': cond_name,
                    'movement': movement_type,
                    'enorm_trial': enorm_trial.tolist(),  # Save only the specific enorm trial for the onset
                    'enorm_avg': avg
                })

# Convert results to a pandas DataFrame
df = pd.DataFrame(results)

# Save DataFrame to CSV
df.to_csv(deriv_fldr / 'df_enorm_avgs.csv')
