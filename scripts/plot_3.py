import os
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib as mpl
import cartopy.crs as ccrs
import cartopy.feature as cfeature

os.makedirs("plots", exist_ok=True)

NC_DIR = Path("nc_output2")
CA = dict(lat=slice(32.54, 42.0), lon=slice(-125.0, -113.05))
SEG1 = (1990, 2005)
SEG2 = (2006, 2024)

def load_stack(start, end):
    files = sorted(NC_DIR.glob("metrics_wy*.nc"))
    sel = [f for f in files if start <= int(f.stem.split("wy")[-1]) <= end]
    if not sel:
        raise RuntimeError(f"No files for {start}–{end}")
    ds_list = []
    for f in sel:
        yr = int(f.stem.split("wy")[-1])
        ds = xr.open_dataset(f).assign_coords(time=yr)
        da = ds["wd50"]
        if da.lat[0] > da.lat[-1]: da = da.sortby("lat")
        if da.lon[0] > da.lon[-1]: da = da.sortby("lon")
        ds_list.append(ds.assign(wd50=da))
    return xr.concat(ds_list, dim="time")

def median_CA(ds):
    return ds.wd50.sel(**CA).sortby("lat").median("time", skipna=True)

# 1) Load both segments; regrid SEG2 to SEG1’s grid BEFORE computing medians
ds1 = load_stack(*SEG1)                                  # reference grid
ds2 = load_stack(*SEG2).interp(lat=ds1.wd50.lat, lon=ds1.wd50.lon)

m1 = median_CA(ds1)                                      # 1990–2005 median
m2 = median_CA(ds2)                                      # 2006–2024 median

# 2) Shared valid footprint; guard against tiny baselines
mask = np.isfinite(m1) & np.isfinite(m2) & (m1 > 0.5)    # WD50 should be >=1, but be safe
m1c = m1.where(mask)
m2c = m2.where(mask)

# 3) Percent change (later vs earlier)
pct = (m2c - m1c) / m1c * 100.0

# Robust, centered color scale (clip extreme outliers but keep symmetry)
abs98 = float(np.nanpercentile(np.abs(pct.values), 98)) if np.isfinite(pct.values).any() else 50.0
vmax = min(max(10.0, abs98), 50.0)                       # cap at ±50% like your draft
norm = mpl.colors.TwoSlopeNorm(vcenter=0.0, vmin=-vmax, vmax=vmax)

# 4) Plot with pcolormesh (no smoothing, no checkerboard)
proj = ccrs.PlateCarree()
fig, ax = plt.subplots(figsize=(8, 6), subplot_kw={'projection': proj})

pc = ax.pcolormesh(
    pct.lon.values, pct.lat.values, pct.values,
    cmap="RdBu_r", norm=norm,
    shading="nearest", antialiased=False, edgecolors="none",
    transform=proj
)
# zero-percent contour for reference
ax.contour(pct.lon, pct.lat, pct, levels=[0], colors="k", linewidths=0.8, alpha=0.7, transform=proj)

ax.coastlines("10m", linewidth=0.6)
ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor="black", facecolor="none")
ax.add_feature(cfeature.STATES,  linewidth=0.5, edgecolor="black", facecolor="none")
ax.set_extent([-125, -113, 32.5, 42])
ax.set_title("Percent Change in WD50 (2006–2024 vs. 1990–2005)", fontsize=13, weight="bold")

cbar = plt.colorbar(pc, ax=ax, orientation="vertical", shrink=0.8,
                    ticks=np.linspace(-vmax, vmax, 5))
cbar.set_label("Percent change (%)")

plt.savefig("plots/wd50_percent_change_1990_2005_to_2006_2024.png", dpi=300, bbox_inches="tight")
plt.show()

# Optional: print a one-liner summary
v1 = m1c.values[np.isfinite(m1c.values)]
v2 = m2c.values[np.isfinite(m2c.values)]
print(f"Statewide per-cell medians (common mask): early={np.median(v1):.1f} d, late={np.median(v2):.1f} d, "
      f"median change={(np.median(v2)-np.median(v1)):.1f} d ({(np.median(v2)-np.median(v1))/np.median(v1)*100:.1f}%)")
