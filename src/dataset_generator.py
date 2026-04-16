import re
import requests
import pandas as pd
from datasets import load_dataset
from io import StringIO

# Load dataset
ds = load_dataset("ashraq/financial-news-articles")
df = ds["train"].to_pandas()

# Extract publication date from first 100 characters only, 2010-2019 only
def extract_date(text):
    beginning = str(text)[:100]
    match = re.search(
        r'(January|February|March|April|May|June|July|August|September|October|November|December)'
        r'\s+\d{1,2},?\s+(201[0-9])', beginning)
    return match.group(0) if match else None

df["date"] = df["text"].apply(extract_date)

# Keep only articles with a valid date
df_dated = df[df["date"].notna()].copy()
df_dated["date"] = pd.to_datetime(df_dated["date"], format='mixed')

# Keep only 2018
df_2018 = df_dated[df_dated["date"].dt.year == 2018].copy()
print(f"Articles from 2018: {len(df_2018):,}")

# Remove clearly non-financial articles by URL
non_financial = ['soccer', 'football', 'basketball', 'tennis', 'golf', 'nfl', 'nba',
                 'rugby', 'cricket', 'olympic', 'cycling', 'racing', 'sports',
                 'mideast', 'syria', 'iraq', 'afghanistan', 'korea', 'military',
                 'entertainment', 'lifestyle', 'fashion', 'music', 'film', 'movie',
                 'health', 'science', 'space', 'weather', 'travel']

mask = ~df_2018["url"].str.contains("|".join(non_financial), case=False, na=False)
df_financial = df_2018[mask].copy()
print(f"Articles after removing non-financial: {len(df_financial):,}")
print(df_financial["url"].head(10))

# Sample 50k
df_final = df_financial.sample(n=50000, random_state=42).reset_index(drop=True)
print(f"\nFinal dataset shape: {df_final.shape}")
print(f"Date range: {df_final['date'].min()} to {df_final['date'].max()}")
print(df_final.head(10))

# Save
df_final.to_csv("dataset.csv", index=False)
print("Saved successfully.")