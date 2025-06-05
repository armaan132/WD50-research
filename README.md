# WD50 Precipitation Analysis (PRISM Data)

This project computes the Wettest Days 50% (WD50) metric using PRISM daily precipitation data. WD50 is defined as the number of wettest days contributing to 50% of the total annual precipitation—a useful metric.

## Features

-  **Single-Point WD50 Analysis**  
  Calculates WD50 from daily `.csv` PRISM data for individual locations (e.g., Irvine, SLO).

-  **Automated Gridded PRISM Downloader**  
  Downloads daily `.bil` raster data from PRISM for specified dates and years, then crops it to the California region.

-  **NetCDF Converter**  
  Converts downloaded `.bil` files into spatially-aware NetCDF datasets for efficient analysis.

-  **Grid-Based WD50 Testing**  
  Computes WD50 at the first grid cell to test processing workflow (full grid support coming soon).

##File Structure

```
WD50-research/
├── data/
│ ├── raw_bil/ # Raw .bil, .hdr, .zip files from PRISM
│ └── processed/ # NetCDF outputs (.nc)
├── scripts/
│ ├── download_prism_test.py # PRISM .bil downloader and NetCDF converter
│ └── wd50_from_gridded.py # Grid-based WD50 test (first cell)
├── wd50_calculation.py # Station-based WD50 using CSV files
├── home.csv, SLO.csv # Sample CSVs for single-location testing (ignored in Git)
├── venv/ # Python virtual environment (ignored)
├── requirements.txt # Python dependencies
└── README.md
```

## Requirements

- Python 3.8+
- `pandas`, `numpy`, `xarray`, `rasterio`, `requests`, `matplotlib` (for plotting, if added later)
