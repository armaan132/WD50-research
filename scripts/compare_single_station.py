import re
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import os

# -----------------------
# Config
# -----------------------
STATION_CSV = "SEY_single_station_testing.csv"
PRISM_DIR = Path("nc_output2")
SITE_LAT = 37.5
SITE_LON = -119.633
WET_DAY_THRESHOLD_MM = 1.0
COMPARE_YEARS = (1994, 2021)  # inclusive; adjust if needed
OUT_DIR = Path("plots")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "sey_vs_prism_wd50.csv"
OUT_PNG = OUT_DIR / "sey_vs_prism_wd50.png"

# -----------------------
# Helpers
# -----------------------
def water_year(dt):
    return dt.year + 1 if dt.month >= 10 else dt.year

def compute_wd50_from_series_mm(precip_mm):
    a = np.asarray(precip_mm, dtype=float)
    a = a[~np.isnan(a)]
    a = a[a >= WET_DAY_THRESHOLD_MM]
    if a.size == 0:
        return 0
    a_sorted = np.sort(a)[::-1]
    total = a_sorted.sum()
    if total <= 0:
        return 0
    cumsum = np.cumsum(a_sorted)
    idx = np.searchsorted(cumsum, 0.5 * total, side="left")
    return int(idx + 1)

def extract_year_from_filename(p: Path):
    m = re.search(r"metrics_wy(\d{4})\.nc$", p.name)
    return int(m.group(1)) if m else None

# -----------------------
# 1) Load and compute SEY WD50 by water year
# -----------------------
print("Loading station CSV and computing WD50 by water year...")
df = pd.read_csv(STATION_CSV, parse_dates=["DATE TIME"])
# Coerce VALUE to numeric (inches)
df["VALUE"] = pd.to_numeric(df["VALUE"], errors="coerce")
# Convert inches -> mm
df["precip_mm"] = df["VALUE"] * 25.4
df["wy"] = df["DATE TIME"].apply(water_year)

sey_wd50 = (
    df.groupby("wy")["precip_mm"]
    .apply(compute_wd50_from_series_mm)
    .rename("wd50_sey")
    .reset_index()
)

# Restrict to desired compare window
sey_wd50 = sey_wd50[(sey_wd50["wy"] >= COMPARE_YEARS[0]) & (sey_wd50["wy"] <= COMPARE_YEARS[1])]

# -----------------------
# 2) Read PRISM WD50 at nearest grid cell for each WY
# -----------------------
print("Locating nearest PRISM grid cell...")
nc_files = sorted([p for p in PRISM_DIR.glob("metrics_wy*.nc") if extract_year_from_filename(p) is not None])
if not nc_files:
    raise FileNotFoundError(f"No PRISM files found in {PRISM_DIR} matching metrics_wyYYYY.nc")

# Use the first file to lock the nearest grid point coordinates
with xr.open_dataset(nc_files[0]) as ds0:
    lat0 = float(ds0["lat"].sel(lat=SITE_LAT, method="nearest"))
    lon0 = float(ds0["lon"].sel(lon=SITE_LON, method="nearest"))

print(f"Using PRISM grid point lat={lat0:.3f}, lon={lon0:.3f}")

rows = []
for p in nc_files:
    wy = extract_year_from_filename(p)
    if wy is None:
        continue
    if wy < COMPARE_YEARS[0] or wy > COMPARE_YEARS[1]:
        continue
    with xr.open_dataset(p) as ds:
        # wd50 is 2D [lat, lon]
        val = ds["wd50"].sel(lat=lat0, lon=lon0, method="nearest").values
        try:
            wd50_val = float(val)
        except Exception:
            wd50_val = np.nan
    rows.append({"wy": wy, "wd50_prism": wd50_val})

prism_wd50 = pd.DataFrame(rows)

# -----------------------
# 3) Join and plot
# -----------------------
print("Joining SEY and PRISM WD50 and plotting...")
merged = pd.merge(sey_wd50, prism_wd50, on="wy", how="inner").dropna()
if merged.empty:
    raise ValueError("No overlapping water years with data found between SEY and PRISM.")

# Save paired values for inspection
merged.sort_values("wy").to_csv(OUT_CSV, index=False)

x = merged["wd50_sey"].to_numpy(dtype=float)
y = merged["wd50_prism"].to_numpy(dtype=float)

# Stats
if x.size >= 2 and np.all(np.isfinite(x)) and np.all(np.isfinite(y)):
    r = np.corrcoef(x, y)[0, 1]
    r2 = r * r
    rmse = np.sqrt(np.mean((x - y) ** 2))
else:
    r2, rmse = np.nan, np.nan

# Plot
plt.figure(figsize=(7, 7), dpi=150)
plt.scatter(x, y, s=40)
minv = float(np.nanmin([x.min(), y.min(), 0]))
maxv = float(np.nanmax([x.max(), y.max()]))
pad = max(1.0, 0.05 * (maxv - minv))
plt.plot([minv - pad, maxv + pad], [minv - pad, maxv + pad], linestyle="--")
plt.xlabel("SEY Station WD50 (days)")
plt.ylabel("PRISM WD50 (nearest grid, days)")
plt.title(f"WD50 Comparison (WY {COMPARE_YEARS[0]}–{COMPARE_YEARS[1]})\n"
          f"Site lat={SITE_LAT}, lon={SITE_LON} | PRISM grid lat={lat0:.3f}, lon={lon0:.3f}\n"
          f"R²={r2:.3f}  RMSE={rmse:.2f}  N={len(merged)}")
plt.axis("equal")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUT_PNG)
print(f"Saved paired data -> {OUT_CSV}")
print(f"Saved plot -> {OUT_PNG}")
