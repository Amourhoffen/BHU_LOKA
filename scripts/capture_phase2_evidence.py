import os
import subprocess
import time
import shutil
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading
from functools import partial

BHU_ROOT = Path(r"C:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक")
EVIDENCE_DIR = BHU_ROOT / "Assets" / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_PATH):
    EDGE_PATH = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

PORT = 8122

class SilentHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def run_server():
    handler = partial(SilentHandler, directory=str(BHU_ROOT))
    httpd = HTTPServer(('127.0.0.1', PORT), handler)
    httpd.serve_forever()

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(1.0)
print(f"Local server started on http://127.0.0.1:{PORT}")

temp_dir = Path(os.environ.get("TEMP", r"C:\Temp"))

def capture_screenshot(url, filename, timeout=18):
    temp_target = temp_dir / filename
    if temp_target.exists():
        temp_target.unlink()

    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=1600,1000",
        f"--screenshot={str(temp_target)}",
        url
    ]
    print(f"Capturing {filename} from {url}...")
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f" -> Command timed out after {timeout}s, checking if screenshot was written...")

    time.sleep(1.0)
    final_target = EVIDENCE_DIR / filename
    if temp_target.exists() and temp_target.stat().st_size > 1000:
        shutil.copy2(temp_target, final_target)
        pub_target = BHU_ROOT / "public" / "Assets" / "evidence" / filename
        pub_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(temp_target, pub_target)
        print(f" -> SUCCESS: {filename} ({final_target.stat().st_size:,} bytes)")
    else:
        print(f" -> FAILED to generate {filename}")

# 1. 2D GIS Pan-India Workspace
capture_screenshot(
    f"http://127.0.0.1:{PORT}/bhu_loka_leafmap_interactive.html",
    "phase2_01_2d_gis_pan_india_workspace.png"
)

# 2. State Selection: Bihar (with 38 Districts)
capture_screenshot(
    f"http://127.0.0.1:{PORT}/bhu_loka_leafmap_interactive.html?state=Bihar&districts=1",
    "phase2_02_state_selection_bihar_districts.png"
)

# 3. State Selection: Telangana (with Sovereign Info Card)
capture_screenshot(
    f"http://127.0.0.1:{PORT}/bhu_loka_leafmap_interactive.html?state=Telangana",
    "phase2_03_state_selection_telangana_sovereign.png"
)

# 4. Land Studio Rewritten: Potential Spatial Overlap & Verification Required
capture_screenshot(
    f"http://127.0.0.1:{PORT}/bhu_loka_cyber_dashboard.html?view=studio",
    "phase2_04_land_studio_rewritten_verification.png"
)

print("Finished capture sequence.")
