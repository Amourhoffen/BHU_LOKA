import os
import subprocess
import sys

target_dir = r"Bhu Loka - भूलोक\Data\06_LST_Thermal"
os.makedirs(target_dir, exist_ok=True)

netrc_file = os.path.join(target_dir, "_netrc_temp")
cookie_file = os.path.join(target_dir, "_cookie_temp.txt")

# Setup netrc
username = "ljprincekashyap_google"
password = "Prince@262626"

with open(netrc_file, "w", encoding="ascii") as f:
    f.write(f"machine urs.earthdata.nasa.gov login {username} password {password}\n")
    f.write(f"machine urs.earthdata.nasa.gov login ljprincekashyap password {password}\n")

urls = [
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019177.h25v06.061.2020355121942/MOD11A2.A2019177.h25v06.061.2020355121942.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019169.h25v06.061.2020355044455/MOD11A2.A2019169.h25v06.061.2020355044455.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019161.h25v06.061.2020354200935/MOD11A2.A2019161.h25v06.061.2020354200935.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019153.h25v06.061.2020354125423/MOD11A2.A2019153.h25v06.061.2020354125423.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019145.h25v06.061.2020354014045/MOD11A2.A2019145.h25v06.061.2020354014045.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019137.h25v06.061.2020353083911/MOD11A2.A2019137.h25v06.061.2020353083911.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019129.h25v06.061.2020353004458/MOD11A2.A2019129.h25v06.061.2020353004458.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019121.h25v06.061.2020353002435/MOD11A2.A2019121.h25v06.061.2020353002435.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019113.h25v06.061.2020353000224/MOD11A2.A2019113.h25v06.061.2020353000224.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019105.h25v06.061.2020352234040/MOD11A2.A2019105.h25v06.061.2020352234040.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019097.h25v06.061.2020352231814/MOD11A2.A2019097.h25v06.061.2020352231814.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019089.h25v06.061.2020352225637/MOD11A2.A2019089.h25v06.061.2020352225637.hdf"
]

total = len(urls)
successful = 0

print("=" * 65)
print(" DOWNLOADING NASA MODIS LST (PATNA 2019 PRE-MONSOON)")
print(f" Target folder: {target_dir}")
print(f" Total files to download: {total}")
print("=" * 65)

for idx, url in enumerate(urls, 1):
    fname = os.path.basename(url)
    dest_path = os.path.join(target_dir, fname)
    
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 100000:
        print(f"[{idx}/{total}] Already exists: {fname} ({os.path.getsize(dest_path)/(1024*1024):.2f} MB)")
        successful += 1
        continue
    
    print(f"[{idx}/{total}] Downloading {fname}...", flush=True)
    
    cmd = [
        "curl.exe",
        "-f",
        "-b", cookie_file,
        "-c", cookie_file,
        "-L",
        "--netrc-file", netrc_file,
        "-g",
        "-o", dest_path,
        url
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(dest_path) and os.path.getsize(dest_path) > 100000:
        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        print(f"       SUCCESS ({size_mb:.2f} MB)", flush=True)
        successful += 1
    else:
        print(f"       FAILED: {res.stderr[:100]}", flush=True)

# Cleanup netrc and cookie
if os.path.exists(netrc_file):
    os.remove(netrc_file)
if os.path.exists(cookie_file):
    os.remove(cookie_file)

print("=" * 65)
print(f" SUMMARY: {successful}/{total} files downloaded successfully.")
print(" Temporary credential files deleted.")
print("=" * 65)

