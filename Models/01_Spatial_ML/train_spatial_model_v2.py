"""
BHU LOKA (भूलोक) — Spatial ML v2.0 (SBCV Ensemble + Zero-Key Global Browser Model)
===================================================================================
Upgrades v1 (ROC-AUC 0.7498, Acc 68.88%) via physically-grounded geomorphological
feature engineering + soft-voting ensemble (HistGradientBoosting + ExtraTrees + RF)
under strict 5-Fold Spatial Block Cross-Validation (zero spatial leakage).

Also trains & exports a compact Global DEM-Only Model (Elevation Rel, Slope, TPI,
TWI, Local Depression Depth) as pure JSON weights so BHU LOKA web users anywhere
on Earth get real trained ML predictions 100% client-side for $0 (zero API cost).
"""
import os, json, time
import numpy as np
from scipy.ndimage import uniform_filter, minimum_filter, maximum_filter
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss

BASE_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR   = os.path.join(BASE_DIR, "Data", "08_Processed_Outputs")
MODEL_DIR = os.path.dirname(__file__)
PUB_VEND  = os.path.join(BASE_DIR, "public", "Assets", "vendor")
ROOT_VEND = os.path.join(BASE_DIR, "Assets", "vendor")

def resize_2d(arr, th, tw):
    """Fast bilinear resize via numpy index interpolation (zero PyTorch overhead)."""
    h, w = arr.shape
    if (h, w) == (th, tw):
        return arr.astype(np.float32)
    y = np.linspace(0, h - 1, th)
    x = np.linspace(0, w - 1, tw)
    y0 = np.floor(y).astype(int); y1 = np.minimum(y0 + 1, h - 1)
    x0 = np.floor(x).astype(int); x1 = np.minimum(x0 + 1, w - 1)
    wy = (y - y0)[:, None]; wx = (x - x0)[None, :]
    top = arr[y0[:, None], x0[None, :]] * (1 - wx) + arr[y0[:, None], x1[None, :]] * wx
    bot = arr[y1[:, None], x0[None, :]] * (1 - wx) + arr[y1[:, None], x1[None, :]] * wx
    return (top * (1 - wy) + bot * wy).astype(np.float32)

t0 = time.time()
print("=== BHU LOKA SPATIAL ML v2.0 — 5-FOLD SBCV TRAINING ===")

y_ras    = np.load(os.path.join(OUT_DIR, "patna_total_flood_v2.npy")).astype(np.uint8)
pmc      = np.load(os.path.join(OUT_DIR, "patna_pmc_mask.npy")).astype(bool)
delta_s0 = np.load(os.path.join(OUT_DIR, "patna_2019_delta_sigma0.npy")).astype(np.float32)
H, W = y_ras.shape

elev_raw  = np.nan_to_num(np.load(os.path.join(OUT_DIR, "patna_dem_elevation_pmc.npy")).astype(np.float32), nan=52.0)
slope_raw = np.nan_to_num(np.load(os.path.join(OUT_DIR, "patna_dem_slope_pmc.npy")).astype(np.float32), nan=0.3)
sinks_raw = np.nan_to_num(np.load(os.path.join(OUT_DIR, "patna_dem_sinks_pmc.npy")).astype(np.float32), nan=0.0)
lst_raw   = np.nan_to_num(np.load(os.path.join(OUT_DIR, "patna_lst_max_heatwave.npy")).astype(np.float32), nan=42.0)

elev  = resize_2d(elev_raw, H, W)
slope = resize_2d(slope_raw, H, W)
sinks = (resize_2d(sinks_raw, H, W) > 0.5).astype(np.float32)
lst   = resize_2d(lst_raw, H, W)
sar_post = -12.0 + delta_s0

# Geomorphological & Multi-Scale Spatial Features
tpi_small = elev - uniform_filter(elev, size=15)
tpi_large = elev - uniform_filter(elev, size=55)
elev_min_local = minimum_filter(elev, size=35)
elev_max_local = maximum_filter(elev, size=35)
rel_elev = (elev - elev_min_local) / np.maximum(0.5, elev_max_local - elev_min_local)
# Topographic Wetness Index proxy: ln(local_concavity_catchment / (tan(slope) + 0.01))
concavity = np.clip(-tpi_large, 0.0, 15.0) + 1.0
twi = np.log((concavity * 40.0) / (np.tan(np.radians(np.clip(slope, 0.05, 45.0))) + 0.015))
sar_mean5 = uniform_filter(delta_s0, size=7)
sar_mean15 = uniform_filter(delta_s0, size=21)
sar_std7 = np.sqrt(np.maximum(0.0, uniform_filter(delta_s0**2, size=7) - sar_mean5**2))

# Sample 60,000 valid PMC pixels with deterministic seed + 5 spatial longitude blocks (same protocol as v1)
valid_y, valid_x = np.where(pmc)
rng = np.random.default_rng(42)
n_samples = min(60000, len(valid_y))
idx = rng.choice(len(valid_y), size=n_samples, replace=False)
sy, sx = valid_y[idx], valid_x[idx]

# 5 geographically contiguous spatial blocks (east-west strips)
edges = np.quantile(sx, np.linspace(0, 1, 6))
blocks = np.digitize(sx, edges[1:-1])

y = y_ras[sy, sx]

feat_names_full = [
    "SAR_Post_dB", "Delta_Sigma0", "SAR_Mean_7x7", "SAR_Mean_21x21", "SAR_Std_7x7",
    "Elevation_m", "Slope_deg", "TPI_Small", "TPI_Large", "Rel_Elev", "TWI", "Is_Sink", "LST_Max_C"
]
X_full = np.column_stack([
    sar_post[sy, sx], delta_s0[sy, sx], sar_mean5[sy, sx], sar_mean15[sy, sx], sar_std7[sy, sx],
    elev[sy, sx], slope[sy, sx], tpi_small[sy, sx], tpi_large[sy, sx], rel_elev[sy, sx], twi[sy, sx],
    sinks[sy, sx], lst[sy, sx]
]).astype(np.float32)

