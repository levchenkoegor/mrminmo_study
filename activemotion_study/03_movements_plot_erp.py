import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path
from collections import defaultdict

# Function to parse timing data
def parse_timing_data(timing_content):
    onset_durations = []
    for line in timing_content:
        events = line.strip().split()  # Split by space
        onset_duration_pairs = [(float(onset), float(duration)) for onset, duration in (event.split(':') for event in events)]
        onset_durations.append(onset_duration_pairs)
    return onset_durations

# Function to adjust timings for global time by adding cumulative run lengths
def adjust_timing_for_global(onset_durations, run_lengths):
    adjusted_timings = []
    cumulative_time = 0
    for run_idx, run in enumerate(onset_durations):
        run_adjusted = [(onset + cumulative_time, duration) for onset, duration in run]
        adjusted_timings.append(run_adjusted)
        cumulative_time += run_lengths[run_idx] * sampling_interval  # Convert run lengths to time in seconds
    return adjusted_timings

# Function to extract ERP data with NaN padding
def extract_corrected_erp(df, timing_data, pre_onset_duration, post_onset_duration, sampling_interval):
    erp_data = []
    total_length = len(df)
    window_size = int((pre_onset_duration + post_onset_duration) / sampling_interval) + 1  # +1 for inclusive endpoint

    for line in timing_data:
        for onset, duration in line:
            onset_idx = int(onset / sampling_interval)  # Convert onset time to index
            start_idx = onset_idx - int(pre_onset_duration / sampling_interval)
            end_idx = onset_idx + int(post_onset_duration / sampling_interval)

            # Initialize NaN array for the current trial window
            erp_window = np.full((window_size, df.shape[1]), np.nan)

            # Calculate valid indices for extraction
            valid_start_idx = max(0, start_idx)
            valid_end_idx = min(end_idx, total_length - 1)

            # Define where to insert the valid data within the NaN-padded window
            insert_start_idx = valid_start_idx - start_idx
            insert_end_idx = insert_start_idx + (valid_end_idx - valid_start_idx) + 1

            # Insert the valid data into the NaN-padded window
            erp_window[insert_start_idx:insert_end_idx] = df.iloc[valid_start_idx:valid_end_idx + 1].values

            # Append the ERP window
            erp_data.append(erp_window)

    return np.array(erp_data)

# Function to plot each trial in a separate subplot and save the plots
def plot_each_trial_and_save(erp_data, time_window_corrected, headers, movement_type, cond_name, subj_id, save_dir):
    num_trials = erp_data.shape[0]
    num_columns = 3  # Number of columns for subplot layout
    num_rows = int(np.ceil(num_trials / num_columns))  # Number of rows

    # Ensure save directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Plot for roll, pitch, yaw (degrees)
    fig, axs = plt.subplots(num_rows, num_columns, figsize=(15, 10))
    axs = axs.flatten()  # Flattening for easy iteration

    for i, trial in enumerate(erp_data):
        # Demean the trial
        trial_normalized = trial - np.nanmean(trial, axis=0)

        for j, column in enumerate(headers[:3]):  # First three columns are roll, pitch, yaw
            axs[i].plot(time_window_corrected, trial_normalized[:, j], label=column)

        axs[i].set_title(f'Trial {i + 1}')
        axs[i].set_xlabel('Time (seconds)')
        axs[i].set_ylabel('Degrees')
        axs[i].legend(loc='upper right')
        axs[i].grid(True)

    plt.suptitle(f'ERP for Roll, Pitch, Yaw (Degrees), movement-{movement_type}_cond-{cond_name}, {subj_id}')
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout to fit the title

    # Save the plot
    roll_pitch_yaw_filename = f'sub-{subj_id}_movement-{movement_type}_cond-{cond_name}_roll_pitch_yaw.png'
    plt.savefig(os.path.join(save_dir, roll_pitch_yaw_filename))
    print(f"File saved: {roll_pitch_yaw_filename}")  # Print message when file is saved
    plt.close(fig)

    # Plot for dS, dL, dP (mm)
    fig, axs = plt.subplots(num_rows, num_columns, figsize=(15, 10))
    axs = axs.flatten()  # Flattening for easy iteration

    for i, trial in enumerate(erp_data):
        # Demean the trial
        trial_normalized = trial - np.nanmean(trial, axis=0)

        for j, column in enumerate(headers[3:]):  # Last three columns are dS, dL, dP
            axs[i].plot(time_window_corrected, trial_normalized[:, j + 3], label=column)

        axs[i].set_title(f'Trial {i + 1}')
        axs[i].set_xlabel('Time (seconds)')
        axs[i].set_ylabel('Millimeters')
        axs[i].legend(loc='upper right')
        axs[i].grid(True)

    plt.suptitle(f'ERP for dS, dL, dP (mm), movement-{movement_type}_cond-{cond_name}, {subj_id}')
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout to fit the title

    # Save the plot
    dS_dL_dP_filename = f'sub-{subj_id}_movement-{movement_type}_cond-{cond_name}_dS_dL_dP.png'
    plt.savefig(os.path.join(save_dir, dS_dL_dP_filename))
    print(f"File saved: {dS_dL_dP_filename}")  # Print message when file is saved
    plt.close(fig)

