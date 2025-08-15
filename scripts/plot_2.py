import xarray as xr
from pathlib import Path
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os

os.makedirs("plots", exist_ok=True)

nc_dir = Path("nc_output2")
files = sorted(nc_dir.glob("metrics_wy*.nc"))
seg2 = [f for f in files if 2006 <= int(f.stem.split("wy")[-1]) <= 2024]

ds_list = []
for f in seg2:
    ds = xr.open_dataset(f)
    year = int(f.stem.split("wy")[-1])
    ds = ds.assign_coords(time=year)
    ds_list.append(ds)

combined = xr.concat(ds_list, dim="time")
median_wd50 = combined["wd50"].median(dim="time")

if median_wd50.lat[0] < median_wd50.lat[-1]:
    median_wd50 = median_wd50.sel(lat=slice(32.54, 42.0), lon=slice(-125.0, -113.05))
else:
    median_wd50 = median_wd50.sel(lat=slice(42.0, 32.54), lon=slice(-125.0, -113.05))


median_wd50 = median_wd50.sortby('lat')

# Plot using imshow with enhanced contrast
fig, ax = plt.subplots(figsize=(7, 6), subplot_kw={'projection': ccrs.PlateCarree()})

img = ax.imshow(
    median_wd50.values,
    extent=[median_wd50.lon.min(), median_wd50.lon.max(),
            median_wd50.lat.min(), median_wd50.lat.max()],
    origin='lower',
    cmap='Blues',
    interpolation='nearest',
    vmin=2,
    vmax=29
)

ax.coastlines("10m", linewidth=0.6)
ax.add_feature(cfeature.BORDERS, linewidth=0.5)
ax.add_feature(cfeature.STATES, linewidth=0.5)
ax.set_extent([-125, -113, 32.5, 42])
ax.set_title("Median WD50 (2006–2024) — California", fontsize=14, weight='bold')

cbar = plt.colorbar(img, ax=ax, orientation='vertical', shrink=0.7)
cbar.set_label("WD50 (days)")

plt.savefig("plots/median_wd50_2006_2024_CA_contrast.png", dpi=300)
plt.show()


