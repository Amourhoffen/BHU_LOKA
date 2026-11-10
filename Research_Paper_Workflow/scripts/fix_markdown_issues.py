import re
import os

review_dir = r"Bhu Loka - भूलोक/Research_Paper_Workflow/Review"

# -------------------------------------------------------------
# 1. FIX 01_Comprehensive_Literature_Review.md
# -------------------------------------------------------------
f01_path = os.path.join(review_dir, "01_Comprehensive_Literature_Review.md")
with open(f01_path, "r", encoding="utf-8") as f:
    c01 = f.read()

# Fix header multiple spaces (MD019)
c01 = re.sub(r"^#\s\s+", "# ", c01, flags=re.MULTILINE)
c01 = re.sub(r"^##\s\s+", "## ", c01, flags=re.MULTILINE)

# Diagram 1: Random CV vs SBCV (Lines 90-100)
diagram1_target = """```
RANDOM CROSS-VALIDATION (LEAKAGE)           SPATIAL BLOCK CROSS-VALIDATION (ROBERTS ET AL.)
┌─────────────────────────────────┐        ┌─────────────────┬─────────────────┐
│ • Train  o Test                 │        │  BLOCK 1        │  BLOCK 2        │
│   •   o   •   o   •   o   •   o │        │  (All Train)    │  (HELD OUT TEST)│
│ o   •   o   •   o   •   o   •   │        │  •  •  •  •  •  │  o  o  o  o  o  │
│   •   o   •   o   •   o   •   o │        ├─────────────────┼─────────────────┤
│ [Proximate test points leak     │        │  BLOCK 3        │  BLOCK 4        │
│  training autocorrelation]      │        │  (All Train)    │  (All Train)    │
└─────────────────────────────────┘        └─────────────────┴─────────────────┘
```"""

diagram1_replacement = """```mermaid
flowchart LR
    subgraph RCV ["Naive Random Cross-Validation (Data Leakage)"]
        direction TB
        R1["Random Pixel Assignment"] --> R2["Proximate Spatial Points Intermixed"]
        R2 --> R3["Spatial Autocorrelation Leakage"]
        R3 --> R4["Artificially Inflated R² = 0.9688"]
    end

    subgraph SBCV ["Spatial Block Cross-Validation (Roberts et al. 2016)"]
        direction TB
        S1["Domain Partitioned into 5 Blocks"] --> S2["Entire Regional Block Held Out"]
        S2 --> S3["Zero Neighborhood Leakage"]
        S3 --> S4["Honest Generalization Skill R² = 0.7678<br/>(20.1% Honest Leakage Penalty)"]
    end
```"""

c01 = c01.replace(diagram1_target, diagram1_replacement)

# Diagram 2: UNU-ITC Risk (Lines 171-185)
diagram2_target = """```
                           ┌──────────────────────────────────────────────┐
                           │   UNU-ITC MULTI-HAZARD RISK ARCHITECTURE     │
                           └──────────────────────┬───────────────────────┘
                                                  │
                ┌─────────────────────────────────┼─────────────────────────────────┐
                ▼                                 ▼                                 ▼
    ┌──────────────────────┐          ┌──────────────────────┐          ┌──────────────────────┐
    │  HAZARD (H)          │          │  EXPOSURE (E)        │          │  VULNERABILITY (V)   │
    │  • Pluvial Runoff    │          │  • Population Raster │          │  • Building Typology │
    │  • Thermal Stress    │          │  • Critical Roads    │          │  • Drainage Capacity │
    │  • Return Periods    │          │  • Health Facilities │          │  • Pumping Redundancy│
    └──────────────────────┘          └──────────────────────┘          └──────────────────────┘
```"""

diagram2_replacement = """```mermaid
flowchart TD
    ROOT["UNU-ITC Multi-Hazard Risk Architecture<br/>Risk = Hazard × Exposure × Vulnerability"]
    ROOT --> H["Hazard (H)<br/>• Pluvial Runoff Depth<br/>• Thermal Stress (LST > 40°C)<br/>• Return Period Storms"]
    ROOT --> E["Exposure (E)<br/>• WorldPop Demographic Density<br/>• Critical Transport Arteries<br/>• Primary Health Facilities"]
    ROOT --> V["Vulnerability (V)<br/>• Impervious Surface Fraction<br/>• Drainage Conduit Capacity<br/>• Municipal Sump Pumping Deficits"]
```"""

c01 = c01.replace(diagram2_target, diagram2_replacement)

