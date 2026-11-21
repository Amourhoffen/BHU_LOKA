# BHU LOKA — GEOSPATIAL AI MODEL BENCHMARK & VALIDATION PLAN
**Document ID:** `BL-ML-BENCH-2026-V1`  
**System:** BHU LOKA (भूलोक) Machine Learning Evaluation Framework  
**Validation Standard:** 5-Fold Spatial Block Cross-Validation (SBCV · Zero Spatial Autocorrelation Leakage)

---

## 1. Benchmarking Objectives & Methodology

The goal of this benchmark plan is to rigorously and empirically evaluate candidate geospatial models on representative Indian terrain before selecting the final production weights for the Site Analytics Engine.

Evaluation must strictly follow **Remote Sensing Best Practices**:
1. **Zero Spatial Autocorrelation Leakage:** Random pixel splitting (e.g. 80/20 train/test split on the same scene) inflates performance by 15%–30% because adjacent pixels share identical spatial context. Splitting **must** be conducted using geographically separated spatial blocks ($> 15\text{ km}$ separation).
2. **Multi-Class Evaluation:** Models must be scored across all 7 target land-cover classes plus background:
   - $C_1$: Built-up / Buildings
   - $C_2$: Road Networks
   - $C_3$: Water Bodies (Lakes, Tanks, Rivers)
   - $C_4$: Trees & Forest Canopy
   - $C_5$: Agricultural Cropland
   - $C_6$: Barren Land / Bare Soil
   - $C_7$: Background / Unclassified

---

## 2. Quantitative Evaluation Metrics

### 2.1. Mathematical Definitions
For each class $c \in \{1, \dots, C\}$:
* **Intersection over Union (IoU / Jaccard Index):**
  $$\text{IoU}_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FP}_c + \text{FN}_c}$$
* **Mean Intersection over Union (mIoU):**
  $$\text{mIoU} = \frac{1}{C} \sum_{c=1}^{C} \text{IoU}_c$$
* **Precision (User's Accuracy):**
  $$\text{Precision}_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FP}_c}$$
* **Recall (Producer's Accuracy):**
  $$\text{Recall}_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FN}_c}$$
* **F1-Score (Dice Coefficient):**
  $$F1_c = \frac{2 \cdot \text{Precision}_c \cdot \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c} = \frac{2 \cdot \text{TP}_c}{2 \cdot \text{TP}_c + \text{FP}_c + \text{FN}_c}$$

---

## 3. Four-Zone Indian Agro-Ecological Test Benches

To guarantee pan-India generalization, models will be evaluated across 4 distinct spatial testing blocks:

```
                                  4-ZONE TEST BENCH TOPOLOGY
                                                │
         ┌──────────────────────────────┬───────┴──────────────────────┬──────────────────────────────┐
         ▼                              ▼                              ▼                              ▼
  ZONE 1: INDO-GANGETIC ALLUVIAL  ZONE 2: DECCAN CRATON & TANKS  ZONE 3: COASTAL DELTAIC        ZONE 4: WESTERN GHATS FOREST
  • Location: Patna & Bihta (Bihar)• Location: Hyderabad (Telangana)• Location: Chennai & Delta    • Location: Wayanad (Kerala)
  • Topography: Flat alluvial    • Topography: Hard granite,    • Topography: Low elevation,   • Topography: Rugged terrain,
    plain ($< 0.5^\circ$ slope)    boulder hills ($500\text{m}$)   waterlogging, aquaculture     dense multi-story canopy
  • Features: Dense mohallas,    • Features: Urban lake FTLs,   • Features: Mangroves, tidal   • Features: High biomass,
    intensive paddy/wheat,         peri-urban layouts, open       drains, coastal roads, saline   shrub, shadows on steep
    silt banks                     barren plots                   soils                          valleys
```

---

## 4. Benchmark Execution Matrix & Targets

