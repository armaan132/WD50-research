import xarray as xr
import numpy as np
import pymannkendall as mk
from pathlib import Path

input_dir = Path("nc_output2")
output_path = "wd50_mk_trend.nc"

wd50_maps = []
years = []

for file in sorted(input_dir.glob("metrics_wy*.nc")):
    year = int(file.stem.split("wy")[-1])
    ds = xr.open_dataset(file)
    if "wd50" not in ds:
        continue
    wd50 = ds["wd50"].expand_dims(time=[year])
    wd50_maps.append(wd50)
    years.append(year)

if not wd50_maps:
    raise RuntimeError("No wd50 data found in NetCDF files.")

wd50_stack = xr.concat(wd50_maps, dim="time")
wd50_stack = wd50_stack.sortby("time")

def run_mk_test(ts):
    if np.isnan(ts).all():
        return np.nan, np.nan, np.nan
    result = mk.original_test(ts)
    return result.trend, result.p, result.slope

print("Running Mann-Kendall test...")

mk_results = xr.apply_ufunc(
    run_mk_test,
    wd50_stack,
    input_core_dims=[["time"]],
    output_core_dims=[[], [], []],
    vectorize=True,
    output_dtypes=[object, float, float]
)

print("Finished Mann-Kendall test.")

trend_map = mk_results[0].rename("trend")
p_value_map = mk_results[1].rename("p_value")
slope_map = mk_results[2].rename("slope")

out_ds = xr.Dataset({
    "trend": trend_map,
    "p_value": p_value_map,
    "slope": slope_map
}, coords={
    "lat": wd50_stack.lat,
    "lon": wd50_stack.lon
}, attrs={
    "description": "Mann-Kendall trend test results on WD50 from 2012–2025"
})

out_ds.to_netcdf(output_path)
print("Saved to wd50_mk_trend.nc")