# Paths
root_fldr = Path('/data/elevchenko/MinMo_movements/activemotion_study')
deriv_fldr = Path(root_fldr / 'derivatives')
stim_fldr = Path(root_fldr / 'stimuli')

run_lengths = [505, 505, 505]

# Define parameters for ERP extraction
sampling_interval = 0.8
pre_onset_duration = 3  # seconds before onset
post_onset_duration = 8  # seconds after onset

# Load sequences of conditions and runs from CSV
sequence_file = Path(root_fldr / 'Sequences of conditions and runs.csv')
sequence_df = pd.read_csv(sequence_file)

# Dictionary to collect ERPs across subjects
erp_by_cond_and_movement = defaultdict(list)

subjects = sequence_df['Subj #']

# main
for subj_id in subjects:
    condition_sequence = sequence_df.loc[sequence_df['Subj #'] == subj_id, 'Conditions'].values[0].split(' ')

    for cond_i, cond_name in enumerate(condition_sequence):
        # Define path
        data_file = Path(deriv_fldr / f'sub-{subj_id}/sub-{subj_id}_task-mvts_cond-{cond_name}/sub-{subj_id}_task-mvts_cond-{cond_name}.results/dfile_rall.1D')

        # Check if preproc outputs exist
        if not data_file.exists():
            print(f"Warning: Data file {data_file.stem} does not exist for sub-{subj_id}, condition-{cond_name}")
            continue

        for movement_type in ['cough', 'crosslegsleftontop', 'crosslegsrightontop', 'raiselefthip', 'raiserighthip', 'lefthandtorightthigh',
                              'righthandtoleftthigh', 'sayHellotheremum', 'scratchleftcheek', 'scratchrightcheek']:
            # Define path
            timing_file = Path(stim_fldr / f'condition-{movement_type}_run-all.1D')

            # Load the movement data and timing data
            data = np.loadtxt(data_file)
            df = pd.DataFrame(data, columns=['roll', 'pitch', 'yaw', 'dS', 'dL', 'dP'])

            # Get the run sequence for the current subject from the CSV file
            run_sequence = sequence_df.loc[sequence_df['Subj #'] == subj_id, 'Runs'].values[0]
            run_sequence = list(map(int, run_sequence.split()))  # Convert "6 5 4 3 2 1" into a list of integers

            # Get the first 3 runs for condition 1 and second 3 runs for condition 2
            if cond_i+1 == 1:
                run_sequence_cond = run_sequence[:3]  # First 3 runs for the first condition
            elif cond_i+1 == 2:
                # Check if the participant has at least 6 runs
                if len(run_sequence) >= 6:
                    run_sequence_cond = run_sequence[3:6]  # Second 3 runs for the second condition
                else:
                    print(f"Subject {subj_id} did not perform the second condition.")
                    continue  # Skip to the next condition

            # Load the timing content (all 6 runs)
            with open(timing_file, 'r') as file:
                timing_content = file.readlines()  # Load all 6 lines (runs)

            # Select the lines based on the run sequence for the current condition
            timing_content_selected = [timing_content[run_idx - 1] for run_idx in run_sequence_cond]  # Adjust for zero-indexing

            # Parse the selected timing data
            timing_data = parse_timing_data(timing_content_selected)

            # Exceptions
            # ...

            # Adjust the timing to global time points
            timing_data_global = adjust_timing_for_global(timing_data, run_lengths)

            # Extract ERP data
            erp_data_corrected = extract_corrected_erp(df, timing_data_global, pre_onset_duration, post_onset_duration, sampling_interval)

            # Store ERP data for collapsing across subjects later
            erp_by_cond_and_movement[(cond_name, movement_type)].append(erp_data_corrected)

            # Time window for plotting
            window_size = int((pre_onset_duration + post_onset_duration) / sampling_interval) + 1
            time_window_corrected = np.linspace(-pre_onset_duration, post_onset_duration, window_size)

            # Plot each trial separately and save the plots
            #plot_each_trial_and_save(erp_data_corrected, time_window_corrected, df.columns, movement_type, cond_name, subj_id, Path(deriv_fldr / 'ERP-like_plots' / subj_id))

