import pandas as pd

# Read the original dataset
df = pd.read_csv('voting_fraud_dataset.csv')

# Get fraudulent and legitimate votes
df_fraud = df[df['is_fraud'] == 1].head(2000)
df_legit = df[df['is_fraud'] == 0]

# Need 1000 legitimate votes
needed = 1000 - len(df_legit)
if needed > 0:
    # Duplicate some legitimate votes to reach 1000
    df_new_legit = pd.concat([df_legit.sample(n=needed, replace=True, random_state=42), df_legit])
else:
    df_new_legit = df_legit.head(1000)

# Combine and shuffle
df_final = pd.concat([df_new_legit, df_fraud]).sample(frac=1, random_state=42).reset_index(drop=True)

# Save updated dataset
df_final.to_csv('voting_fraud_dataset.csv', index=False)

print(f'CSV updated successfully!')
print(f'Candidate A (legitimate/is_fraud=0): {len(df_new_legit)} votes')
print(f'Candidate B (fraudulent/is_fraud=1): {len(df_fraud)} votes')
print(f'Total: {len(df_final)} votes')
