import pandas as pd

# Load the data
df = pd.read_csv("run_lengths.csv")  # Adjust path if needed

# Get unique BTF run lengths (should be identical for all runs)
btf_lengths = df[df['dataset'] == 'BTF']['run_length_minutes'].unique()

# Filter NNDb data
nndb_df = df[df['dataset'] == 'NNdb']

# Find NNDb subjects with exactly 3 runs
nndb_run_counts = nndb_df.groupby('subject').size()
subjects_with_3_runs = nndb_run_counts[nndb_run_counts == 3].index

# Set tolerance in minutes
tolerance = 10

# Check if all 3 runs for a subject match BTF run length within tolerance
matching_subjects = []
for subject in subjects_with_3_runs:
    subject_runs = nndb_df[nndb_df['subject'] == subject]['run_length_minutes'].values
    if all(any(abs(run_len - btf_len) <= tolerance for btf_len in btf_lengths) for run_len in subject_runs):
        matching_subjects.append(subject)

# Print results
print(f"Number of NNDb subjects with 3 BTF-like runs (±{tolerance} min): {len(matching_subjects)}")
print("Matching subjects:", matching_subjects)
