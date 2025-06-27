#same as dynamic script but implemented water years #3


import os
import requests
import zipfile
import rasterio
import numpy as np
import time
from datetime import datetime, timedelta
import shutil

# === CONFIGURATION ===
start_water_year = 1990
end_water_year = 1992  # inclusive
variable = "ppt"
output_dir = "temp_prism"
target_lat = 33.7448
target_lon = -117.7467

def calculate_wd50(precip_series):
    # Only include wet days > 1 mm
    wet_days = precip_series[precip_series > 1.0]
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
    daily_precip = []

    print(f"\n🟦 Processing Water Year {wy} ({start_date.date()} to {end_date.date()})")

    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y%m%d")
        year = current.year
        url = f"https://ftp.prism.oregonstate.edu/daily/{variable}/{year}/PRISM_{variable}_stable_4kmD2_{date_str}_bil.zip"

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        try:
            print(f"\n {date_str}...")
            t0 = time.time()

            r = requests.get(url)
            if r.status_code != 200:
                print(f"❌ {date_str} not found.")
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
                lat_res = (bounds.top - bounds.bottom) / src.height
                lon_res = (bounds.right - bounds.left) / src.width

                lats = np.linspace(bounds.top - 0.5 * lat_res, bounds.bottom + 0.5 * lat_res, src.height)
                lons = np.linspace(bounds.left + 0.5 * lon_res, bounds.right - 0.5 * lon_res, src.width)


                lat_idx = np.abs(lats - target_lat).argmin()
                lon_idx = np.abs(lons - target_lon).argmin()

                value = data[lat_idx, lon_idx]
                daily_precip.append(value)

                print(f" lat={lats[lat_idx]:.4f}, lon={lons[lon_idx]:.4f}, precip={value:.2f} mm")
                print(f" Time: {time.time() - t0:.2f} sec")

        except Exception as e:
            print(f"⚠️ Error on {date_str}: {e}")

        finally:
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)

        current += timedelta(days=1)

    daily_precip = np.array(daily_precip)
    print(f"\n📊 Days collected: {len(daily_precip)} (expected: {(end_date - start_date).days + 1})")

    if len(daily_precip) == 0 or np.all(np.isnan(daily_precip)):
        print(f"🚫 No data for Water Year {wy}")
    else:
        wd50 = calculate_wd50(daily_precip)
        print(f"🌧️ WD50 for Water Year {wy}: {wd50}")
