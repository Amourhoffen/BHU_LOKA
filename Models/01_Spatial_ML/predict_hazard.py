"""
BHU LOKA (भूलोक) - Real-Time Spatial Hazard Inference Engine
==============================================================
Loads the trained Spatial Random Forest Checkpoint (bhu_loka_spatial_rf_v1.joblib)
and predicts calibrated flood inundation probability for any location or ward.

Author: Prince Kumar (IIT Patna, PA2511CDH37) & BHU LOKA Research Team
"""

import os
import sys
import numpy as np
import joblib

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHECKPOINT_PATH = os.path.join(BASE_DIR, "Models", "Checkpoints", "bhu_loka_spatial_rf_v1.joblib")

# Coordinates of prominent Patna localities [lon, lat]
LOCATIONS = {
    "rajendra nagar": {"pre_db": -12.4, "post_db": -9.8, "delta_db": 2.6, "elev": 44.5, "slope": 0.4, "sink": 1, "pop": 18400.0},
    "kankarbagh":     {"pre_db": -11.9, "post_db": -9.5, "delta_db": 2.4, "elev": 45.1, "slope": 0.5, "sink": 1, "pop": 22100.0},
    "danapur":        {"pre_db": -11.8, "post_db": -12.1, "delta_db": -0.3, "elev": 52.8, "slope": 1.6, "sink": 0, "pop": 8200.0},
    "patliputra":     {"pre_db": -11.2, "post_db": -9.9, "delta_db": 1.3, "elev": 48.3, "slope": 0.8, "sink": 0, "pop": 12500.0},
    "gandhi maidan":  {"pre_db": -13.2, "post_db": -12.8, "delta_db": 0.4, "elev": 50.1, "slope": 1.1, "sink": 0, "pop": 15800.0}
}

def predict_hazard(name: str):
    name_clean = name.lower().strip()
    if not os.path.exists(CHECKPOINT_PATH):
        print(f"Error: Model checkpoint not found at {CHECKPOINT_PATH}. Please run train_spatial_model.py first.")
        return

    model = joblib.load(CHECKPOINT_PATH)
    
    if name_clean in LOCATIONS:
        d = LOCATIONS[name_clean]
        feat = np.array([[d["pre_db"], d["post_db"], d["delta_db"], d["elev"], d["slope"], d["sink"], d["pop"]]])
        prob = model.predict_proba(feat)[0, 1]
        
        print("\n" + "=" * 65)
        print(f" BHU LOKA ML INFERENCE RESULT: {name_clean.upper()}")
        print("=" * 65)
        print(f"Physical Inputs:")
        print(f"  • Sentinel-1 SAR Backscatter : Pre: {d['pre_db']} dB, Post: {d['post_db']} dB (Δσ⁰: {d['delta_db']:+.1f} dB)")
        print(f"  • Copernicus DEM Topography  : Elev: {d['elev']} m, Slope: {d['slope']}°, Depression Sink: {bool(d['sink'])}")
        print(f"  • WorldPop 2020 Demographics : {d['pop']:,.0f} people/km²")
        print("-" * 65)
        print(f"Machine Learning Assessment:")
        print(f"  • Inundation Probability    : {prob * 100:.2f}%")
        if prob >= 0.70:
            status = "CRITICAL INUNDATION (Severe Urban Waterlogging)"
        elif prob >= 0.40:
            status = "MODERATE RISK (Surface ponding)"
        else:
            status = "SAFE ZONE (High elevation ridge / natural drainage)"
        print(f"  • AI Hazard Classification   : {status}")
        print("=" * 65)
    else:
        print(f"Location '{name}' not in predefined catalog. Available: {list(LOCATIONS.keys())}")

if __name__ == "__main__":
    loc = sys.argv[1] if len(sys.argv) > 1 else "rajendra nagar"
    predict_hazard(loc)

