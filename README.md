# WD50 Precipitation Analysis (PRISM Data)

This project computes the Wettest Days 50% (WD50) metric using PRISM daily precipitation data for California grid points. It includes:

- Python script for calculating WD50 from daily `.csv` files
- Automated PRISM `.bil` data downloader and spatial slicer (coming soon)
- Planned extensions for NetCDF time series and spatial trend analysis

## Structure

- `wd50_calculation.py` – main script for calculating WD50 for a single station
- `home.csv`, `SLO.csv` – sample outputs for Irvine and San Luis Obispo (ignored in Git)
- `venv/` – local Python environment (also ignored in Git)

## Author

Armaan Saxena
