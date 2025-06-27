#forgot what this is


import os
import requests
import zipfile
import rasterio
import numpy as np
import xarray as xr
from datetime import datetime, timedelta

def download_prism_test(variable="ppt", output_dir="prism_test"):
    os.makedirs(output_dir, exist_ok=True)
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 3)  # just 3 days

    data_list = []
    time_list = []

    lat, lon = None, None

    date = start
    while date <= end:
        date_str = date.strftime("%Y%m%d")
        url = f"https://ftp.prism.oregonstate.edu/daily/{variable}/2023/PRISM_{variable}_stable_4kmD2_{date_str}_bil.zip"
        zip_path = os.path.join(output_dir, f"{variable}_{date_str}.zip")
        bil_name = f"PRISM_{variable}_stable_4kmD2_{date_str}_bil.bil"
        bil_path = os.path.join(output_dir, bil_name)

        if not os.path.exists(bil_path):
            print(f"Downloading {date_str}...")
            r = requests.get(url)
            if r.status_code == 200:
                with open(zip_path, 'wb') as f:
                    f.write(r.content)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(output_dir)
            else:
                print(f"{date_str} not found (HTTP {r.status_code})")
                date += timedelta(days=1)
                continue

        try:
            with rasterio.open(bil_path) as src:
                data = src.read(1).astype(np.float32)
                data[data == -9999] = np.nan

                bounds = src.bounds
                lats = np.linspace(bounds.top, bounds.bottom, src.height)
                lons = np.linspace(bounds.left, bounds.right, src.width)

                if lat is None or lon is None:
                    lat = lats
                    lon = lons
                    lat_idx = np.where((lat >= 34) & (lat <= 35))[0]
                    lon_idx = np.where((lons >= -119) & (lons <= -118))[0]

                cropped = data[lat_idx[:, None], lon_idx]
                data_list.append(cropped)
                time_list.append(np.datetime64(date))
        except Exception as e:
            print(f"Error on {date_str}: {e}")

        date += timedelta(days=1)

    da = xr.DataArray(
        data=np.stack(data_list),
        coords={"time": time_list, "lat": lat[lat_idx], "lon": lon[lon_idx]},
        dims=["time", "lat", "lon"],
        name=variable
    )
    ds = xr.Dataset({variable: da})
    out_path = os.path.join(output_dir, f"{variable}_daily_test.nc")
    print(f"Saved NetCDF to {out_path}")
    ds.to_netcdf(out_path, encoding={variable: {"zlib": True, "complevel": 4}})

# func call
download_prism_test()