| Model Candidate | Target Task | mIoU Target (Urban) | mIoU Target (Rural) | F1 Target (Water) | F1 Target (Trees) | Latency Target (T4 GPU) | Max VRAM | License Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SegFormer-B0** | LULC 7-Class (Fast) | $\ge 72.0\%$ | $\ge 68.0\%$ | $\ge 88.0\%$ | $\ge 82.0\%$ | $\le 18\text{ ms}$ | $\le 1.0\text{ GB}$ | ✅ Apache 2.0 |
| **SegFormer-B2** | LULC 7-Class (High-Res) | $\ge 78.5\%$ | $\ge 74.0\%$ | $\ge 91.5\%$ | $\ge 86.0\%$ | $\le 35\text{ ms}$ | $\le 1.8\text{ GB}$ | ✅ Apache 2.0 |
| **Prithvi-EO 2.0** | Bi-Temporal Change (10m) | $\ge 65.0\%$ | $\ge 70.0\%$ | $\ge 85.0\%$ | $\ge 80.0\%$ | $\le 95\text{ ms}$ | $\le 4.0\text{ GB}$ | ✅ Apache 2.0 |
| **DeepForest** | Individual Tree Crowns | N/A (Recall $\ge 82\%$) | N/A (Recall $\ge 85\%$) | N/A | $\ge 84.0\%$ (ITC) | $\le 40\text{ ms}$ | $\le 1.6\text{ GB}$ | ✅ MIT |
| **FastSAM / SAMGeo**| Interactive Click Refine| $\ge 80.0\%$ | $\ge 76.0\%$ | $\ge 92.0\%$ | $\ge 84.0\%$ | $\le 50\text{ ms}$ | $\le 2.0\text{ GB}$ | ✅ Apache 2.0 |

---

## 5. Automated Python Evaluation Script

The benchmark is executed through an automated test harness (`Models/01_Spatial_ML/benchmark_site_models.py`):

```python
import numpy as np
from sklearn.metrics import confusion_matrix

def compute_multiclass_metrics(y_true: np.ndarray, y_pred: np.ndarray, class_names: list) -> dict:
    """
    Computes exact per-class IoU, Precision, Recall, and F1 score
    from ground truth and predicted segmentation masks.
    """
    flat_true = y_true.flatten()
    flat_pred = y_pred.flatten()
    
    # Mask out invalid NODATA pixels (value 255)
    valid_mask = flat_true != 255
    flat_true = flat_true[valid_mask]
    flat_pred = flat_pred[valid_mask]
    
    num_classes = len(class_names)
    cm = confusion_matrix(flat_true, flat_pred, labels=list(range(num_classes)))
    
    results = {}
    ious = []
    
    for i, name in enumerate(class_names):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        
        denom_iou = tp + fp + fn
        iou = tp / denom_iou if denom_iou > 0 else 0.0
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        results[name] = {
            "iou": float(np.round(iou * 100, 2)),
            "precision": float(np.round(precision * 100, 2)),
            "recall": float(np.round(recall * 100, 2)),
            "f1": float(np.round(f1 * 100, 2))
        }
        ious.append(iou)
        
    results["mean_iou"] = float(np.round(np.mean(ious) * 100, 2))
    return results
```

---

## 6. Scientific Reporting Protocol

When presenting Site Analytics results to government users or researchers, the UI must display:
1. **Model Name & Version:** e.g., `SegFormer-B0-LoveDA-v1.4`
2. **Sensor Source:** e.g., `Sentinel-2B L2A (10m) · Tile 44QMF`
3. **Acquisition Timestamp:** e.g., `14 Nov 2026 05:12:30 UTC`
4. **Spatial Resolution:** e.g., `GSD: 10.0 m/pixel`
5. **Confidence Range:** e.g., `Mean Softmax Probability: 0.84 ± 0.09`
6. **Honesty Tag:** `MODEL_PREDICTION (UNVERIFIED FIELD AUDIT REQUIRED)`
