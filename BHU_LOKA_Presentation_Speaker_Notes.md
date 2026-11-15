# BHU LOKA — NASA Space Apps Challenge 2026 Presentation Script & Speaker Notes
**Team:** Amour Hoffen  
**Challenge:** Dancing with the SARs  
**Presenters:** Prince Kumar (Team Lead, IIT Patna) & Payal Priyadarshini (IIITDM Jabalpur)  
**Slide Deck:** [BHU_LOKA_Presentation_Amour_Hoffen.html](file:///c:/Users/ljpri/OneDrive/Desktop/Learning%20Pathways/LearningPathways/Bhu%20Loka%20-%20%E0%A4%AD%E0%A5%82%E0%A4%B2%E0%A5%8B%E0%A4%95/BHU_LOKA_Presentation_Amour_Hoffen.html)

---

## 🎯 Quick Navigation & Keyboard Shortcuts
- **Next Slide:** Press `Right Arrow (→)` or `Spacebar` or `PageDown`
- **Previous Slide:** Press `Left Arrow (←)` or `PageUp`
- **Toggle Fullscreen Presentation Mode:** Press `F`
- **Export to 16:9 PDF Slides:** Press `P` (or click the "Print PDF" button at top-right)

---

## 🎙️ Slide-by-Slide Speaker Script (5–7 Minute Presentation)

### Slide 1: Title & Hero Banner (Opening — 45 seconds)
- **Visual:** Cybernetic HUD with NASA Space Apps badge, Team Amour Hoffen roster, and 3 key discovery metric cards.
- **What to Say:**
  > *"Good morning respected judges and mentors. We are Team Amour Hoffen — I am Prince Kumar from IIT Patna, joined by my colleague Payal Priyadarshini from IIITDM Jabalpur. Today, we are proud to present **BHU LOKA (भूलोक)** — a state-of-the-art spatial intelligence framework for sequential compound hydro-thermal risk and urban corner-reflector flood mapping, calibrated for the challenging alluvial terrain of Patna, Bihar."*
- **Key Points to Emphasize:**
  - 95.98% urban radar blindspot exposed and solved.
  - +17.4% runoff surge from antecedent heatwave soil baking.
  - Spatial block cross-validation penalty unmasked.

---

### Slide 2: The Core Scientific Dilemma (Why Standard Satellites Miss Urban Floods — 60 seconds)
- **Visual:** Interactive Chart comparing UN-SPIDER (4.01 km²) vs BHU LOKA Bimodal SAR (99.60 km²).
- **What to Say:**
  > *"Every monsoon, emergency authorities look at satellite flood maps to deploy rescue boats. But here is the alarming scientific truth: traditional algorithms like the UN-SPIDER change detection look only for open-water specular backscatter drops ($\Delta\sigma^0 \le -2.0\text{ dB}$). On open rural lakes, that works. But inside dense cities, vertical masonry walls and standing water act as 90-degree dihedral corner retro-reflectors. Instead of dropping, the radar signal bounces right back to the satellite, surging above $+1.5\text{ dB}$.*
  > 
  > *During Patna's historic deluge, standard thresholding detected only 4.01 square kilometers of water inside the municipal corporation — missing 95.98% of the flooded city! BHU LOKA's bimodal physics unmasked the true 99.60 square kilometers of inundated urban streets."*

---

### Slide 3: Study Basin & The September 2019 Deluge (45 seconds)
- **Visual:** 3-card geomorphology breakdown with Copernicus GLO-30 DEM metrics.
- **What to Say:**
  > *"Why is Patna uniquely vulnerable? Patna sits in a low-relief 'saucer bowl' trapped between the Ganges, Son, and Punpun rivers. The northern riverfront embankment stands at 53 to 55 meters elevation, looking down into southern residential bowls that dip to 44 meters.*
  > 
  > *In September 2019, 342.5 mm of rain fell in 72 hours. Because the Ganges reached danger levels, river outfalls had to be sealed shut to prevent river backflow. Dewatering pumps failed, trapping water in the city for over a week. Our Copernicus 30m GLO-30 DEM analysis reveals that 33.15% (47.24 km²) of the city lies in concave depression sinks, trapping nearly 50,000 residents."*

---

### Slide 4: Compound Hydro-Thermal Cascade (Heatwave to Flood Link — 60 seconds)
- **Visual:** Interactive Runoff Coefficient ($C_{\text{runoff}}$) vs Pre-Monsoon LST curve.
- **What to Say:**
  > *"Disaster models traditionally treat spring heatwaves and autumn flash floods as independent events. But our research reveals a dangerous thermodynamic loop: in continental alluvial basins with fine clay topsoils, pre-monsoon heatwaves exceeding 44°C bake the surface, collapsing soil pores into a hydrophobic crust.*
  > 
  > *Combined with Clausius-Clapeyron atmospheric moisture scaling (6.5% to 7% per Kelvin), when the monsoon depression arrives, rain cannot infiltrate. In our controlled experiments, holding urban impervious density constant, thermal baking alone escalates the runoff coefficient by 17.4%."*

---

### Slide 5: Spatial AI Validation Rigor (SBCV vs Random Leakage — 60 seconds)
- **Visual:** 7-bar chart comparing optimistic Random 5-Fold ($R^2 = 0.9688$) against disjoint Spatial Blocks ($R^2 = 0.8258$, Urban Core $R^2 = 0.5266$).
- **What to Say:**
  > *"A critical contribution of our work is scientific honesty in geospatial machine learning. When models use standard random train-test splits, adjacent pixels leak spatial correlation. Random 5-fold CV claims an unrealistic $R^2$ of 0.9688.*
  > 
  > *Following Roberts et al., we implemented 5-Block Spatial Block Cross-Validation (SBCV), testing completely unseen geographic sectors. True out-of-block performance drops to $R^2 = 0.8258$ — a 14.8% spatial penalty. In the dense Central Urban Core (Block 2), performance drops to 0.5266. BHU LOKA exposes this penalty so civil protection teams know exactly where models must be trusted and where ground truth is required."*

---

### Slide 6: Dual-Track Architecture & Explainability (45 seconds)
- **Visual:** Architecture columns comparing Track 1 (Empirical EO) vs Track 2 (Simulation Proxy) with Tree-SHAP attributions.
- **What to Say:**
  > *"To ensure academic integrity, BHU LOKA strictly separates Track 1 (Empirical Multi-Sensor Earth Observation using Sentinel-1, Copernicus DEM, MODIS, and WorldPop) from Track 2 (Derived Simulation Proxy Benchmark for sensitivity testing).*
  > 
  > *Using Quantile Gradient Boosting ($\alpha = 0.50$ and $0.90$) with Tree-SHAP explainability, we discovered that distance to river confluence and surface elevation dictate normal ponding, but for extreme 90th-percentile storms, impervious urban surface density jumps to become the dominant hazard driver."*

---

### Slide 7: BHU LOKA Operational Cyber Workstation (45 seconds)
- **Visual:** 5 Workstation badges (World 3D, Pan-India Cropper, Human 3D, Precision Agri, Flood Intel).
- **What to Say:**
  > *"This research is not just equations on paper; it is live in the BHU LOKA Cyber Workstation. It features 5 operational workspaces:*
  > *1. World 3D & Solar Twin for Keplerian orbital mechanics.*
  > *2. A Pan-India 3D Geospatial Cropper that extrudes 30m DEM terrain relief for any bounding box across the country.*
  > *3. A 3D Human Clinical Twin translating satellite pollution and floodwaters into human vitals.*
  > *4. Precision Agriculture for farmer crop trading and NDVI monitoring.*
  > *5. Scientific Flood Model Intelligence with bimodal radar swiping and honest 24h to 72h physics-bounded forecasts."*

---

### Slide 8: Citizen Protection, Evacuation Triage & Ground Impact (45 seconds)
- **Visual:** Priority Evacuation Sinks (<48m) vs Designated Safe High-Ground Ridges (>52m) + Citizen Action Plan.
- **What to Say:**
  > *"The ultimate goal is saving lives. BHU LOKA identifies exact evacuation corridors:*
  > *- Where to evacuate FROM: Rajendra Nagar (46.2m) and Kankarbagh (47.1m) with sink trap depths exceeding 2 to 2.8 meters.*
  > *- Where to evacuate TO: Bihta / IIT Patna High Ridge (55.2m, 0.0% flood risk, ULSI 88/100) and Bailey Road Corridor.*
  > *- Immediate Citizen Protocol: Water boiling alerts for submerged shallow tubewells, 48-hour vector warnings for stagnant mosquito breeding, and N95 masks for toxic dried silt particulates (PM2.5 $142\,\mu\text{g/m}^3$)."*

---

### Slide 9: Submission Summary & Mission Accomplished (30 seconds)
- **Visual:** Official NASA Space Apps Challenge 2026 Deliverables Matrix & Team Signoff.
- **What to Say:**
  > *"To conclude, Team Amour Hoffen has delivered:*
  > *1. A publication-grade scientific manuscript formatted for the InterPore Journal.*
  > *2. The complete NASA Space Apps Challenge submission dossier answering all challenge requirements.*
  > *3. A reproducible, open-source cyber workstation transforming Synthetic Aperture Radar from passive observation into lifesaving urban intelligence.*
  > 
  > *Thank you very much. We are now open for your questions and live demonstration!"*
