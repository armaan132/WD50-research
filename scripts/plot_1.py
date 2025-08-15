# plot_wd50_segments_final.py
## plots first segment, second segment, and a delta days segment
import os
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# ---- config
NC_DIR = Path("nc_output2")
OUT = Path("plots"); OUT.mkdir(exist_ok=True)
SEG1 = (1990, 2005)
SEG2 = (2006, 2024)
CA = dict(lat=slice(32.54, 42.0), lon=slice(-125.0, -113.05))
VMIN, VMAX = 2.0, 29.0

def load_stack(start, end):
    files = sorted(NC_DIR.glob("metrics_wy*.nc"))
    sel = [f for f in files if start <= int(f.stem.split("wy")[-1]) <= end]
    if not sel:
        raise RuntimeError(f"No NetCDFs found for {start}–{end}.")
    ds_list = []
    for f in sel:
        yr = int(f.stem.split("wy")[-1])
        ds = xr.open_dataset(f).assign_coords(time=yr)
        da = ds["wd50"]
        if da.lat[0] > da.lat[-1]: da = da.sortby("lat")
        if da.lon[0] > da.lon[-1]: da = da.sortby("lon")
        ds_list.append(ds.assign(wd50=da))
    return xr.concat(ds_list, dim="time")

def per_cell_median(ds):
    return ds.wd50.sel(**CA).sortby("lat").median("time", skipna=True)

# ---- load & regrid to a common grid (seg2 -> seg1 grid)
ds1 = load_stack(*SEG1)                      # reference grid
ds2 = load_stack(*SEG2)
ds2_rg = ds2.interp(lat=ds1.wd50.lat, lon=ds1.wd50.lon)

# ---- per-cell medians over California
m1 = per_cell_median(ds1)
m2 = per_cell_median(ds2_rg)

# common valid-cell mask so panels show the same footprint
mask = np.isfinite(m1) & np.isfinite(m2)
m1 = m1.where(mask)
m2 = m2.where(mask)

# quick numeric summary
for name, da in [("1990–2005", m1), ("2006–2024", m2)]:
    v = da.values[np.isfinite(da.values)]
    print(f"{name}: n={v.size}, min/median/mean/max = "
          f"{np.min(v):.1f}/{np.median(v):.1f}/{np.mean(v):.2f}/{np.max(v):.1f}")

proj = ccrs.PlateCarree()

# ---- side-by-side maps (fixed scale, no smoothing; no grid artifacts)
fig, axes = plt.subplots(1, 2, figsize=(12, 6), subplot_kw={'projection': proj})
for ax, da, title in [
    (axes[0], m1, "Median WD50 (1990–2005) — California"),
    (axes[1], m2, "Median WD50 (2006–2024) — California"),
]:
    pc = ax.pcolormesh(
        da.lon.values, da.lat.values, da.values,
        cmap="Blues", vmin=VMIN, vmax=VMAX,
        shading="nearest", antialiased=False, edgecolors="none",
        transform=proj
    )
    ax.coastlines("10m", linewidth=0.6)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor="black", facecolor="none")
    ax.add_feature(cfeature.STATES,  linewidth=0.5, edgecolor="black", facecolor="none")
    ax.set_extent([-125, -113, 32.5, 42])
    ax.set_title(title, fontsize=14, weight="bold")

cbar = fig.colorbar(pc, ax=axes, orientation="vertical", fraction=0.046, pad=0.04)
cbar.set_label("WD50 (days)")
fig.tight_layout()
fig.savefig(OUT/"wd50_CA_seg1_seg2_fixed.png", dpi=300, bbox_inches="tight")
plt.show()

# ---- difference map (later − earlier); negative = lower later
diff = m2 - m1
fig, ax = plt.subplots(figsize=(7, 6), subplot_kw={'projection': proj})
pdiff = ax.pcolormesh(
    diff.lon.values, diff.lat.values, diff.values,
    cmap="BrBG", vmin=-6, vmax=6,
    shading="nearest", antialiased=False, edgecolors="none",
    transform=proj
)
ax.coastlines("10m", linewidth=0.6)
ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor="black", facecolor="none")
ax.add_feature(cfeature.STATES,  linewidth=0.5, edgecolor="black", facecolor="none")
ax.set_extent([-125, -113, 32.5, 42])
ax.set_title("Δ Median WD50 (2006–2024 − 1990–2005), regridded", fontsize=13, weight="bold")
plt.colorbar(pdiff, ax=ax, shrink=0.8, label="Δ days (negative = lower later)")
fig.tight_layout()
fig.savefig(OUT/"wd50_CA_diff_regridded.png", dpi=300, bbox_inches="tight")
plt.show()
