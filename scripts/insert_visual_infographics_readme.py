with open('README.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Insert 2D Workspace Overview Image in Module 2
m2_marker = "* **QGIS/ArcGIS Export:** One-click export of observed inundation and parcel vectors in standard GeoJSON format."
m2_addition = """* **QGIS/ArcGIS Export:** One-click export of observed inundation and parcel vectors in standard GeoJSON format.

<div align="center">

<img width="1200" alt="2D Workspace: Understand the Lake and Its Surroundings in One View" src="Assets/images/bhu_loka_2d_workspace_overview.jpg" />

*Figure: 2D GIS Workspace integrating Satellite Basemaps, Water & FTL Boundary Layers, Building Footprints, Road Corridors, Green Spaces, and Dynamic AOI Selection.*

</div>"""

# 2. Insert 3D Exploded Layer by Layer Image in Module 4
m4_marker = "* **Bharatiya Sakshya Adhiniyam, 2023 (BSA §63) Compliance:** Generates official government-ready electronic evidence dossiers containing cryptographic SHA-256 hashes, acquisition timestamps, sensor calibration levels, and statutory technical screening disclaimers. Completely eliminates speculative automated demolition claims in favor of objective `POTENTIAL SPATIAL OVERLAP — REQUIRES OFFICIAL VERIFICATION`."
m4_addition = """* **Bharatiya Sakshya Adhiniyam, 2023 (BSA §63) Compliance:** Generates official government-ready electronic evidence dossiers containing cryptographic SHA-256 hashes, acquisition timestamps, sensor calibration levels, and statutory technical screening disclaimers. Completely eliminates speculative automated demolition claims in favor of objective `POTENTIAL SPATIAL OVERLAP — REQUIRES OFFICIAL VERIFICATION`.

<div align="center">

<img width="1200" alt="3D Exploded Layers & Multi-Source Analysis Board" src="Assets/images/bhu_loka_3d_exploded_layers_analysis.jpg" />

*Figure: Exploded 3D Layer-by-Layer Visualization (Terrain DEM, Contours, Flood/SAR, Land Use, Water, Greenery, Roads, Buildings, Infrastructure) alongside the Multi-Source Analysis Board for granular spatial screening.*

</div>"""

if m2_marker in text and m4_marker in text:
    text = text.replace(m2_marker, m2_addition)
    text = text.replace(m4_marker, m4_addition)
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully inserted both visual infographics into README.md!")
else:
    print("Could not find markers in README.md!")
