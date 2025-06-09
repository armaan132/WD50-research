import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

ds = xr.open_dataset("data/processed/ppt_daily_test.nc")
ppt = ds['ppt']  # (time, lat, lon) preciptation format

ppt_single = ppt[:, 0, 0].values

def calculate_wd50(precip_series):
    sorted_daily = np.sort(precip_series[~np.isnan(precip_series)])[::-1]
    cumulative = np.cumsum(sorted_daily)
    half_total = cumulative[-1] / 2
    wd50 = np.sum(cumulative < half_total) + 1
    return wd50

wd50_value = calculate_wd50(ppt_single)
print(f"WD50 at first grid point: {wd50_value}")

