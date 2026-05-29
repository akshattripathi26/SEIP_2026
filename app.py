import streamlit as st
import gzip
import matplotlib as plt
import simplejson # Keep import in case it's used elsewhere, but not in parse for now.
import pandas as pd
import zlib # Import zlib to catch its specific errors

def parse(filename):
    entry = {}
    try:
        # Open in text mode with utf-8 encoding as the content appears to be text (key: value pairs)
        with gzip.open(filename, 'rt', encoding='utf-8') as f:
            for l in f:
                l = l.strip()
                if not l:  # Empty line indicates end of an entry
                    if entry: # Yield if entry is not empty
                        yield entry
                    entry = {}
                    continue
                colonPos = l.find(':')
                if colonPos == -1: # Malformed line if no colon but not empty
                    print(f"Skipping malformed line (no colon found): {l}")
                    continue # Skip this line, don't break the current entry
                
                eName = l[:colonPos].strip()
                rest = l[colonPos+1:].strip() # +1 to skip ':', then strip spaces
                entry[eName] = rest
            if entry: # Yield the last entry if it's not empty after loop finishes
                yield entry
    except zlib.error as e:
        print(f"Error decompressing file {filename}: {e}. Processing partial data.")
    except Exception as e:
        print(f"An unexpected error occurred while reading {filename}: {e}")

# Load into DataFrame
df = pd.DataFrame(list(parse("Watches.txt.gz")))

print(df.columns.tolist())
print(df.head())

df['review/score'] = pd.to_numeric(df['review/score'], errors='coerce')
df['review/time'] = pd.to_numeric(df['review/time'], errors='coerce')
df['review/time'] = pd.to_datetime(df['review/time'], unit='s')  # Unix timestamp to date

df = df.dropna(subset=['review/score'])
print(df.dtypes)


rating_counts = df['review/score'].value_counts().sort_index()

plt.figure(figsize=(8, 5))
plt.bar(rating_counts.index, rating_counts.values, color='steelblue', edgecolor='black')
plt.title('Distribution of Review Ratings')
plt.xlabel('Rating (Stars)')
plt.ylabel('Number of Reviews')
plt.xticks([1, 2, 3, 4, 5])
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()
