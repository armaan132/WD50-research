#dynamic script in water years storing NC file and testing different variables



import os
import requests
import zipfile
import rasterio
import numpy as np
import time
from datetime import datetime, timedelta
import shutil
import xarray as xr

# === CONFIGURATION ===
start_water_year = 1990
end_water_year = 2001  # inclusive
variable = "ppt"
output_dir = "temp_prism"
nc_output_dir = "nc_output"

os.makedirs(nc_output_dir, exist_ok=True)

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

for wy in range(start_water_year, end_water_year + 1):
    start_date = datetime(wy - 1, 10, 1)
    end_date = datetime(wy, 9, 30)
    print(f"\nProcessing Water Year {wy} ({start_date.date()} to {end_date.date()})")

    daily_stack = []
    lat_grid, lon_grid = None, None

    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y%m%d")
        year = current.year
        url = f"https://ftp.prism.oregonstate.edu/daily/{variable}/{year}/PRISM_{variable}_stable_4kmD2_{date_str}_bil.zip"

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        try:
            print(f"Fetching {date_str}...")
            t0 = time.time()

            r = requests.get(url)
            if r.status_code != 200:
                print(f"Not found: {date_str}")
                current += timedelta(days=1)
                continue

            zip_path = os.path.join(output_dir, f"{variable}_{date_str}.zip")
            with open(zip_path, 'wb') as f:
                f.write(r.content)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)

            bil_name = f"PRISM_{variable}_stable_4kmD2_{date_str}_bil.bil"
            bil_path = os.path.join(output_dir, bil_name)

            with rasterio.open(bil_path) as src:
                data = src.read(1).astype(np.float32)
                data[data == -9999] = np.nan

                if lat_grid is None or lon_grid is None:
                    bounds = src.bounds
                    lat_res = (bounds.top - bounds.bottom) / src.height
                    lon_res = (bounds.right - bounds.left) / src.width
                    lat_grid = np.linspace(bounds.top - 0.5 * lat_res, bounds.bottom + 0.5 * lat_res, src.height)
                    lon_grid = np.linspace(bounds.left + 0.5 * lon_res, bounds.right - 0.5 * lon_res, src.width)

                daily_stack.append(data)

            print(f"Processed {date_str} | Time: {time.time() - t0:.2f}s")

        except Exception as e:
            print(f"Error on {date_str}: {e}")

        finally:
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)

        current += timedelta(days=1)

    if len(daily_stack) > 0:
        print("Calculating WD50 and other metrics...")
        full_data = np.stack(daily_stack, axis=0)

        # Apply metrics
        wd50_map = np.apply_along_axis(calculate_wd50, 0, full_data)

        # PRCPTOT: Total precip on wet days (≥1 mm)
        prcptot_map = np.apply_along_axis(lambda s: np.nansum(s[s >= 1.0]), 0, full_data)

        # 95th percentile threshold (for each grid cell)
        r95_threshold = np.nanpercentile(full_data, 95, axis=0)

        # Boolean mask for days > 95th percentile
        r95_mask = full_data > r95_threshold

        # R95p: number of days > 95th percentile
        r95p_map = np.sum(r95_mask & ~np.isnan(full_data), axis=0)

        # R95pTOT: total precipitation on those days
        r95ptot_map = np.sum(np.where(r95_mask, full_data, 0), axis=0)

        # Create dataset
        ds = xr.Dataset(
            {
                "wd50": (("lat", "lon"), wd50_map),
                "prcptot": (("lat", "lon"), prcptot_map),
                "r95p": (("lat", "lon"), r95p_map),
                "r95ptot": (("lat", "lon"), r95ptot_map),
            },
            coords={
                "lat": lat_grid,
                "lon": lon_grid
            },
            attrs={
                "units": "varies",
                "description": f"Precipitation metrics for Water Year {wy}"
            }
        )

        encoding = {
            "wd50": {"zlib": True, "complevel": 4},
            "prcptot": {"zlib": True, "complevel": 4},
            "r95p": {"zlib": True, "complevel": 4},
            "r95ptot": {"zlib": True, "complevel": 4},
        }

        nc_path = os.path.join(nc_output_dir, f"metrics_wy{wy}.nc")
        ds.to_netcdf(nc_path, encoding=encoding)
        print(f"Saved precipitation metrics to {nc_path}")

