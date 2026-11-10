# BHU LOKA (भूलोक) - Model Zoo & Geospatial Foundation Architectures

## Overview
The `Models` directory houses the machine learning, deep learning, and geospatial foundation model architectures powering Project **BHU LOKA (भूलोक)**.

```
Models/
├── 01_Spatial_ML/               # Tabular and Spatial Machine Learning
│   ├── spatial_block_cv.py      # 5-fold Spatial Block Cross-Validation (SBCV)
│   ├── quantile_lightgbm.py     # Quantile Gradient Boosting for uncertainty intervals
│   └── random_forest_spatial.py # Spatial Random Forest baseline
├── 02_Deep_Learning_Backbones/  # Spatial Vision & Segmentation
│   ├── spatial_unet.py          # Multi-band U-Net for pixel-level hazard segmentation
│   └── feature_pyramid.py       # Multi-scale feature extraction for multi-sensor inputs
├── 03_Geo_GPT_Foundation/       # Geospatial Foundation & Small Language Models
│   ├── nanogpt_geo_educational.py # First-principles Transformer built in PyTorch (Educational)
│   ├── geo_slm_adapter.py       # Multi-modal raster-to-text projection layer
│   └── fine_tune_lora.py        # LoRA fine-tuning pipeline for domain decision-support
└── Checkpoints/                 # Saved model weights (.pt, .safetensors, .joblib)
```

---

## Geospatial AI Paradigm: From Classical ML to Geo-Foundation Models

### 1. Spatial Machine Learning (`01_Spatial_ML/`)
- **Spatial Block Cross-Validation (SBCV)**:
  Standard random cross-validation yields inflated accuracy metrics due to Tobler's First Law of Geography (spatial autocorrelation between neighboring pixels). We enforce contiguous spatial blocking ($5\text{ km} \times 5\text{ km}$ spatial folds) to test true generalization.
- **Uncertainty Quantification**:
  Predictions are rendered as calibrated probability distributions ($10^{\text{th}}, 50^{\text{th}}, 90^{\text{th}}$ percentiles) using pinball loss optimization.

### 2. Geo-GPT / Geo-SLM Foundation Architecture (`03_Geo_GPT_Foundation/`)
Building or adapting a domain-specific Geospatial Large Language Model operates on two distinct scientific tiers:

#### Tier A: First-Principles Educational Transformer (`nanogpt_geo_educational.py`)
- Purpose: Build a decoder-only Transformer from scratch using pure PyTorch.
- Enables deep understanding of:
  - Multi-Head Scaled Dot-Product Self-Attention:
    $$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{Q K^T}{\sqrt{d_k}}\right) V$$
  - Causal masking to prevent lookahead bias.
  - Rotary / Learnable positional embeddings.
  - Residual connections and Pre-Layer Normalization.

#### Tier B: SOTA Multi-Modal Geospatial Foundation Adaptation (`geo_slm_adapter.py` + LoRA)
- Purpose: Connect empirical earth observation features with open-weight compact language models (e.g., **Qwen2.5-1.5B/3B**, **Llama-3.2-1B/3B**, or **SmolLM2-1.7B**).
- Architecture:
  1. **Earth Observation Encoder**: Extracts spatial vector representations from Sentinel-1 SAR + Copernicus DEM + MODIS LST + WorldPop.
  2. **Multi-Modal Projection Adapter**: Projects the spatial embedding into the LLM's token dimension ($d_{\text{model}}$).
  3. **Low-Rank Adaptation (LoRA)**: Freezes the base language weights and trains low-rank parameter matrices ($W = W_0 + \frac{\alpha}{r} B A$) on curated disaster mitigation and urban planning directives.
  4. **Output**: The model produces scientifically validated hazard explanations, confidence bounds, and actionable civil defense recommendations.