# Section 9: Synthesis & Value Proposition (Lines 239-259)
section9_target = """```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  EXISTING LITERATURE STATUS                                   │
├──────────────────────────────┬───────────────────────────────┬───────────────────────────────┤
│ Ganguli et al. (2025)        │ Coastal Chennai focus         │ Lacks continental river basin │
│ Singh et al. (2026)          │ Delhi multi-hazard LightGBM   │ No thermodynamic coupling     │
│ Roberts et al. (2016)        │ Methodological warning        │ Widely ignored in Indian GeoAI│
│ GSMA / J-Alert               │ Infrastructure blue-sky specs │ Disconnected from spatial ML  │
└──────────────────────────────┴───────────────────────────────┴───────────────────────────────┘
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                BHU LOKA (भूलोक) INNOVATION                                   │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. First coupled thermodynamic heatwave-flood sequential hazard model for the Gangetic plain │
│ 2. Implementation of Spatial Block Cross-Validation eliminating spatial autocorrelation bias │
│ 3. Quantile LightGBM isolating 90th percentile catastrophic municipal risk thresholds        │
│ 4. Game-theoretic Tree-SHAP attribution mapping local drivers across Patna's 75 wards        │
│ 5. Policy bridging toward CAP/GSMA-compliant cell broadcast early warning systems            │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```"""

section9_replacement = """### 9.1 Research Gap vs. BHU LOKA Resolution Matrix

| Research Dimension | Existing Literature Benchmark | Documented Operational Gap | BHU LOKA Breakthrough Resolution |
| :--- | :--- | :--- | :--- |
| **Thermodynamic Coupling** | Ganguli et al. (2025) | Focused strictly on coastal maritime Chennai; ignores continental alluvial river basins. | Formulates the coupled non-linear runoff amplification function $\\Psi(T_{\\text{LST}})$ for Gangetic alluvial clay soils under severe pre-monsoon baking. |
| **Spatial Validation Rigor** | Roberts et al. (2016) | Standard random $k$-fold cross-validation artificially inflates accuracy by $>20\\%$ due to spatial autocorrelation. | Enforces strict 5-fold Spatial Block Cross-Validation (SBCV), quantifying an honest baseline drop ($R^2 = 0.9688 \\to 0.7678$). |
| **Tail Risk Optimization** | Singh et al. (2026) | Conditional mean regression models average out tail extremes, failing during flash deluges. | Deploys asymmetric pinball loss at $\\alpha = 0.90$ to isolate catastrophic 90th percentile stormwater thresholds. |
| **Game-Theoretic XAI** | Black-box GeoAI | Municipal authorities and engineers reject opaque deep learning models without spatial accountability. | Employs Tree-SHAP decomposition to map exact biophysical feature contributions across Patna's 75 municipal wards. |
| **Early Warning Telemetry** | J-Alert / GSMA (2023) | High-level telecom blueprints remain disconnected from localized Earth observation and machine learning rasters. | Synthesizes Common Alerting Protocol (CAP ITU X.1303) standards with ward-level spatial hazard indices for targeted cellular dissemination. |

### 9.2 Conceptual Innovation Flowchart

```mermaid
flowchart TD
    subgraph LIT ["Status of Existing Literature & Current Limitations"]
        direction TB
        L1["Ganguli et al. (2025): Coastal focus, lacks continental Gangetic basin dynamics"]
        L2["Singh et al. (2026): Delhi multi-hazard LightGBM, lacks thermodynamic coupling"]
        L3["Roberts et al. (2016): Methodological warning widely ignored in Indian GeoAI"]
        L4["GSMA & J-Alert: High-level infrastructure disconnected from localized spatial ML"]
    end

    subgraph CORE ["BHU LOKA (भूलोक) Core Innovations"]
        direction TB
        C1["1. First coupled thermodynamic heatwave-flood hazard model for Gangetic plain"]
        C2["2. Spatial Block Cross-Validation eliminating 20.1% spatial autocorrelation bias"]
        C3["3. Quantile LightGBM isolating 90th percentile catastrophic municipal risk"]
        C4["4. Game-theoretic Tree-SHAP attribution mapping local drivers across 75 wards"]
        C5["5. Policy bridge toward CAP and GSMA-compliant cell broadcast early warnings"]
    end

    LIT ==> CORE
```"""

c01 = c01.replace(section9_target, section9_replacement)

# Fix bibliography numbering: 9-16 -> 1-8
c01 = re.sub(r"^9\.\s+\*\*Jato-Espino", "1. **Jato-Espino", c01, flags=re.MULTILINE)
c01 = re.sub(r"^10\.\s+\*\*Roberts", "2. **Roberts", c01, flags=re.MULTILINE)
c01 = re.sub(r"^11\.\s+\*\*Ganguli", "3. **Ganguli", c01, flags=re.MULTILINE)
c01 = re.sub(r"^12\.\s+\*\*Singh", "4. **Singh", c01, flags=re.MULTILINE)
c01 = re.sub(r"^13\.\s+\*\*Rohini", "5. **Rohini", c01, flags=re.MULTILINE)
c01 = re.sub(r"^14\.\s+\*\*Van Westen", "6. **Van Westen", c01, flags=re.MULTILINE)
c01 = re.sub(r"^15\.\s+\*\*GSMA", "7. **GSMA", c01, flags=re.MULTILINE)
c01 = re.sub(r"^16\.\s+\*\*Tallapragada", "8. **Tallapragada", c01, flags=re.MULTILINE)

