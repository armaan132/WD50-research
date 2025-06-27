#just to check if the other scripts are working properly - testing single grid point #1


import pandas as pd
import numpy as np

# Step 1: Find where the actual data starts
with open("test.csv", "r") as f:
    lines = f.readlines()

# Locate the line that contains the header
header_line_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith("Date,ppt"):
        header_line_idx = i
        break

if header_line_idx is None:
    raise ValueError("Could not find 'Date,ppt (inches)' header in file.")

# Step 2: Load from the header line onward
df = pd.read_csv("test.csv", skiprows=header_line_idx)
df.columns = df.columns.str.strip()  # Clean up whitespace

print("Columns found:", df.columns)

# Step 3: Check and convert
if 'ppt (inches)' not in df.columns:
    raise KeyError("Expected column 'ppt (inches)' not found. Available columns: " + str(df.columns))

precip_mm = df['ppt (inches)'].astype(float) * 25.4

# Step 4: Calculate WD50
def calculate_wd50(precip_series):
    sorted_daily = np.sort(precip_series[~np.isnan(precip_series)])[::-1]
    cumulative = np.cumsum(sorted_daily)
    half_total = cumulative[-1] / 2
    wd50 = np.sum(cumulative < half_total) + 1
    return wd50

wd50_value = calculate_wd50(precip_mm)
print(f"WD50 from CSV: {wd50_value}")