# Global Browser-Runnable DEM-Only Feature Set (zero-key, works globally!)
feat_names_global = ["Rel_Elev", "Slope_deg", "TPI_Large", "TWI", "Is_Sink"]
X_global = np.column_stack([
    rel_elev[sy, sx], slope[sy, sx], tpi_large[sy, sx], twi[sy, sx], sinks[sy, sx]
]).astype(np.float32)

def eval_sbcv(X, model_fn, label):
    folds = []
    for f in range(5):
        te = (blocks == f)
        tr = ~te
        clf = model_fn()
        clf.fit(X[tr], y[tr])
        prob = clf.predict_proba(X[te])[:, 1]
        pred = (prob >= 0.5).astype(int)
        folds.append({
            "fold": f + 1,
            "train_samples": int(tr.sum()),
            "test_samples": int(te.sum()),
            "accuracy": float(accuracy_score(y[te], pred)),
            "precision": float(precision_score(y[te], pred, zero_division=0)),
            "recall": float(recall_score(y[te], pred, zero_division=0)),
            "f1_score": float(f1_score(y[te], pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y[te], prob)),
            "brier_score": float(brier_score_loss(y[te], prob))
        })
    mean_auc = float(np.mean([r["roc_auc"] for r in folds]))
    std_auc  = float(np.std([r["roc_auc"] for r in folds]))
    mean_acc = float(np.mean([r["accuracy"] for r in folds]) * 100.0)
    mean_f1  = float(np.mean([r["f1_score"] for r in folds]))
    mean_br  = float(np.mean([r["brier_score"] for r in folds]))
    print(f"[{label}] SBCV ROC-AUC={mean_auc:.4f} (+/- {std_auc:.4f}) | Acc={mean_acc:.2f}% | F1={mean_f1:.4f} | Brier={mean_br:.4f}")
    return {
        "mean_roc_auc": round(mean_auc, 4),
        "std_roc_auc": round(std_auc, 4),
        "mean_accuracy_pct": round(mean_acc, 2),
        "mean_f1_score": round(mean_f1, 4),
        "mean_brier_score": round(mean_br, 4),
        "fold_results": folds
    }

# 1. Train Full Multi-Sensor Ensemble v2 (HistGB + ExtraTrees + RF soft-vote)
class SoftVoteEnsemble:
    def __init__(self):
        self.hgb = HistGradientBoostingClassifier(max_iter=160, max_depth=7, learning_rate=0.06, min_samples_leaf=40, l2_regularization=1.0, random_state=42)
        self.et  = ExtraTreesClassifier(n_estimators=90, max_depth=14, min_samples_leaf=15, n_jobs=-1, random_state=42)
        self.rf  = RandomForestClassifier(n_estimators=90, max_depth=14, min_samples_leaf=15, n_jobs=-1, random_state=42)
    def fit(self, X, y):
        self.hgb.fit(X, y); self.et.fit(X, y); self.rf.fit(X, y)
        return self
    def predict_proba(self, X):
        p = 0.50 * self.hgb.predict_proba(X) + 0.25 * self.et.predict_proba(X) + 0.25 * self.rf.predict_proba(X)
        return p

res_full = eval_sbcv(X_full, SoftVoteEnsemble, "Full Multi-Sensor Ensemble v2")

# Compute feature importances from final ExtraTrees + RF on full data
et_final = ExtraTreesClassifier(n_estimators=90, max_depth=14, min_samples_leaf=15, n_jobs=-1, random_state=42).fit(X_full, y)
importances = {k: round(float(v), 4) for k, v in zip(feat_names_full, et_final.feature_importances_)}

# 2. Train Global Zero-Key DEM-Only Logistic Model (for 100% FREE client-side browser inference!)
res_global = eval_sbcv(
    X_global,
    lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=400)),
    "Global DEM-Only Browser Model"
)
pipe_global = make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=400)).fit(X_global, y)
scaler = pipe_global.named_steps["standardscaler"]
lr = pipe_global.named_steps["logisticregression"]

v2_metrics = {
    "model_name": "BHU_LOKA_Spatial_Ensemble_v2",
    "evaluation_method": "5-Fold Spatial Block Cross-Validation (SBCV, Zero Leakage)",
    "num_samples": n_samples,
    "v1_baseline": {"mean_roc_auc": 0.7498, "mean_accuracy_pct": 68.88, "mean_f1_score": 0.653, "mean_brier_score": 0.2003},
    "v2_full_multisensor": {**res_full, "features": feat_names_full, "feature_importances": importances},
    "v2_global_dem_browser": {
        **res_global,
        "features": feat_names_global,
        "scaler_mean": [round(float(x), 6) for x in scaler.mean_],
        "scaler_scale": [round(float(x), 6) for x in scaler.scale_],
        "coef": [round(float(x), 6) for x in lr.coef_[0]],
        "intercept": round(float(lr.intercept_[0]), 6)
    },
    "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}

out_json = os.path.join(MODEL_DIR, "spatial_cv_metrics_v2.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(v2_metrics, f, indent=2)

print(f"\nSaved verified metrics to {out_json} in {time.time()-t0:.1f}s")
print("Top Feature Importances:", sorted(importances.items(), key=lambda kv: -kv[1])[:6])
print("Global DEM Browser Coefs:", dict(zip(feat_names_global, v2_metrics["v2_global_dem_browser"]["coef"])))
