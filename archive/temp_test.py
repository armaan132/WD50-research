#testing NC file if storing WD50 values correctly in .ncs


import xarray as xr
import numpy as np


target_lat = 37.0580 
target_lon = -121.1137


ds = xr.open_dataset("nc_output2/metrics_wy1993.nc")


lat_idx = np.abs(ds.lat - target_lat).argmin().item()
lon_idx = np.abs(ds.lon - target_lon).argmin().item()


closest_lat = ds.lat[lat_idx].item()
closest_lon = ds.lon[lon_idx].item()


wd50_val = ds.wd50[lat_idx, lon_idx].item()
prcptot_val = ds.prcptot[lat_idx, lon_idx].item()
r95p_val = ds.r95p[lat_idx, lon_idx].item()
r95ptot_val = ds.r95ptot[lat_idx, lon_idx].item()


print(f"Closest grid point: lat={closest_lat:.4f}, lon={closest_lon:.4f}")
print(f"WD50: {wd50_val}")
print(f"Total Precipitation (prcptot): {prcptot_val:.2f} mm")
print(f"Number of extreme days (r95p): {r95p_val}")
print(f"Extreme precipitation total (r95ptot): {r95ptot_val:.2f} mm")