# Remove multiple consecutive blank lines (MD012)
c01 = re.sub(r"\n{3,}", "\n\n", c01)

# Remove trailing whitespace except intentional double space (MD009)
lines01 = [line.rstrip() + "  " if line.endswith("  ") else line.rstrip() for line in c01.splitlines()]
c01 = "\n".join(lines01) + "\n"

with open(f01_path, "w", encoding="utf-8") as f:
    f.write(c01)
print("Updated 01_Comprehensive_Literature_Review.md successfully")


# -------------------------------------------------------------
# 2. FIX 02_Peer_Review_Methodology_and_Results.md
# -------------------------------------------------------------
f02_path = os.path.join(review_dir, "02_Peer_Review_Methodology_and_Results.md")
with open(f02_path, "r", encoding="utf-8") as f:
    c02 = f.read()

c02 = re.sub(r"^#\s\s+", "# ", c02, flags=re.MULTILINE)
c02 = re.sub(r"^##\s\s+", "## ", c02, flags=re.MULTILINE)

diagram_p02_target = """```
                               ┌──────────────────────────────────┐
                               │  Earth Observation Ingestion     │
                               │  (Sentinel-1, S-2, SRTM, IMD)    │
                               └─────────────────┬────────────────┘
                                                 │
                                                 ▼
                               ┌──────────────────────────────────┐
                               │ Spatial Feature Engineering      │
                               │ Elevation, Slope, LST, Rainfall  │
                               └─────────────────┬────────────────┘
                                                 │
                                                 ▼
                               ┌──────────────────────────────────┐
                               │ Spatial Block Cross-Validation   │
                               │ 5 Independent Regional Blocks    │
                               └─────────────────┬────────────────┘
                                                 │
                         ┌───────────────────────┴───────────────────────┐
                         ▼                                               ▼
           ┌───────────────────────────┐                   ┌───────────────────────────┐
           │ Quantile LightGBM/GBR     │                   │ Game-Theoretic XAI        │
           │ Median (q=0.50)           │                   │ Tree-SHAP Values          │
           │ Tail Risk (q=0.90)        │                   │ Local Driver Attribution  │
           └───────────────────────────┘                   └───────────────────────────┘
```"""

