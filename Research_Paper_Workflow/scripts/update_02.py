path = r"Bhu Loka - भूलोक/Research_Paper_Workflow/Review/02_Peer_Review_Methodology_and_Results.md"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

mermaid = """```mermaid
flowchart TD
    EO["Earth Observation Ingestion<br/>(Sentinel-1 C-SAR, Sentinel-2 MSI, NASA SRTM, IMD Gridded Rainfall)"]
    FE["Spatial Feature Engineering<br/>(Elevation, Slope, LST, Impervious Fraction, Design Rainfall)"]
    SBCV["Spatial Block Cross-Validation<br/>(5 Spatially Contiguous Regional Blocks)"]
    QLGBM["Quantile LightGBM / GBR<br/>• Median Hazard Regime (α = 0.50)<br/>• Catastrophic Tail Risk (α = 0.90)"]
    SHAP["Game-Theoretic Explainability<br/>• Tree-SHAP Feature Attributions<br/>• Ward-Level Municipal Decision Limits"]

    EO --> FE
    FE --> SBCV
    SBCV --> QLGBM
    SBCV --> SHAP
```"""

start_str = "```\n                              ┌"
start_idx = content.find(start_str)
end_str = "```\n\n---"
end_idx = content.find(end_str, start_idx) + 3

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + mermaid + content[end_idx:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Updated 02 successfully")
else:
    print("Could not find block", start_idx, end_idx)

