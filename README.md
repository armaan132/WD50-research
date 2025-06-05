# WD50 Precipitation Analysis (PRISM Data)

This project computes the Wettest Days 50% (WD50) metric using PRISM daily precipitation data. WD50 is defined as the number of wettest days contributing to 50% of the total annual precipitation—a useful metric for studying precipitation intensification and hydrologic extremes.

## Features

-  **Single-Point WD50 Analysis**  
  Calculates WD50 from daily `.csv` PRISM data for individual locations (e.g., Irvine, San Luis Obispo).

-  **Automated Gridded PRISM Downloader**  
  Downloads daily `.bil` raster data from PRISM for specified dates and years, then crops it to the California region.

-  **NetCDF Converter**  
  Converts downloaded `.bil` files into spatially-aware NetCDF datasets for efficient analysis.

-  **Grid-Based WD50 Testing**  
  Computes WD50 at the first grid cell to test processing workflow (full grid support coming soon).

## File Structure

WD50-research/
│
├── wd50_calculation.py # Script for single-location WD50 using .csv
├── download_prism_test.py # Script to download and convert 3 days of PRISM .bil data
├── wd50_from_gridded.py # WD50 calculation on first grid cell of NetCDF file
├── prism_test/ # Output NetCDF and raw PRISM files (ignored in Git)
├── home.csv, SLO.csv # Sample location data (ignored in Git)
└── venv/ # Local Python environment (ignored in Git)


## Requirements

- Python 3.8+
- `pandas`, `numpy`, `xarray`, `rasterio`, `requests`, `matplotlib` (for plotting, if added later)
