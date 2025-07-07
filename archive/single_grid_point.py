##testing .CSV and using single grid points to determine if .nc files produced proper values



import pandas as pd
import numpy as np

## MAKE SURE TO PULL IN WATER YEARS
with open("test.csv", "r") as f:
    lines = f.readlines()
## MAKE SURE TO PULL IN WATER YEARS

header_line_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith("Date,ppt"):
        header_line_idx = i
        break

if header_line_idx is None:
    raise ValueError("Could not find header starting with 'Date,ppt' in file.")


df = pd.read_csv("test.csv", skiprows=header_line_idx)
df.columns = df.columns.str.strip()  # Clean up whitespace

print("Columns found:", df.columns)

# Step 3: Check and convert units
if "ppt (inches)" in df.columns:
    precip_mm = df["ppt (inches)"].astype(float) * 25.4
elif "ppt (mm)" in df.columns:
    precip_mm = df["ppt (mm)"].astype(float)
else:
    raise KeyError("Expected 'ppt (inches)' or 'ppt (mm)' column. Found: " + str(df.columns))

# Calculate WD50
def calculate_wd50(series):
    series = series[~np.isnan(series)]
    wet_days = series[series > 1.0]
    if len(wet_days) == 0:
        return np.nan
    sorted_daily = np.sort(wet_days)[::-1]
    cumulative = np.cumsum(sorted_daily)
    half_total = cumulative[-1] / 2
    wd50 = np.sum(cumulative < half_total) + 1
    return wd50

wd50_value = calculate_wd50(precip_mm)
print(f"WD50 from CSV: {wd50_value}")
