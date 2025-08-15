import xarray as xr
import numpy as np

# Load the output file
ds = xr.open_dataset("wd50_mk_trend.nc")

# Access individual variables
trend = ds["trend"]
p_value = ds["p_value"]
slope = ds["slope"]

# Basic overview
print("WD50 Mann-Kendall Trend Results:")
print(f"- Trend categories: {np.unique(trend.values)}")
print(f"- P-value range: {np.nanmin(p_value.values):.4f} to {np.nanmax(p_value.values):.4f}")
print(f"- Slope range: {np.nanmin(slope.values):.4f} to {np.nanmax(slope.values):.4f}")

# Count how many grid cells have significant trends (p < 0.05)
sig_mask = p_value < 0.05
num_sig = np.sum(sig_mask.values)
total_cells = np.count_nonzero(~np.isnan(p_value.values))
print(f"- Significant trends (p < 0.05): {num_sig} of {total_cells} cells")

# Optional: count how many are increasing vs decreasing
increasing = ((trend == "increasing") & sig_mask).sum().item()
decreasing = ((trend == "decreasing") & sig_mask).sum().item()
print(f"- Increasing (sig): {increasing}")
print(f"- Decreasing (sig): {decreasing}")
