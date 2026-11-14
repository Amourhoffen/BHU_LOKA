# Annexure – I: Abstract of Problem Statement
**Indian Institute of Technology Patna**  
**Executive M. Tech. / M.S. Project (Semester III)**

---

### Title: (Not more than 20 words)
**An Uncertainty-Aware Geospatial AI Framework for Multi-Hazard Assessment and Climate-Resilient Urban Land Suitability: A Case Study of Patna, India**  
*(Word Count: 18 words | Compliant with limit <= 20 words)*

---

### Abstract of Problem Statement (Not more than 600 words):

Rapid urbanization across continental alluvial basins in the Indo-Gangetic Plain has accelerated anthropogenic exposure to cascading hydrometeorological and geophysical hazards. In metropolitan riverine settings such as Patna, Bihar—bounded by the hydrodynamic confluence of the Ganges, Son, and Punpun rivers—urban expansion routinely occurs across low-lying, saucer-shaped alluvial depressions without comprehensive prior assessment of multi-hazard vulnerabilities. Critical decisions regarding land acquisition, industrial zoning, infrastructure expansion, and residential construction are currently executed based on fragmented administrative records or uncoupled single-hazard maps that fail to capture the compound interaction of extreme pre-monsoon heatwaves, ground subsidence, pluvial waterlogging, and regional riverine flooding.

This problem is increasingly critical in the contemporary scenario due to escalating climate variability and unplanned urban growth. Prolonged pre-monsoon thermal regimes severely desiccate fine-grained alluvial surface soils, suppressing natural infiltration capacity and escalating subsequent monsoonal flash-flood runoff by more than 40%. Concurrently, high river stages in the Ganges generate persistent backwater pressure, closing gravity drainage outfalls and submerging municipal wards for weeks, as manifested during the catastrophic deluge of September 2019 (342.5 mm rainfall in 72 hours). Furthermore, traditional municipal land-suitability assessments lack spatial uncertainty quantification, resulting in misplaced public infrastructure, severe economic disruption, and public health vulnerabilities.

To address these challenges, this research develops a modular, uncertainty-aware Geospatial Artificial Intelligence (GeoAI) framework calibrated for Patna District. The technical solution couples multi-sensor Earth observation data—specifically C-band active microwave radar from Sentinel-1 and incoming dual-frequency NASA-ISRO SAR (NISAR)—with optical reflectance (Sentinel-2) and high-resolution digital elevation models. Because smooth standing floodwaters induce specular microwave reflection, Synthetic Aperture Radar provides all-weather cloud-penetrating capability during peak monsoon cloudbursts when optical satellites fail. The framework ingests multi-temporal SAR backscatter to map surface water dynamics and combines them with discrete 50-meter hexagonal spatial grids to eliminate graphical vector overlap.

Rather than relying on black-box heuristics, the platform formulates spatial machine learning models using a calibrated Spatial Random Forest ensemble (`scikit-learn`) alongside quantile gradient boosting architectures (`HistGradientBoosting` / LightGBM extension roadmap) to characterize extreme tail inundation risk rather than uninformative conditional means. To remove spatial autocorrelation bias that overestimates conventional machine learning accuracy, models are evaluated through strict 5-block Spatial Block Cross-Validation (SBCV) with empirical feature-importance attributions explaining the physical drivers of risk across municipal wards.

The broader objective of this prototype is to serve as an interactive spatial decision-support system. By evaluating historical flood exposure, surface thermal anomalies, elevation controls, and socio-economic vulnerability, the platform enables urban planners, institutional stakeholders, and citizens to objectively evaluate the safety, resilience, and multi-hazard suitability of land parcels before construction and development, supporting climate-resilient smart-city governance.

*(Total Word Count: 423 words | Compliant with limit <= 600 words)*

---

| **Student Details** | **Supervisor Details** |
| :--- | :--- |
| **Name:** Prince Kumar | **Name:** Pallav Rustogi |
| **Roll Number:** PA2511CDH37 | **Designation:** AI Native Engineer |
| **Programme:** M.S. (CSDA), Semester III | **Affiliation:** AI Native Engineering, India |
| **Department:** Computer Science & Engineering | **Email:** `pallav.rustogi@gmail.com` |
| **Institute:** Indian Institute of Technology Patna | |
| **Signature:** __________________________ | **Signature:** __________________________ |

