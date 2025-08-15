# debug_wd50_regrid.py
import os
from pathlib import Path
import random
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

OUTDIR = Path("debug_outputs"); OUTDIR.mkdir(parents=True, exist_ok=True)
NC_DIR = Path("nc_output2")
CA_BBOX = dict(lat=slice(32.54, 42.0), lon=slice(-125.0, -113.05))
SEG1 = (1990, 2005)
SEG2 = (2006, 2024)
VMIN, VMAX = 2.0, 29.0

def list_year_files(start, end):
    files = sorted(NC_DIR.glob("metrics_wy*.nc"))
    sel = [f for f in files if start <= int(f.stem.split("wy")[-1]) <= end]
    if not sel:
        raise RuntimeError(f"No NetCDFs found for {start}–{end}.")
    return sel

def load_stack(files):
    ds_list = []
    for f in files:
        yr = int(f.stem.split("wy")[-1])
        ds = xr.open_dataset(f).assign_coords(time=yr)
        # ensure ascending coords
        da = ds["wd50"]
        if da.lat[0] > da.lat[-1]: da = da.sortby("lat")
        if da.lon[0] > da.lon[-1]: da = da.sortby("lon")
        ds_list.append(ds.assign(wd50=da))
    combo = xr.concat(ds_list, dim="time")
    return combo

def segment_median(ds, bbox):
    da = ds.wd50.sel(**bbox).sortby("lat")
    return da.median("time", skipna=True)

def stats_for(da, name):
    v = da.values
    finite = np.isfinite(v)
    vals = v[finite]
    return dict(
        segment=name,
        n_cells=int(vals.size),
        n_nans=int((~finite).sum()),
        min=float(np.min(vals)) if vals.size else np.nan,
        p05=float(np.percentile(vals,5)) if vals.size else np.nan,
        median=float(np.median(vals)) if vals.size else np.nan,
        mean=float(np.mean(vals)) if vals.size else np.nan,
        p95=float(np.percentile(vals,95)) if vals.size else np.nan,
        max=float(np.max(vals)) if vals.size else np.nan,
    )

def statewide_yearly_median(ds, bbox):
    da = ds.wd50.sel(**bbox).sortby("lat")
    return da.median(dim=("lat","lon"), skipna=True).to_series().sort_index()

# 1) Load both segments
seg1_files = list_year_files(*SEG1)
seg2_files = list_year_files(*SEG2)
ds1 = load_stack(seg1_files)
ds2 = load_stack(seg2_files)

# 2) Report original grid differences
print("Original grid:")
print("  seg1 lat:", float(ds1.wd50.lat.min()), "→", float(ds1.wd50.lat.max()),
      "n=", ds1.wd50.sizes["lat"])
print("  seg1 lon:", float(ds1.wd50.lon.min()), "→", float(ds1.wd50.lon.max()),
      "n=", ds1.wd50.sizes["lon"])
print("  seg2 lat:", float(ds2.wd50.lat.min()), "→", float(ds2.wd50.lat.max()),
      "n=", ds2.wd50.sizes["lat"])
print("  seg2 lon:", float(ds2.wd50.lon.min()), "→", float(ds2.wd50.lon.max()),
      "n=", ds2.wd50.sizes["lon"])

# 3) Regrid seg2 to seg1 grid (rectilinear) BEFORE slicing to CA
target_lat = ds1.wd50.lat
target_lon = ds1.wd50.lon
ds2_rg = ds2.interp(lat=target_lat, lon=target_lon)  # linear interp

print("\nAfter regrid to seg1 grid:")
print("  seg1 grid:", ds1.wd50.sizes)
print("  seg2_rg  :", ds2_rg.wd50.sizes)
print("  lat equal?", np.array_equal(ds1.wd50.lat.values, ds2_rg.wd50.lat.values))
print("  lon equal?", np.array_equal(ds1.wd50.lon.values, ds2_rg.wd50.lon.values))

# 4) Per‑cell medians over CA (on identical grid)
seg1_med = segment_median(ds1, CA_BBOX)
seg2_med = segment_median(ds2_rg, CA_BBOX)