# Plot grand average ERP across subjects (with trial-wise demeaning)
def plot_grand_average_erp(erp_dict, time_window, headers, save_dir):
    os.makedirs(save_dir, exist_ok=True)

    for (cond_name, movement_type), list_of_erp_arrays in erp_dict.items():
        if cond_name == 'MinMo':
            continue # Skip minmo for now

        # Concatenate all ERP trials from all subjects
        all_erps = np.concatenate(list_of_erp_arrays, axis=0)  # shape: (total_trials, time, channels)

        # Demean each trial (zero-center across time for each channel)
        all_erps_demeaned = all_erps - np.nanmean(all_erps, axis=1, keepdims=True)

        # Compute mean and SEM
        mean_erp = np.nanmean(all_erps_demeaned, axis=0)  # shape: (time, channels)
        sem_erp = np.nanstd(all_erps_demeaned, axis=0) / np.sqrt(np.sum(~np.isnan(all_erps_demeaned), axis=0))

        # --- Plot yaw, pitch, roll ---
        fig, ax = plt.subplots(figsize=(10, 6))
        for j, column in enumerate(headers[:3]):
            ax.errorbar(time_window, mean_erp[:, j], yerr=sem_erp[:, j], label=column, capsize=2)
        ax.set_title(f'Grand Avg ERP (Yaw, Pitch, Roll)\ncond-{cond_name}, movement-{movement_type}')
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Degrees (demeaned)')
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        filename = f'grandavg_movement-{movement_type}_cond-{cond_name}_roll_pitch_yaw.png'
        fig.savefig(os.path.join(save_dir, filename))
        plt.close(fig)

        # --- Plot dS, dL, dP ---
        fig, ax = plt.subplots(figsize=(10, 6))
        for j, column in enumerate(headers[3:]):
            ax.errorbar(time_window, mean_erp[:, j + 3], yerr=sem_erp[:, j + 3], label=column, capsize=2)
        ax.set_title(f'Grand Avg ERP (dS, dL, dP)\ncond-{cond_name}, movement-{movement_type}')
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Millimeters (demeaned)')
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        filename = f'grandavg_movement-{movement_type}_cond-{cond_name}_dS_dL_dP.png'
        fig.savefig(os.path.join(save_dir, filename))
        plt.close(fig)

# Define where to save the grand average plots
grand_avg_save_dir = deriv_fldr / 'ERP-like_plots' / 'grand_averages'
plot_grand_average_erp(erp_by_cond_and_movement, time_window_corrected, df.columns, grand_avg_save_dir)
