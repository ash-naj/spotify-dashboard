import pandas as pd

df = pd.read_csv('CSV exports/ASCII.csv')

df['track'] = df['track'].str.slice(0, 15) + '...'
mini_df = df[['track', 'artist', 'hours_listened']]

print(mini_df.to_markdown(index=False))