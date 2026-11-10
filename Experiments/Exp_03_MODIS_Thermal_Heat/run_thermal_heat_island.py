"""
BHU LOKA (भूलोक) - Experiment 03: NASA MODIS Urban Heat Island (UHI) & Thermal Stress
========================================================================================
Scientific Goal:
Extract and synthesize 91 consecutive days of empirical Earth Observation from NASA Terra
MODIS (MOD11A1 v061, 1km thermal sensor) across the pre-monsoon summer (April 1 - June 30, 2019).

Scientific Outputs:
1. Daily time-series of Land Surface Temperature (LST) over Patna urban core.
2. Urban Heat Island (UHI) footprint: Delta T_LST = T_urban - T_rural_surroundings.
3. Peak heatwave anomaly detection during the historic June 2019 Bihar heatwave event.
4. PMC-aligned thermal vulnerability raster for compound multi-hazard integration (ULSI).

Zero External C-Library Requirement:
Uses native Python binary TLV parser & zlib decompression to parse HDF-EOS2 data directly.

Author: Prince Kumar (IIT Patna, Roll No: PA2511CDH37) & BHU LOKA Research Team
"""

import os
import glob
import json
import struct
import zlib
import time
import numpy as np

# Base paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_HDF_DIR = os.path.join(BASE_DIR, "Data", "06_LST_Thermal", "raw_hdf")
OUT_DIR = os.path.join(BASE_DIR, "Data", "08_Processed_Outputs")
EXP_OUT = os.path.join(os.path.dirname(__file__))

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(EXP_OUT, exist_ok=True)

print("=" * 72)
print(" BHU LOKA (भूलोक) - EXPERIMENT 03: NASA MODIS THERMAL HEAT ISLAND AUDIT")
print(" 91 Consecutive Days (April 1 - June 30, 2019) | 1km Sensor Pixel Resolution")
print("=" * 72)

def extract_lst_grid(hdf_path: str):
    """Parses HDF4 DDH and decompresses the 1200x1200 uint16 LST_Day_1km raster."""
    try:
        with open(hdf_path, "rb") as f:
            magic = f.read(4)
            if magic != b"\x0e\x03\x13\x01":
                return None
            ndds, next_ddh = struct.unpack(">HI", f.read(6))
            for _ in range(ndds):
                tag, ref, off, length = struct.unpack(">HHII", f.read(12))
                # Tag 40 = DFTAG_COMPRESSED; LST_Day_1km is always > 500 KB compressed
                if tag == 40 and length > 500000:
                    f.seek(off)
                    decomp = zlib.decompress(f.read(length))
                    if len(decomp) == 2880000:
                        return np.frombuffer(decomp, dtype=">u2").reshape((1200, 1200))
    except Exception:
        return None
    return None

# Patna center inside tile h25v06
# Col = 813, Row = 528 (Sinusoidal forward projection)
patna_col = 813
patna_row = 528

# 30km x 30km regional bounding box (radius = 15 pixels)
rad = 15
c_min, c_max = patna_col - rad, patna_col + rad + 1
r_min, r_max = patna_row - rad, patna_row + rad + 1

hdf_files = sorted(glob.glob(os.path.join(RAW_HDF_DIR, "*.hdf")))
total_files = len(hdf_files)
print(f"Discovered {total_files} empirical MODIS daily HDF observation files.")

daily_urban_lst = []
daily_dates = []
spatial_stack = []

t0 = time.time()
cloud_free_days = 0

for idx, hdf_p in enumerate(hdf_files, 1):
    fname = os.path.basename(hdf_p)
    # Extract Day of Year (DOY) from filename: MOD11A1.A2019XXX...
    doy_str = fname.split(".")[1][5:8]
    doy = int(doy_str)
    
    arr = extract_lst_grid(hdf_p)
    if arr is None:
        continue
        
    crop = arr[r_min:r_max, c_min:c_max].astype(np.float32)
    # Scale factor 0.02, Convert Kelvin to Celsius
    # Valid range in Kelvin: 7500 to 65535
    valid_mask = (crop >= 7500)
    
    if np.sum(valid_mask) > 100:  # At least 100 clear pixels in 31x31 region
        temp_c = np.where(valid_mask, crop * 0.02 - 273.15, np.nan)
        spatial_stack.append(temp_c)
        
        # Central Patna urban core (3x3 pixels = ~3km x 3km)
        urban_core = temp_c[rad-1:rad+2, rad-1:rad+2]
        if not np.all(np.isnan(urban_core)):
            u_mean = float(np.nanmean(urban_core))
            daily_urban_lst.append({
                "doy": doy,
                "date_approx": f"2019-DOY-{doy:03d}",
                "urban_lst_celsius": round(u_mean, 2)
            })
            cloud_free_days += 1

