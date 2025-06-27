#testing NC file if storing WD50 values correctly


import xarray as xr
import numpy as np

ds = xr.open_dataset("nc_output/wd50_map_wy1990.nc")
print(ds)

# Summary of finite values
finite_count = np.sum(np.isfinite(ds["wd50"].values))
print(f"Number of valid (non-NaN) grid cells: {finite_count}")

# Preview some values
print(ds["wd50"].values[100:105, 100:105])
