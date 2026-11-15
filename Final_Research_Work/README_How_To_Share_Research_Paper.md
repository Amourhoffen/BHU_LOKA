# BHU LOKA — Guide: How to Share the Research Paper with NASA Space Apps Challenge

**Team Name:** Amour Hoffen  
**Challenge:** Dancing with the SARs (NASA Space Apps Challenge 2026)  
**Lead:** Prince Kumar (IIT Patna)  
**Member:** Payal Priyadarshini (IIITDM Jabalpur)  

---

## 4 Easy Ways to Share Your Research Paper

### 1. Direct PDF Export from the Interactive Dashboard (Fastest & Easiest)
1. Open `bhu_loka_cyber_dashboard.html` in any web browser (Chrome, Edge, Firefox).
2. In the top command bar, click **`🛰️ DANCING WITH THE SARS (NASA 2026)`** or **`🔬 MODEL EVALUATION`**.
3. In the modal, click the **`📥 DOWNLOAD REPORT (.MD)`** button in the top right.
4. You can also view the full manuscript in the **Overview**, **Performance**, **Horizon**, **Omission**, and **Shelters** tabs.
5. To generate a PDF: Press `Ctrl + P` in the browser, choose **Save as PDF**, and save it as `BHU_LOKA_Research_Paper_Amour_Hoffen.pdf`.

---

### 2. Copying Official Text into the NASA Space Apps Project Submission Portal
When filling out your team page on the official NASA Space Apps website:
1. Open the file [`NASA_Space_Apps_Submission_Amour_Hoffen.md`](./NASA_Space_Apps_Submission_Amour_Hoffen.md).
2. Copy the sections directly into the corresponding portal fields:
   - **Project Name:** `BHU LOKA (भूलोक) — Planetary Digital Twin & Scientific SAR Urban Flood Intelligence`
   - **High-Level Summary:** Section 1
   - **Space Agency Data Used:** Section 2 (Sentinel-1 C-SAR, Copernicus GLO-30, NASA Terra MODIS, NISAR)
   - **How You Addressed the Challenge:** Section 3 (Dihedral corner double-bounce, SBCV validation, safe evacuation routing)
   - **Team Information:**
     - Lead: Prince Kumar (Indian Institute of Technology Patna)
     - Member: Payal Priyadarshini (IIITDM Jabalpur)

---

### 3. Sharing via GitHub Repository
NASA Space Apps requires a public GitHub repository link:
1. In your GitHub repository, ensure the `Final_Research_Work/` folder is committed and pushed.
2. Direct link format:
   ```
   https://github.com/<your-username>/<repo-name>/tree/main/Final_Research_Work
   ```
3. Highlight the key research files in your root `README.md`:
   - `Final_Research_Work/main.tex`: Full LaTeX research paper source
   - `Final_Research_Work/NASA_Space_Apps_Submission_Amour_Hoffen.md`: Challenge submission dossier
   - `Final_Research_Work/Figures/`: Publication-grade empirical SAR, thermal, and cross-validation figures

---

### 4. Compiling the LaTeX Paper into a PDF via Overleaf
If you want a journal-formatted PDF using the InterPore / Nature style template:
1. Go to [Overleaf.com](https://www.overleaf.com) and create a **New Project -> Upload Project**.
2. Upload the `Final_Research_Work/` folder (or zip it).
3. Set compiler to `pdfLaTeX` or `XeLaTeX`.
4. Click **Recompile**.
5. Download the compiled PDF to share directly with judges!

---

## Official Team Citation
```bibtex
@article{KumarPriyadarshini2026,
  author       = {Prince Kumar and Payal Priyadarshini},
  title        = {Sequential Compound Hydro-Thermal Risk and Urban Corner-Reflector Flood Mapping in Continental Alluvial Metropolises: Empirical Earth Observation and Spatial Validation Sensitivity over Patna, India},
  journal      = {NASA Space Apps Challenge 2026: Dancing with the SARs},
  team         = {Amour Hoffen},
  institutions = {Indian Institute of Technology Patna & IIITDM Jabalpur},
  year         = {2026},
  month        = {November}
}
```