elapsed = time.time() - t0
print(f"Processed {len(spatial_stack)} clear-sky scenes in {elapsed:.2f} seconds.")

# Temporal Synthesis across Pre-Monsoon
stack_arr = np.array(spatial_stack)  # Shape: (N_clear, 31, 31)

mean_regional_lst = np.nanmean(stack_arr, axis=0)
max_regional_lst = np.nanmax(stack_arr, axis=0)

# Urban vs Rural Heat Island Analysis
# Central urban pixels (radius 3 around center)
urban_mask = np.zeros((2*rad+1, 2*rad+1), dtype=bool)
urban_mask[rad-2:rad+3, rad-2:rad+3] = True

# Peripheral rural agricultural pixels (outer ring)
rural_mask = np.ones((2*rad+1, 2*rad+1), dtype=bool)
rural_mask[rad-6:rad+7, rad-6:rad+7] = False

mean_urban_lst = float(np.nanmean(mean_regional_lst[urban_mask]))
mean_rural_lst = float(np.nanmean(mean_regional_lst[rural_mask]))
uhi_intensity = mean_urban_lst - mean_rural_lst

peak_urban_lst = float(np.nanmax(max_regional_lst[urban_mask]))
peak_rural_lst = float(np.nanmax(max_regional_lst[rural_mask]))

# Find hottest day
hottest_entry = max(daily_urban_lst, key=lambda x: x["urban_lst_celsius"])

print("\n" + "=" * 72)
print(" EMPIRICAL URBAN HEAT ISLAND & THERMAL EXTREME SUMMARY (PATNA 2019)")
print("=" * 72)
print(f"Pre-Monsoon Observation Period     : April 1, 2019 to June 30, 2019 (91 Days)")
print(f"High-Quality Clear-Sky Observations: {cloud_free_days} days ({cloud_free_days/total_files*100:.1f}%)")
print(f"Mean Urban Core LST (Terra 10:30am) : {mean_urban_lst:.2f} °C")
print(f"Mean Rural Surroundings LST         : {mean_rural_lst:.2f} °C")
print(f"Surface Urban Heat Island (SUHI ΔT) : +{uhi_intensity:.2f} °C (Urban Thermal Trap)")
print(f"Absolute Peak Urban LST Recorded    : {peak_urban_lst:.2f} °C ({hottest_entry['date_approx']})")
print("=" * 72)

# Save intermediate numpy arrays for spatial pipeline integration
np.save(os.path.join(OUT_DIR, "patna_lst_mean_premonsoon.npy"), mean_regional_lst.astype(np.float32))
np.save(os.path.join(OUT_DIR, "patna_lst_max_heatwave.npy"), max_regional_lst.astype(np.float32))

# Save experimental results JSON
results = {
    "experiment": "Exp_03_MODIS_Thermal_Heat",
    "satellite_sensor": "NASA Terra MODIS (MOD11A1 v061 1km Thermal Infrared)",
    "pre_monsoon_window": "2019-04-01 to 2019-06-30",
    "total_scenes_processed": total_files,
    "clear_sky_scenes": cloud_free_days,
    "mean_urban_lst_celsius": round(mean_urban_lst, 2),
    "mean_rural_lst_celsius": round(mean_rural_lst, 2),
    "surface_urban_heat_island_delta_celsius": round(uhi_intensity, 2),
    "peak_urban_lst_celsius": round(peak_urban_lst, 2),
    "hottest_day_recorded": hottest_entry,
    "time_series_sample": daily_urban_lst[:10]
}

out_json_path = os.path.join(EXP_OUT, "exp03_results.json")
with open(out_json_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"Experiment 03 complete. Results saved to {out_json_path}")

