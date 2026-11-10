import os
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT_DIR = r"Bhu Loka - भूलोक\Data\08_Processed_Outputs"
SAR_DIR = r"Bhu Loka - भूलोक\Data\02_SAR_Sentinel1"

mask_path = os.path.join(OUT_DIR, "patna_2019_flood_extent_empirical.npy")
delta_path = os.path.join(OUT_DIR, "patna_2019_delta_sigma0.npy")

inundation = np.load(mask_path)
delta_sigma0 = np.load(delta_path)

print(f"Loaded inundation mask shape: {inundation.shape}")

# For clean publication plotting, downsample by 2x to reduce memory footprint
# Original is 2602 x 1709 -> 1301 x 854 (plenty sharp for 300 DPI)
h, w = inundation.shape
small_h, small_w = h // 2, w // 2

inundation_img = Image.fromarray(inundation * 255).resize((small_w, small_h), Image.NEAREST)
inundation_small = np.array(inundation_img) > 128

delta_img = Image.fromarray(((delta_sigma0 + 20) * (255 / 40)).clip(0, 255).astype(np.uint8)).resize((small_w, small_h), Image.BILINEAR)
delta_small = (np.array(delta_img, dtype=np.float32) / (255 / 40)) - 20.0

# Create figure
fig, axes = plt.subplots(1, 3, figsize=(18, 6), dpi=150)

# Panel A: Backscatter Delta
im0 = axes[0].imshow(delta_small, cmap='coolwarm_r', vmin=-15, vmax=5)
axes[0].set_title("(a) Sentinel-1 Radar Backscatter Drop\n$\Delta\sigma^0 = \sigma^0_{\\text{post}} - \sigma^0_{\\text{pre}}$ (29 vs 23 Sep 2019)", fontsize=11, fontweight='bold')
axes[0].axis('off')
cbar0 = plt.colorbar(im0, ax=axes[0], orientation='horizontal', pad=0.04)
cbar0.set_label("Backscatter Change $\Delta\sigma^0$ (dB)", fontsize=9)

# Panel B: Delta Histogram with Otsu Threshold
axes[1].hist(delta_small[delta_small < 0].flatten(), bins=100, color='#3b82f6', alpha=0.7, density=True)
axes[1].axvline(-3.80, color='red', linestyle='--', linewidth=2, label='Otsu Threshold $T^* = -3.80\\text{ dB}$')
axes[1].set_title("(b) Automated Otsu Bimodal Thresholding\n(Specular Radar Attenuation on Flood Surface)", fontsize=11, fontweight='bold')
axes[1].set_xlabel("Backscatter Difference $\Delta\sigma^0$ (dB)", fontsize=9)
axes[1].set_ylabel("Normalized Density", fontsize=9)
axes[1].legend(loc='upper left', fontsize=9)
axes[1].grid(True, linestyle=':', alpha=0.5)

# Panel C: Extracted Empirical Inundation Extent
base_gray = np.array(delta_img)
axes[2].imshow(base_gray, cmap='gray')
# Create uint8 RGBA overlay
overlay = np.zeros((small_h, small_w, 4), dtype=np.uint8)
# Bright cyan flood water
overlay[inundation_small] = [0, 200, 255, 200]
axes[2].imshow(overlay)
axes[2].set_title(f"(c) Empirical Flood Delineation (Patna Urban Core)\nVerified Inundated: 26.54 km² (5.97% Urban Fabric)", fontsize=11, fontweight='bold')
axes[2].axis('off')

plt.tight_layout()
out_png = os.path.join(OUT_DIR, "patna_2019_flood_extent_empirical.png")
fig.savefig(out_png, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved empirical flood figure: {out_png}")

