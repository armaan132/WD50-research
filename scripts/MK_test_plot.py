import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

os.makedirs("plots", exist_ok=True)

ds = xr.open_dataset("wd50_mk_trend.nc")
trend = ds["trend"].sortby("lat").sel(lat=slice(32.54, 42.0), lon=slice(-125.0, -113.05))

codes = xr.where(
    trend.astype(str) == "decreasing", -1,
    xr.where(trend.astype(str) == "no trend", 0,
             xr.where(trend.astype(str) == "increasing", 1, np.nan))
).astype(float)

idx = np.full(codes.shape, 3, dtype=np.uint8)  # 3 = transparent for NaN
idx[np.isfinite(codes)] = 1  # default to white (none)
idx[codes == -1] = 0         # red
idx[codes == 0]  = 1         # white
idx[codes == 1]  = 2         # blue

lut = np.array([
    [255,   0,   0, 255],  # red
    [255, 255, 255, 255],  # white
    [  0,   0, 255, 255],  # blue
    [  0,   0,   0,   0],  # transparent (NaN)
], dtype=np.uint8)

rgba = lut[idx]  # (lat, lon, 4)

fig, ax = plt.subplots(figsize=(7, 6), subplot_kw={"projection": ccrs.PlateCarree()})

img = ax.imshow(
    rgba,
    extent=[float(codes.lon.min()), float(codes.lon.max()),
            float(codes.lat.min()), float(codes.lat.max())],
    origin="lower",
    interpolation="nearest",
    resample=False,
)

ax.coastlines("10m", linewidth=0.6)
ax.add_feature(cfeature.BORDERS, linewidth=0.5)
ax.add_feature(cfeature.STATES, linewidth=0.5)
ax.set_extent([-125, -113, 32.5, 42])
ax.set_title("Mann-Kendall Trend (WD50) — California", fontsize=14, weight="bold")

from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.colorbar import ColorbarBase
cmap = ListedColormap(["#ff0000", "#ffffff", "#0000ff"])
norm = BoundaryNorm([-1.5, -0.5, 0.5, 1.5], 3)
cax = fig.add_axes([0.88, 0.2, 0.03, 0.6])
cb = ColorbarBase(cax, cmap=cmap, norm=norm, ticks=[-1,0,1], boundaries=[-1.5,-0.5,0.5,1.5])
cb.ax.set_yticklabels(["Decreasing", "None", "Increasing"])

plt.savefig("plots/wd50_mk_trend_CA_discrete.png", dpi=600, bbox_inches="tight")
plt.show()