# 5) Stats & save table
s1 = stats_for(seg1_med, f"{SEG1[0]}–{SEG1[1]}")
s2 = stats_for(seg2_med, f"{SEG2[0]}–{SEG2[1]}")
summary = pd.DataFrame([s1, s2])
summary.to_csv(OUTDIR/"wd50_segment_summary_regridded.csv", index=False)
print("\nSegment stats (CA, regridded):")
print(summary)

# 6) Spot checks: prove per‑cell median equals explicit median of yearly values
print("\nSpot checks on the common grid (map vs explicit median):")
H, W = seg1_med.shape
for _ in range(10):
    i, j = random.randrange(H), random.randrange(W)
    lat0, lon0 = float(seg1_med.lat[i]), float(seg1_med.lon[j])
    s1_series = ds1.wd50.sel(lat=lat0, lon=lon0, method="nearest").dropna("time").values
    s2_series = ds2_rg.wd50.sel(lat=lat0, lon=lon0, method="nearest").dropna("time").values
    m1_map = float(seg1_med[i, j]); m2_map = float(seg2_med[i, j])
    m1_calc = float(np.median(s1_series)) if s1_series.size else np.nan
    m2_calc = float(np.median(s2_series)) if s2_series.size else np.nan
    print(f"  ({lat0:.3f},{lon0:.3f})  seg1 map={m1_map:.2f} calc={m1_calc:.2f} | seg2 map={m2_map:.2f} calc={m2_calc:.2f}")

# 7) Statewide yearly medians (time series)
ts1 = statewide_yearly_median(ds1, CA_BBOX)
ts2 = statewide_yearly_median(ds2_rg, CA_BBOX)
fig, ax = plt.subplots(figsize=(9,4))
ax.plot(ts1.index, ts1.values, label=f"{SEG1[0]}–{SEG1[1]} (regridded base)", marker="o", lw=1)
ax.plot(ts2.index, ts2.values, label=f"{SEG2[0]}–{SEG2[1]} (on seg1 grid)", marker="o", lw=1)
ax.set_ylabel("Statewide median WD50 (days)"); ax.set_xlabel("Water Year")
ax.grid(True, alpha=0.3); ax.legend(); plt.tight_layout()
plt.savefig(OUTDIR/"fig_timeseries_statewide_regridded.png", dpi=300)

# 8) Histograms of per‑cell medians (same bins, same scale)
fig, ax = plt.subplots(figsize=(7,4))
ax.hist(seg1_med.values.ravel(), bins=28, range=(VMIN, VMAX), alpha=0.6, label=f"{SEG1[0]}–{SEG1[1]}")
ax.hist(seg2_med.values.ravel(), bins=28, range=(VMIN, VMAX), alpha=0.6, label=f"{SEG2[0]}–{SEG2[1]}")
ax.set_xlabel("Per‑cell median WD50 (days)"); ax.set_ylabel("Cell count")
ax.legend(); ax.grid(True, alpha=0.3); plt.tight_layout()
plt.savefig(OUTDIR/"fig_histograms_regridded.png", dpi=300)

# 9) Spatial difference map (later − earlier) on the common grid
diff = seg2_med - seg1_med
lon = seg1_med.lon.values; lat = seg1_med.lat.values
fig, ax = plt.subplots(figsize=(7,6), subplot_kw={'projection': ccrs.PlateCarree()})
pc = ax.pcolormesh(lon, lat, diff.values,
                   cmap="BrBG", vmin=-6, vmax=6,
                   shading="nearest", antialiased=False, edgecolors="none",
                   transform=ccrs.PlateCarree())
ax.coastlines("10m", linewidth=0.6); ax.add_feature(cfeature.BORDERS, linewidth=0.5); ax.add_feature(cfeature.STATES, linewidth=0.5)
ax.set_extent([-125,-113,32.5,42]); ax.set_title("Δ Median WD50 (2006–2024 minus 1990–2005), regridded")
cbar = plt.colorbar(pc, ax=ax, shrink=0.8, label="Δ days (negative = lower later)")
plt.tight_layout(); plt.savefig(OUTDIR/"fig_diff_map_regridded.png", dpi=300)

print("\nWrote:")
print(" ", OUTDIR/"wd50_segment_summary_regridded.csv")
print(" ", OUTDIR/"fig_timeseries_statewide_regridded.png")
print(" ", OUTDIR/"fig_histograms_regridded.png")
print(" ", OUTDIR/"fig_diff_map_regridded.png")
