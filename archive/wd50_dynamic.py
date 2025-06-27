#new dynamic script implemented to prevent heavy file usage #2



import os
import requests
import zipfile
import rasterio
import numpy as np
import time
from datetime import datetime, timedelta
import shutil


start_date = datetime(1990, 1, 1)
end_date = datetime(1990, 12, 31)
variable = "ppt"
output_dir = "temp_prism"

# PRISM test location from CSV
target_lat = 33.7448
target_lon = -117.7467

def calculate_wd50(precip_series):
    # Filter: only include days > 1 mm
    wet_days = precip_series[precip_series > 1.0]
    if len(wet_days) == 0:
        return np.nan  # Not enough valid days

    sorted_daily = np.sort(wet_days)[::-1]
    cumulative = np.cumsum(sorted_daily)
    half_total = cumulative[-1] / 2
    wd50 = np.sum(cumulative < half_total) + 1
    return wd50


daily_precip = []

current = start_date
while current <= end_date:
    date_str = current.strftime("%Y%m%d")
    year = current.year
    url = f"https://ftp.prism.oregonstate.edu/daily/{variable}/{year}/PRISM_{variable}_stable_4kmD2_{date_str}_bil.zip"

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    try:
        print(f"\n Processing {date_str}...")
        t0 = time.time()

        r = requests.get(url)
        if r.status_code != 200:
            print(f" {date_str} not found.")
            current += timedelta(days=1)
            continue

        zip_path = os.path.join(output_dir, f"{variable}_{date_str}.zip")
        with open(zip_path, 'wb') as f:
            f.write(r.content)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        time.sleep(0.5)

        bil_name = f"PRISM_{variable}_stable_4kmD2_{date_str}_bil.bil"
        bil_path = os.path.join(output_dir, bil_name)

        with rasterio.open(bil_path) as src:
            data = src.read(1).astype(np.float32)
            data[data == -9999] = np.nan

            ##This was used to match testing grid point to 
            ##Latitude: 33.7448   Longitude: -117.7467 by pulling directly from
            ##the PRISM server and downloading as test.csv
            bounds = src.bounds
            lats = np.linspace(bounds.top, bounds.bottom, src.height)
            lons = np.linspace(bounds.left, bounds.right, src.width)

            lat_idx = np.abs(lats - target_lat).argmin()
            lon_idx = np.abs(lons - target_lon).argmin()

            value = data[lat_idx, lon_idx]
            daily_precip.append(value)

            print(f" lat={lats[lat_idx]:.4f}, lon={lons[lon_idx]:.4f}, precip={value:.2f} mm")

        t1 = time.time()
        print(f"⏱️ Time taken: {t1 - t0:.2f} sec")

    except Exception as e:
        print(f" Error on {date_str}: {e}")

    finally:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

    current += timedelta(days=1)

print(f"\nTotal valid days collected: {len(daily_precip)} (expected: {(end_date - start_date).days + 1})")

daily_precip = np.array(daily_precip)
if len(daily_precip) == 0 or np.all(np.isnan(daily_precip)):
    print("No valid precipitation data collected. WD50 cannot be computed.")
else:
    wd50 = calculate_wd50(daily_precip)
    print(f"\nWD50 from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}: {wd50}")