diagram_p02_replacement = """```mermaid
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

c02 = c02.replace(diagram_p02_target, diagram_p02_replacement)
c02 = re.sub(r"\n{3,}", "\n\n", c02)
lines02 = [line.rstrip() + "  " if line.endswith("  ") else line.rstrip() for line in c02.splitlines()]
c02 = "\n".join(lines02) + "\n"

with open(f02_path, "w", encoding="utf-8") as f:
    f.write(c02)
print("Updated 02_Peer_Review_Methodology_and_Results.md successfully")


# -------------------------------------------------------------
# 3. FIX 03_Senior_Researcher_Supervision_Roadmap.md
# -------------------------------------------------------------
f03_path = os.path.join(review_dir, "03_Senior_Researcher_Supervision_Roadmap.md")
with open(f03_path, "r", encoding="utf-8") as f:
    c03 = f.read()

c03 = re.sub(r"^#\s\s+", "# ", c03, flags=re.MULTILINE)
c03 = re.sub(r"^##\s\s+", "## ", c03, flags=re.MULTILINE)

# Fix code block without language
c03 = c03.replace("```\nPHASE 1: Real Earth Observation", "```text\nPHASE 1: Real Earth Observation")
c03 = re.sub(r"\n{3,}", "\n\n", c03)
lines03 = [line.rstrip() + "  " if line.endswith("  ") else line.rstrip() for line in c03.splitlines()]
c03 = "\n".join(lines03) + "\n"

with open(f03_path, "w", encoding="utf-8") as f:
    f.write(c03)
print("Updated 03_Senior_Researcher_Supervision_Roadmap.md successfully")


# -------------------------------------------------------------
# 4. FIX 04_Master_Research_Compendium_and_PhD_Blueprint.md
# -------------------------------------------------------------
f04_path = os.path.join(review_dir, "04_Master_Research_Compendium_and_PhD_Blueprint.md")
with open(f04_path, "r", encoding="utf-8") as f:
    c04 = f.read()

c04 = re.sub(r"^#\s\s+", "# ", c04, flags=re.MULTILINE)
c04 = re.sub(r"^##\s\s+", "## ", c04, flags=re.MULTILINE)

# Diagram 1: 8 Pillars (Lines 23-37)
diagram_p04_1_target = """```
                                    ┌──────────────────────────────────────────────┐
                                    │    BHU LOKA MULTI-DISCIPLINARY SYNTHESIS    │
                                    └──────────────────────┬───────────────────────┘
                                                           │
         ┌──────────────────────────────┬──────────────────┴───────────────┬──────────────────────────────┐
         ▼                              ▼                                  ▼                              ▼
┌──────────────────┐           ┌──────────────────┐               ┌──────────────────┐           ┌──────────────────┐
│ Pillar I & II    │           │ Pillar III & IV  │               │ Pillar V & VI    │           │ Pillar VII & VIII│
│ Thermodynamics & │           │ Spatial AI &     │               │ Atmospheric &    │           │ Civil Protection │
│ Spatial Rigor    │           │ Tail Risk        │               │ Geoinformatics   │           │ & NWP Downscaling│
│ • Ganguli (2025) │           │ • Singh (2026)   │               │ • Rohini (2025)  │           │ • Boni (2025)    │
│ • Roberts (2016) │           │ • Jato-Espino    │               │ • van Westen     │           │ • Tallapragada   │
└──────────────────┘           └──────────────────┘               └──────────────────┘           └──────────────────┘
```"""

diagram_p04_1_replacement = """```mermaid
flowchart TD
    CORE["BHU LOKA Multi-Disciplinary Synthesis"]
    CORE --> P1["Pillars I & II: Thermodynamics & Spatial Rigor<br/>• Ganguli et al. (2025)<br/>• Roberts et al. (2016)"]
    CORE --> P2["Pillars III & IV: Spatial AI & Tail Risk<br/>• Singh et al. (2026)<br/>• Jato-Espino et al. (2024)"]
    CORE --> P3["Pillars V & VI: Atmospheric & Geoinformatics<br/>• Rohini et al. (2025)<br/>• van Westen et al. (2011)"]
    CORE --> P4["Pillars VII & VIII: Civil Protection & NWP Downscaling<br/>• Boni et al. (2025)<br/>• Tallapragada et al. (2026)"]
```"""

c04 = c04.replace(diagram_p04_1_target, diagram_p04_1_replacement)

# Diagram 2: SAR Physics (Lines 150-165)
diagram_p04_2_target = """```
                            ┌──────────────────────────────────────────────┐
                            │    SAR ACTIVE MICROWAVE SENSING PHYSICS     │
                            └──────────────────────┬───────────────────────┘
                                                   │
                ┌──────────────────────────────────┴──────────────────────────────────┐
                ▼                                                                     ▼
    ┌──────────────────────┐                                              ┌──────────────────────┐
    │  ROUGH URBAN SURFACES│                                              │  SMOOTH FLOOD WATER  │
    │  • Diffuse / Double  │                                              │  • Specular Mirror   │
    │    Bounce Scattering │                                              │    Reflection        │
    │  • High Backscatter  │                                              │  • Low Backscatter   │
    │    (σ0 > -10 dB)     │                                              │    (σ0 < -18 dB)     │
    │  • BRIGHT PIXELS     │                                              │  • DARK PIXELS       │
    └──────────────────────┘                                              └──────────────────────┘
```"""

diagram_p04_2_replacement = """```mermaid
flowchart TD
    SAR["SAR Active Microwave Sensing Physics (Sentinel-1 C-Band)"]
    SAR --> URBAN["Rough Urban Surfaces<br/>• Diffuse and Double-Bounce Scattering<br/>• High Backscatter: σ⁰ > -10 dB<br/>• Bright Pixels"]
    SAR --> WATER["Smooth Flood Water Surfaces<br/>• Specular Mirror Reflection Away From Sensor<br/>• Low Backscatter: σ⁰ < -18 dB<br/>• Dark Pixels"]
```"""

c04 = c04.replace(diagram_p04_2_target, diagram_p04_2_replacement)

# Fix code block without language around line 180
c04 = c04.replace("```\n1. TITLE & ABSTRACT:", "```text\n1. TITLE & ABSTRACT:")

c04 = re.sub(r"\n{3,}", "\n\n", c04)
lines04 = [line.rstrip() + "  " if line.endswith("  ") else line.rstrip() for line in c04.splitlines()]
c04 = "\n".join(lines04) + "\n"

with open(f04_path, "w", encoding="utf-8") as f:
    f.write(c04)
print("Updated 04_Master_Research_Compendium_and_PhD_Blueprint.md successfully")

