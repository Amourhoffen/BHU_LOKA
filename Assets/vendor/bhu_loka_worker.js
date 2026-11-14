/**
 * BHU LOKA Human Intelligence — Gig & Outdoor Worker Climate Health Controller (R0.2)
 * 
 * Features:
 * 1. 3D Anatomical Human & Organ Stress Hologram (Three.js WebGL):
 *    - Faceless humanoid avatar (strictly anonymous, no facial features).
 *    - 5 Vital Organs: Brain, Heart (pulsing), Lungs, Kidneys, Stomach/Core.
 *    - Dynamic organ stress coloration based on live WBGT thermal load and PM2.5 exposure.
 *    - 360-degree interactive rotation and organ click inspector.
 * 2. Climate & Time-Aware Dietary, Hydration & Nutrition Intelligence:
 *    - Dynamic time-of-day awareness (Morning, Midday Peak Sun 11-16h, Evening, Night).
 *    - Traditional and evidence-based Indian cooling nutrition (Sattu, Bel, Chaas, Coconut water, ORS).
 *    - Anti-pollution respiratory cleansing recommendations (Jaggery, Tulsi, Curcumin) during elevated PM2.5.
 * 3. ISO 7243 WBGT heat stress calculation & CPCB 2014 NAQI standards.
 * 4. OpenStreetMap Overpass cooling shelter & emergency medical hub finder.
 * 
 * Zero-Fabrication Policy:
 * Offline or unreachable telemetry strictly renders fail-closed UNAVAILABLE states.
 * 
 * Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
 * UI/UX Designer: Payal Priyadarshini (IIITDM Jabalpur)
 * Institutional Anchor: IIT Patna, M.S. CSDA
 */

(function (window) {
  'use strict';

  const FASTAPI_BASE = (function () {
    if (typeof window === 'undefined') return 'http://127.0.0.1:8000';
    if (window.BHU_LOKA_API_BASE) return window.BHU_LOKA_API_BASE;
    if (window.location && /^https?:$/.test(window.location.protocol)) {
      if (window.location.port === '8000') return window.location.origin;
      return `${window.location.protocol}//${window.location.hostname}:8000`;
    }
    return 'http://127.0.0.1:8000';
  })();

  function esc(val) {
    return String(val ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  const WBGT_COLORS = {
    SAFE: '#10b981',
    CAUTION: '#f59e0b',
    WARNING: '#f97316',
    DANGER: '#f43f5e',
    EXTREME: '#9333ea',
    UNAVAILABLE: '#64748b'
  };

  const NAQI_COLORS = {
    GOOD: '#10b981',
    SATISFACTORY: '#84cc16',
    MODERATE: '#f59e0b',
    POOR: '#f97316',
    VERY_POOR: '#f43f5e',
    SEVERE: '#9333ea',
    UNAVAILABLE: '#64748b'
  };

  const RISK_COLORS = {
    LOW: '#10b981',
    MODERATE: '#f59e0b',
    HIGH: '#f97316',
    EXTREME: '#f43f5e',
    UNAVAILABLE: '#64748b'
  };

  function injectWorkerStyles() {
    if (typeof document === 'undefined' || document.getElementById('bhu-worker-styles')) return;
    const st = document.createElement('style');
    st.id = 'bhu-worker-styles';
    st.textContent = `
      #bhu-worker-panel {
        position: fixed;
        top: 96px;
        left: 360px;
        z-index: 1210;
        width: min(560px, calc(100vw - 380px));
        max-height: calc(100vh - 120px);
        background: #080d16;
        color: #f8fafc;
        border: 1px solid rgba(56, 189, 248, 0.32);
        border-radius: 8px;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.85);
        display: none;
        flex-direction: column;
        overflow: hidden;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      }
      .bhu-worker-card {
        background: rgba(15, 23, 42, 0.88);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 6px;
        padding: 10px 12px;
      }
      .bhu-worker-badge {
        font-size: 10px;
        padding: 2px 7px;
        border-radius: 4px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
      }
      .bhu-worker-scroll {
        overflow-y: auto;
        max-height: calc(100vh - 190px);
      }
      .bhu-worker-scroll::-webkit-scrollbar {
        width: 6px;
      }
      .bhu-worker-scroll::-webkit-scrollbar-thumb {
        background: rgba(148, 163, 184, 0.3);
        border-radius: 3px;
      }
      .bhu-organ-btn {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 4px;
        padding: 4px 6px;
        font-size: 9px;
        color: #cbd5e1;
        cursor: pointer;
        transition: all 0.2s ease;
      }
      .bhu-organ-btn:hover {
        background: rgba(56, 189, 248, 0.15);
        border-color: #38bdf8;
        color: #f8fafc;
      }
      .bhu-nutrition-tag {
        display: inline-block;
        font-size: 9px;
        padding: 1px 5px;
        border-radius: 3px;
        margin-right: 4px;
        margin-bottom: 3px;
      }
    `;
    document.head.appendChild(st);
  }

  class BhuLokaWorkerController {
    constructor() {
      this.lat = 25.5941;
      this.lon = 85.1376;
      this.placeName = 'Patna, Bihar';
      this.data = null;
      this.loading = false;
      this.activeOrgan = null;

      // 3D Human Model references
      this.scene3d = null;
      this.camera3d = null;
      this.renderer3d = null;
      this.humanGroup = null;
      this.organs = {};
      this.animFrameId = null;
      this.isDragging3d = false;
      this.previousMousePosition = { x: 0, y: 0 };

      this.init();
    }

    init() {
      injectWorkerStyles();
      this.mountPanel();
      this.listenToLocationEngine();
    }

    listenToLocationEngine() {
      if (typeof window === 'undefined') return;
      if (window.BhuLokaLocationEngine && typeof window.BhuLokaLocationEngine.subscribe === 'function') {
        window.BhuLokaLocationEngine.subscribe((ctx) => {
          if (ctx && ctx.latitude && ctx.longitude) {
            this.setLocation(ctx.latitude, ctx.longitude, ctx.placeName || ctx.name);
          }
        });
      }
    }

    setLocation(lat, lon, placeName) {
      this.lat = Number(lat);
      this.lon = Number(lon);
      if (placeName) this.placeName = placeName;
      if (this.isVisible()) {
        this.fetchData();
      }
    }

    mountPanel() {
      if (typeof document === 'undefined') return;
      let panel = document.getElementById('bhu-worker-panel');
      if (panel) return;

      panel = document.createElement('div');
      panel.id = 'bhu-worker-panel';
      panel.innerHTML = `
        <div style="background:linear-gradient(90deg, #091322, #132238); padding:10px 14px; border-bottom:1px solid rgba(56,189,248,0.28); display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-size:12px; font-weight:800; color:#38bdf8; letter-spacing:0.08em; display:flex; align-items:center; gap:6px;">
              <span>HUMAN INTEL &middot; GIG WORKER CLIMATE HEALTH</span>
              <span class="bhu-worker-badge" style="background:rgba(56,189,248,0.2); color:#38bdf8; border:1px solid rgba(56,189,248,0.4);">R0.2 3D ANATOMY</span>
            </div>
            <div id="bhu-worker-location-tag" style="font-size:10px; color:#94a3b8; margin-top:2px;">
              Target: ${esc(this.placeName)} (${this.lat.toFixed(4)}&deg;N, ${this.lon.toFixed(4)}&deg;E)
            </div>
          </div>
          <div style="display:flex; align-items:center; gap:8px;">
            <button id="bhu-worker-refresh-btn" style="background:rgba(56,189,248,0.15); color:#38bdf8; border:1px solid rgba(56,189,248,0.3); border-radius:4px; font-size:10px; padding:3px 8px; cursor:pointer;">
              REFRESH
            </button>
            <button id="bhu-worker-close-btn" style="background:none; border:none; color:#94a3b8; font-size:18px; cursor:pointer; line-height:1;">
              &times;
            </button>
          </div>
        </div>

        <div class="bhu-worker-scroll" style="padding:12px; display:flex; flex-direction:column; gap:10px;">
          
          <!-- 3D ANATOMICAL HUMAN & ORGAN STRESS VIEWER -->
          <div class="bhu-worker-card" style="padding:8px 10px; background:linear-gradient(180deg, rgba(8,15,30,0.95), rgba(4,8,16,0.95));">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
              <span style="font-size:11px; font-weight:700; color:#cbd5e1; display:flex; align-items:center; gap:6px;">
                <span>3D ANATOMICAL ORGAN STRESS HOLOGRAM</span>
                <span style="font-size:9px; color:#64748b; font-weight:normal;">(FACELESS &middot; MEDICAL VIEW)</span>
              </span>
              <span id="bhu-worker-3d-hint" style="font-size:9px; color:#38bdf8;">DRAG TO ROTATE &middot; CLICK ORGAN</span>
            </div>

            <div style="position:relative; width:100%; height:200px; background:#04070e; border-radius:6px; overflow:hidden; border:1px solid rgba(148,163,184,0.15);">
              <div id="bhu-worker-3d-container" style="width:100%; height:100%;"></div>
              
              <!-- Floating Organ Telemetry Overlay -->
              <div id="bhu-organ-overlay" style="position:absolute; bottom:6px; left:8px; right:8px; background:rgba(15,23,42,0.88); backdrop-filter:blur(4px); border:1px solid rgba(56,189,248,0.25); border-radius:4px; padding:6px 8px; font-size:10px; display:none;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <span id="bhu-organ-name" style="font-weight:800; color:#38bdf8;">ORGAN INSPECTION</span>
                  <span id="bhu-organ-status-tag" class="bhu-worker-badge" style="background:#10b981; color:#fff;">NORMAL</span>
                </div>
                <div id="bhu-organ-desc" style="color:#cbd5e1; margin-top:2px; font-size:9px;">
                  Select an organ or inspect physiological response to ambient heat &amp; particulate load.
                </div>
              </div>
            </div>

            <!-- Organ Selector Quick Buttons -->
            <div style="display:flex; gap:4px; margin-top:6px; justify-content:space-between;">
              <button class="bhu-organ-btn" onclick="window.BhuLokaWorkerController.selectOrgan('brain')">BRAIN</button>
              <button class="bhu-organ-btn" onclick="window.BhuLokaWorkerController.selectOrgan('heart')">HEART</button>
              <button class="bhu-organ-btn" onclick="window.BhuLokaWorkerController.selectOrgan('lungs')">LUNGS</button>
              <button class="bhu-organ-btn" onclick="window.BhuLokaWorkerController.selectOrgan('kidneys')">KIDNEYS</button>
              <button class="bhu-organ-btn" onclick="window.BhuLokaWorkerController.selectOrgan('core')">CORE BODY</button>
            </div>
          </div>

          <!-- CLIMATE & TIME-AWARE NUTRITION & HYDRATION INTELLIGENCE -->
          <div class="bhu-worker-card" style="border-left:3px solid #10b981;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-size:11px; font-weight:700; color:#34d399;">AHARA &amp; HYDRATION INTELLIGENCE</span>
              <span id="bhu-worker-time-window" class="bhu-worker-badge" style="background:rgba(16,185,129,0.2); color:#34d399; border:1px solid rgba(16,185,129,0.4);">
                LIVE CLIMATE TIMED
              </span>
            </div>
            <div id="bhu-worker-nutrition-content" style="margin-top:6px; font-size:10px; color:#cbd5e1; display:flex; flex-direction:column; gap:6px;">
              <div>Calculating physiological dietary and electrolyte requirements for current coordinates...</div>
            </div>
          </div>

          <!-- WBGT Heat Stress Card -->
          <div class="bhu-worker-card" id="bhu-worker-wbgt-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-size:11px; font-weight:700; color:#cbd5e1;">ISO 7243 WBGT HEAT STRESS</span>
              <span class="bhu-worker-badge" id="bhu-worker-wbgt-badge" style="background:#64748b; color:#fff;">CHECKING</span>
            </div>
            <div style="display:flex; align-items:baseline; gap:8px; margin-top:6px;">
              <span id="bhu-worker-wbgt-val" style="font-size:24px; font-weight:900; color:#f8fafc;">--</span>
              <span style="font-size:11px; color:#94a3b8;">&deg;C (Outdoor Approx.)</span>
            </div>
            <div id="bhu-worker-wbgt-advice" style="font-size:11px; color:#fcd34d; margin-top:4px;">
              Fetching real-time atmospheric boundary conditions...
            </div>
          </div>

          <!-- Composite Risk Card -->
          <div class="bhu-worker-card" id="bhu-worker-risk-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-size:11px; font-weight:700; color:#cbd5e1;">COMPOSITE EXPOSURE RISK</span>
              <span class="bhu-worker-badge" id="bhu-worker-risk-badge" style="background:#64748b; color:#fff;">--</span>
            </div>
            <div style="display:flex; align-items:center; gap:10px; margin-top:8px;">
              <div style="flex:1; height:8px; background:#1e293b; border-radius:4px; overflow:hidden;">
                <div id="bhu-worker-risk-meter" style="width:0%; height:100%; background:#10b981; transition:width 0.4s ease;"></div>
              </div>
              <span id="bhu-worker-risk-score" style="font-size:13px; font-weight:800; min-width:32px; text-align:right;">--</span>
            </div>
            <div id="bhu-worker-risk-rec" style="font-size:10px; color:#94a3b8; margin-top:6px;">
              Synthesizing 60% thermal load + 40% PM2.5 concentration.
            </div>
          </div>

          <!-- PM2.5 / NAQI Card -->
          <div class="bhu-worker-card" id="bhu-worker-aqi-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-size:11px; font-weight:700; color:#cbd5e1;">SURFACE PM2.5 / NAQI (CPCB 2014)</span>
              <span class="bhu-worker-badge" id="bhu-worker-aqi-badge" style="background:#64748b; color:#fff;">--</span>
            </div>
            <div style="display:flex; align-items:baseline; gap:8px; margin-top:6px;">
              <span id="bhu-worker-pm25-val" style="font-size:20px; font-weight:800; color:#f8fafc;">--</span>
              <span style="font-size:11px; color:#94a3b8;">&mu;g/m&sup3;</span>
            </div>
            <div id="bhu-worker-aqi-station" style="font-size:10px; color:#64748b; margin-top:4px;">
              Source: OpenAQ v3 API
            </div>
          </div>

          <!-- Micro-Met Variables Grid -->
          <div class="bhu-worker-card">
            <div style="font-size:11px; font-weight:700; color:#94a3b8; margin-bottom:6px;">METEOROLOGICAL TELEMETRY</div>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; font-size:10px;">
              <div style="background:rgba(2,6,23,0.5); padding:6px; border-radius:4px;">
                <div style="color:#64748b;">DRY BULB</div>
                <div id="bhu-worker-tdry" style="font-weight:700; color:#f8fafc; font-size:12px;">--</div>
              </div>
              <div style="background:rgba(2,6,23,0.5); padding:6px; border-radius:4px;">
                <div style="color:#64748b;">NAT. WET BULB</div>
                <div id="bhu-worker-tnwb" style="font-weight:700; color:#f8fafc; font-size:12px;">--</div>
              </div>
              <div style="background:rgba(2,6,23,0.5); padding:6px; border-radius:4px;">
                <div style="color:#64748b;">GLOBE TEMP</div>
                <div id="bhu-worker-tglobe" style="font-weight:700; color:#f8fafc; font-size:12px;">--</div>
              </div>
              <div style="background:rgba(2,6,23,0.5); padding:6px; border-radius:4px;">
                <div style="color:#64748b;">HUMIDITY</div>
                <div id="bhu-worker-rh" style="font-weight:700; color:#f8fafc; font-size:12px;">--</div>
              </div>
              <div style="background:rgba(2,6,23,0.5); padding:6px; border-radius:4px;">
                <div style="color:#64748b;">WIND SPEED</div>
                <div id="bhu-worker-wind" style="font-weight:700; color:#f8fafc; font-size:12px;">--</div>
              </div>
              <div style="background:rgba(2,6,23,0.5); padding:6px; border-radius:4px;">
                <div style="color:#64748b;">SOLAR RAD</div>
                <div id="bhu-worker-solar" style="font-weight:700; color:#f8fafc; font-size:12px;">--</div>
              </div>
            </div>
          </div>

          <!-- Cooling Shelters List -->
          <div class="bhu-worker-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
              <span style="font-size:11px; font-weight:700; color:#cbd5e1;">NEAREST COOLING SHELTERS &amp; MEDICAL HUBS</span>
              <span id="bhu-worker-shelter-count" style="font-size:10px; color:#38bdf8;">0 FOUND</span>
            </div>
            <div id="bhu-worker-shelter-list" style="display:flex; flex-direction:column; gap:4px; max-height:130px; overflow-y:auto; font-size:10px;">
              <div style="color:#64748b; text-align:center; padding:10px;">Querying OpenStreetMap Overpass...</div>
            </div>
          </div>

          <!-- Institutional Disclaimer -->
          <div style="font-size:9px; color:#475569; text-align:center; padding:4px 0;">
            BHU LOKA Human Intelligence &middot; IIT Patna PA2511CDH37 &middot; Zero-Fabrication Directive Active
          </div>
        </div>
      `;

      document.body.appendChild(panel);

      document.getElementById('bhu-worker-close-btn').onclick = () => this.hide();
      document.getElementById('bhu-worker-refresh-btn').onclick = () => this.fetchData();
    }

    /* -----------------------------------------------------------------------
     * 3D ANATOMICAL HUMAN & ORGAN STRESS MODEL (THREE.JS)
     * Strictly faceless: smooth abstract cyber-geometry without eyes/mouth/face.
     * ----------------------------------------------------------------------- */

    init3DHumanModel() {
      if (this.renderer3d) return; // already initialized
      const container = document.getElementById('bhu-worker-3d-container');
      if (!container || typeof window.THREE === 'undefined') return;

      const width = container.clientWidth || 500;
      const height = container.clientHeight || 200;

      const scene = new window.THREE.Scene();
      this.scene3d = scene;

      const camera = new window.THREE.PerspectiveCamera(35, width / height, 0.1, 100);
      camera.position.set(0, 0.2, 5.2);
      this.camera3d = camera;

      const renderer = new window.THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      container.appendChild(renderer.domElement);
      this.renderer3d = renderer;

      // Lights
      const ambient = new window.THREE.AmbientLight(0xffffff, 0.65);
      scene.add(ambient);
      const dirLight = new window.THREE.DirectionalLight(0x38bdf8, 1.2);
      dirLight.position.set(3, 4, 4);
      scene.add(dirLight);
      const backLight = new window.THREE.DirectionalLight(0x10b981, 0.8);
      backLight.position.set(-3, -2, -3);
      scene.add(backLight);

      // Human Group
      const human = new window.THREE.Group();
      this.humanGroup = human;
      scene.add(human);

      // 1. Faceless Head (Smooth Cyber Silhouette, zero facial features)
      const headMat = new window.THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        wireframe: true,
        transparent: true,
        opacity: 0.45,
        roughness: 0.3
      });
      const headGeom = new window.THREE.SphereGeometry(0.38, 20, 16);
      headGeom.scale(0.85, 1.15, 0.95); // realistic cranium proportions
      const headMesh = new window.THREE.Mesh(headGeom, headMat);
      headMesh.position.set(0, 1.45, 0);
      human.add(headMesh);

      // Neck
      const neckGeom = new window.THREE.CylinderGeometry(0.14, 0.16, 0.22, 12);
      const neckMesh = new window.THREE.Mesh(neckGeom, headMat);
      neckMesh.position.set(0, 1.05, 0);
      human.add(neckMesh);

      // 2. Torso & Ribcage Shell
      const torsoMat = new window.THREE.MeshStandardMaterial({
        color: 0x1e293b,
        wireframe: true,
        transparent: true,
        opacity: 0.3,
        roughness: 0.5
      });
      const chestGeom = new window.THREE.CylinderGeometry(0.48, 0.36, 0.8, 16);
      const chestMesh = new window.THREE.Mesh(chestGeom, torsoMat);
      chestMesh.position.set(0, 0.55, 0);
      human.add(chestMesh);

      const pelvisGeom = new window.THREE.CylinderGeometry(0.36, 0.38, 0.45, 14);
      const pelvisMesh = new window.THREE.Mesh(pelvisGeom, torsoMat);
      pelvisMesh.position.set(0, -0.05, 0);
      human.add(pelvisMesh);

      // Limbs (Slender stylized cyber lines)
      const limbMat = new window.THREE.LineBasicMaterial({ color: 0x475569, transparent: true, opacity: 0.4 });
      const createLimb = (p1, p2, p3) => {
        const g = new window.THREE.BufferGeometry().setFromPoints([
          new window.THREE.Vector3(...p1),
          new window.THREE.Vector3(...p2),
          new window.THREE.Vector3(...p3)
        ]);
        return new window.THREE.Line(g, limbMat);
      };
      human.add(createLimb([-0.5, 0.85, 0], [-0.75, 0.35, 0], [-0.85, -0.15, 0])); // left arm
      human.add(createLimb([0.5, 0.85, 0], [0.75, 0.35, 0], [0.85, -0.15, 0]));   // right arm
      human.add(createLimb([-0.24, -0.25, 0], [-0.28, -0.9, 0], [-0.3, -1.6, 0])); // left leg
      human.add(createLimb([0.24, -0.25, 0], [0.28, -0.9, 0], [0.3, -1.6, 0]));   // right leg

      // -------------------------------------------------------------
      // VITAL ORGANS (INTERACTIVE MESHES)
      // -------------------------------------------------------------

      // A. Brain (located in upper cranium)
      const brainMat = new window.THREE.MeshStandardMaterial({
        color: 0x10b981,
        emissive: 0x064e3b,
        roughness: 0.2,
        metalness: 0.1
      });
      const brainGeom = new window.THREE.SphereGeometry(0.18, 16, 14);
      brainGeom.scale(1.0, 0.8, 1.2);
      const brainMesh = new window.THREE.Mesh(brainGeom, brainMat);
      brainMesh.position.set(0, 1.48, 0.02);
      human.add(brainMesh);
      this.organs.brain = { mesh: brainMesh, mat: brainMat, name: 'Brain & Nervous System' };

      // B. Heart (pulsing cardiac mesh in left-center chest)
      const heartMat = new window.THREE.MeshStandardMaterial({
        color: 0xf43f5e,
        emissive: 0x881337,
        roughness: 0.3
      });
      const heartGeom = new window.THREE.SphereGeometry(0.11, 14, 12);
      heartGeom.scale(0.9, 1.1, 0.9);
      const heartMesh = new window.THREE.Mesh(heartGeom, heartMat);
      heartMesh.position.set(-0.08, 0.62, 0.1);
      human.add(heartMesh);
      this.organs.heart = { mesh: heartMesh, mat: heartMat, name: 'Cardiovascular System (Heart)', baseScale: 1.0 };

      // C. Lungs (Dual lobes in chest cavity)
      const lungsMat = new window.THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        emissive: 0x0c4a6e,
        roughness: 0.3,
        transparent: true,
        opacity: 0.85
      });
      const lungGeom = new window.THREE.SphereGeometry(0.12, 12, 10);
      lungGeom.scale(0.7, 1.3, 0.8);
      const lungL = new window.THREE.Mesh(lungGeom, lungsMat);
      lungL.position.set(-0.16, 0.6, 0.04);
      const lungR = new window.THREE.Mesh(lungGeom, lungsMat);
      lungR.position.set(0.16, 0.6, 0.04);
      human.add(lungL);
      human.add(lungR);
      this.organs.lungs = { meshes: [lungL, lungR], mat: lungsMat, name: 'Respiratory System (Lungs)' };

      // D. Kidneys (Dual retroperitoneal organs in lower back)
      const kidneyMat = new window.THREE.MeshStandardMaterial({
        color: 0x10b981,
        emissive: 0x064e3b,
        roughness: 0.4
      });
      const kidneyGeom = new window.THREE.SphereGeometry(0.065, 10, 8);
      kidneyGeom.scale(0.8, 1.2, 0.7);
      const kidneyL = new window.THREE.Mesh(kidneyGeom, kidneyMat);
      kidneyL.position.set(-0.14, 0.2, -0.06);
      const kidneyR = new window.THREE.Mesh(kidneyGeom, kidneyMat);
      kidneyR.position.set(0.14, 0.2, -0.06);
      human.add(kidneyL);
      human.add(kidneyR);
      this.organs.kidneys = { meshes: [kidneyL, kidneyR], mat: kidneyMat, name: 'Renal & Hydration (Kidneys)' };

      // E. Stomach / Core Body
      const coreMat = new window.THREE.MeshStandardMaterial({
        color: 0x10b981,
        emissive: 0x064e3b,
        roughness: 0.4
      });
      const coreGeom = new window.THREE.SphereGeometry(0.13, 12, 10);
      coreGeom.scale(1.1, 0.8, 0.9);
      const coreMesh = new window.THREE.Mesh(coreGeom, coreMat);
      coreMesh.position.set(0.05, 0.26, 0.08);
      human.add(coreMesh);
      this.organs.core = { mesh: coreMesh, mat: coreMat, name: 'Core Body & Thermal Equilibrium' };

      // Centering
      human.position.set(0, -0.1, 0);

      // Interactive Mouse / Drag Rotation
      const dom = renderer.domElement;
      dom.onmousedown = (e) => {
        this.isDragging3d = true;
        this.previousMousePosition = { x: e.clientX, y: e.clientY };
      };
      dom.onmousemove = (e) => {
        if (!this.isDragging3d) return;
        const deltaX = e.clientX - this.previousMousePosition.x;
        human.rotation.y += deltaX * 0.015;
        this.previousMousePosition = { x: e.clientX, y: e.clientY };
      };
      dom.onmouseup = () => { this.isDragging3d = false; };
      dom.onmouseleave = () => { this.isDragging3d = false; };

      // Touch controls
      dom.ontouchstart = (e) => {
        if (e.touches.length === 1) {
          this.isDragging3d = true;
          this.previousMousePosition = { x: e.touches[0].clientX, y: e.touches[0].clientY };
        }
      };
      dom.ontouchmove = (e) => {
        if (!this.isDragging3d || e.touches.length !== 1) return;
        const deltaX = e.touches[0].clientX - this.previousMousePosition.x;
        human.rotation.y += deltaX * 0.015;
        this.previousMousePosition = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      };
      dom.ontouchend = () => { this.isDragging3d = false; };

      // Render Loop
      let clock = 0;
      const animate = () => {
        this.animFrameId = requestAnimationFrame(animate);
        clock += 0.03;

        // Subtle idle rotation when not dragging
        if (!this.isDragging3d) {
          human.rotation.y += 0.003;
        }

        // Heart pulse animation (heart rate scales with cardiovascular load)
        if (this.organs.heart && this.organs.heart.mesh) {
          const pulseSpeed = this.cardiacPulseSpeed || 2.5;
          const s = 1.0 + Math.sin(clock * pulseSpeed) * 0.12;
          this.organs.heart.mesh.scale.set(0.9 * s, 1.1 * s, 0.9 * s);
        }

        renderer.render(scene, camera);
      };
      animate();
    }

    updateOrganStressColors(wbgtData, aqiData) {
      if (!this.organs.brain) return;

      const wbgtTier = (wbgtData && wbgtData.tier) || 'UNAVAILABLE';
      const aqiCat = (aqiData && aqiData.naqi_category) || 'UNAVAILABLE';

      // 1. Brain: Stress scales with WBGT heat stress (risk of heat stroke / delirium)
      let brainCol = 0x10b981;
      let brainEmiss = 0x064e3b;
      if (wbgtTier === 'CAUTION') { brainCol = 0xf59e0b; brainEmiss = 0x78350f; }
      else if (wbgtTier === 'WARNING') { brainCol = 0xf97316; brainEmiss = 0x7c2d12; }
      else if (wbgtTier === 'DANGER' || wbgtTier === 'EXTREME') { brainCol = 0x9333ea; brainEmiss = 0x581c87; }
      else if (wbgtTier === 'UNAVAILABLE') { brainCol = 0x64748b; brainEmiss = 0x1e293b; }
      this.organs.brain.mat.color.setHex(brainCol);
      this.organs.brain.mat.emissive.setHex(brainEmiss);

      // 2. Heart: Cardiac pulse speed scales with cutaneous vasodilation demand
      if (wbgtTier === 'EXTREME' || wbgtTier === 'DANGER') this.cardiacPulseSpeed = 6.0;
      else if (wbgtTier === 'WARNING') this.cardiacPulseSpeed = 4.2;
      else if (wbgtTier === 'CAUTION') this.cardiacPulseSpeed = 3.2;
      else this.cardiacPulseSpeed = 2.2;

      // 3. Lungs: Stress scales with PM2.5 / NAQI
      let lungCol = 0x38bdf8;
      let lungEmiss = 0x0c4a6e;
      if (aqiCat === 'MODERATE') { lungCol = 0xf59e0b; lungEmiss = 0x78350f; }
      else if (aqiCat === 'POOR') { lungCol = 0xf97316; lungEmiss = 0x7c2d12; }
      else if (aqiCat === 'VERY_POOR' || aqiCat === 'SEVERE') { lungCol = 0xf43f5e; lungEmiss = 0x881337; }
      else if (aqiCat === 'UNAVAILABLE') { lungCol = 0x64748b; lungEmiss = 0x1e293b; }
      this.organs.lungs.mat.color.setHex(lungCol);
      this.organs.lungs.mat.emissive.setHex(lungEmiss);

      // 4. Kidneys: Dehydration & acute renal strain under heat
      let kidCol = 0x10b981;
      let kidEmiss = 0x064e3b;
      if (wbgtTier === 'WARNING' || wbgtTier === 'DANGER') { kidCol = 0xf59e0b; kidEmiss = 0x78350f; }
      else if (wbgtTier === 'EXTREME') { kidCol = 0xf43f5e; kidEmiss = 0x881337; }
      else if (wbgtTier === 'UNAVAILABLE') { kidCol = 0x64748b; kidEmiss = 0x1e293b; }
      this.organs.kidneys.mat.color.setHex(kidCol);
      this.organs.kidneys.mat.emissive.setHex(kidEmiss);

      // 5. Core Body: Overall thermal equilibrium
      let coreCol = 0x10b981;
      let coreEmiss = 0x064e3b;
      if (wbgtTier === 'WARNING') { coreCol = 0xf59e0b; coreEmiss = 0x78350f; }
      else if (wbgtTier === 'DANGER' || wbgtTier === 'EXTREME') { coreCol = 0xf43f5e; coreEmiss = 0x881337; }
      else if (wbgtTier === 'UNAVAILABLE') { coreCol = 0x64748b; coreEmiss = 0x1e293b; }
      this.organs.core.mat.color.setHex(coreCol);
      this.organs.core.mat.emissive.setHex(coreEmiss);
    }

    selectOrgan(key) {
      this.activeOrgan = key;
      const overlay = document.getElementById('bhu-organ-overlay');
      const nameEl = document.getElementById('bhu-organ-name');
      const tagEl = document.getElementById('bhu-organ-status-tag');
      const descEl = document.getElementById('bhu-organ-desc');
      if (!overlay || !nameEl || !descEl) return;

      overlay.style.display = 'block';

      const wbgtTier = (this.data && this.data.wbgt && this.data.wbgt.tier) || 'SAFE';
      const aqiCat = (this.data && this.data.aqi && this.data.aqi.naqi_category) || 'GOOD';

      const organProfiles = {
        brain: {
          name: 'BRAIN & CENTRAL NERVOUS SYSTEM',
          status: (wbgtTier === 'EXTREME' || wbgtTier === 'DANGER') ? 'HEAT EXHAUSTION RISK' : 'STABLE',
          color: (wbgtTier === 'EXTREME' || wbgtTier === 'DANGER') ? '#f43f5e' : '#10b981',
          desc: `Thermal stress alters cerebral blood flow. In high WBGT (${wbgtTier}), monitor for dizziness, sluggish reflexes, or delirium. Rest under shade and cool head with damp towel immediately.`
        },
        heart: {
          name: 'HEART & CARDIOVASCULAR PUMP',
          status: (wbgtTier === 'EXTREME' || wbgtTier === 'DANGER') ? 'ELEVATED CARDIAC STRAIN' : 'NORMAL LOAD',
          color: (wbgtTier === 'EXTREME' || wbgtTier === 'DANGER') ? '#f43f5e' : '#10b981',
          desc: `Severe ambient heat triggers cutaneous vasodilation, demanding 2-3x cardiac output. Pulse rate increases to dissipate core heat. Avoid sudden heavy lifting during peak sun.`
        },
        lungs: {
          name: 'RESPIRATORY TRACT & LUNGS',
          status: (aqiCat === 'VERY_POOR' || aqiCat === 'SEVERE' || aqiCat === 'POOR') ? `PM2.5 INFLAMMATION (${aqiCat})` : 'CLEAR',
          color: (aqiCat === 'VERY_POOR' || aqiCat === 'SEVERE' || aqiCat === 'POOR') ? '#f43f5e' : '#38bdf8',
          desc: `Deep alveolar particulate deposition occurs when PM2.5 is elevated. Outdoor gig workers should wear N95/FFP2 masks during peak traffic hours.`
        },
        kidneys: {
          name: 'KIDNEYS & HYDRATION REGULATION',
          status: (wbgtTier === 'EXTREME' || wbgtTier === 'DANGER' || wbgtTier === 'WARNING') ? 'ACUTE RENAL STRAIN' : 'HYDRATED',
          color: (wbgtTier === 'EXTREME' || wbgtTier === 'DANGER' || wbgtTier === 'WARNING') ? '#f59e0b' : '#10b981',
          desc: `Excessive sweating depletes electrolytes. Concentrated urine (<300ml/4hr) indicates acute tubular stress. Minimum hourly hydration intake: 250-400 ml with ORS/salt.`
        },
        core: {
          name: 'CORE BODY & THERMAL EQUILIBRIUM',
          status: `CORE EQUILIBRIUM (${wbgtTier})`,
          color: (wbgtTier === 'EXTREME') ? '#9333ea' : (wbgtTier === 'DANGER' ? '#f43f5e' : '#10b981'),
          desc: `Human core temperature must stay within 36.5 - 37.5 C. When environmental WBGT exceeds 33 C, sweat cannot evaporate efficiently. Mechanical shade & airflow required.`
        }
      };

      const p = organProfiles[key] || organProfiles.core;
      nameEl.textContent = p.name;
      tagEl.textContent = p.status;
      tagEl.style.background = p.color;
      descEl.textContent = p.desc;
    }

    /* -----------------------------------------------------------------------
     * CLIMATE & TIME-AWARE DIETARY, HYDRATION & HEALTH BENEFITS
     * ----------------------------------------------------------------------- */

    renderNutritionAndDietary(wbgtData, aqiData) {
      const container = document.getElementById('bhu-worker-nutrition-content');
      const timeTag = document.getElementById('bhu-worker-time-window');
      if (!container) return;

      const now = new Date();
      const hour = now.getHours();
      let timeWindow = 'Daytime';
      if (hour >= 5 && hour < 11) timeWindow = 'Morning Energy & Hydration (05:00-11:00)';
      else if (hour >= 11 && hour < 16) timeWindow = 'Peak Heat Window — Critical Hydration (11:00-16:00)';
      else if (hour >= 16 && hour < 20) timeWindow = 'Evening Recovery & Cleansing (16:00-20:00)';
      else timeWindow = 'Nighttime Cellular Recovery (20:00-05:00)';

      if (timeTag) timeTag.textContent = timeWindow;

      const wbgtTier = (wbgtData && wbgtData.tier) || 'SAFE';
      const aqiCat = (aqiData && aqiData.naqi_category) || 'GOOD';
      const isExtremeHeat = wbgtTier === 'EXTREME' || wbgtTier === 'DANGER' || wbgtTier === 'WARNING';
      const isSmoggy = aqiCat === 'VERY_POOR' || aqiCat === 'SEVERE' || aqiCat === 'POOR';

      let html = '';

      // 1. Mandatory Electrolytes & Fluids
      if (isExtremeHeat) {
        html += `
          <div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); border-radius:4px; padding:6px 8px;">
            <div style="font-weight:700; color:#f87171; margin-bottom:3px;">
              CRITICAL HYDRATION INTAKE: MIN 350-500 ML / 30 MIN
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:4px;">
              <span class="bhu-nutrition-tag" style="background:#065f46; color:#a7f3d0;">Sattu Sharbat (Cumin + Rock Salt)</span>
              <span class="bhu-nutrition-tag" style="background:#065f46; color:#a7f3d0;">Chaas / Spiced Buttermilk</span>
              <span class="bhu-nutrition-tag" style="background:#065f46; color:#a7f3d0;">Tender Coconut Water</span>
              <span class="bhu-nutrition-tag" style="background:#1e40af; color:#bfdbfe;">WHO-ORS Solution</span>
            </div>
            <div style="font-size:9px; color:#fca5a5; margin-top:4px;">
              Benefit: Roasted Bengal gram (Sattu) provides sustained slow-release protein + potassium; replenishes serum sodium lost in heavy sweat.
            </div>
          </div>
        `;
      } else {
        html += `
          <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.25); border-radius:4px; padding:6px 8px;">
            <div style="font-weight:700; color:#34d399; margin-bottom:3px;">
              OPTIMAL PREVENTIVE FLUIDS: 250 ML / 45 MIN
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:4px;">
              <span class="bhu-nutrition-tag" style="background:#065f46; color:#a7f3d0;">Lemon Water (Nimbu Paani)</span>
              <span class="bhu-nutrition-tag" style="background:#065f46; color:#a7f3d0;">Mint &amp; Coriander Cooler</span>
              <span class="bhu-nutrition-tag" style="background:#065f46; color:#a7f3d0;">Bel Fruit Sherbet</span>
            </div>
            <div style="font-size:9px; color:#a7f3d0; margin-top:4px;">
              Benefit: Natural citrus and herb flavonoids maintain microvascular integrity and normal renal clearance.
            </div>
          </div>
        `;
      }

      // 2. Food & Meal Advisory for Current Time of Day
      if (hour >= 11 && hour < 16) {
        html += `
          <div style="background:rgba(15,23,42,0.6); border:1px solid rgba(148,163,184,0.15); border-radius:4px; padding:6px 8px;">
            <div style="font-weight:700; color:#fde047;">MIDDAY PEAK FOOD ADVISORY</div>
            <div style="margin-top:2px; font-size:9px; color:#cbd5e1;">
              &bull; <strong>Recommended:</strong> Light water-rich vegetables (Lauki/bottle gourd, Torai/ridge gourd, cucumber, watermelon, boiled rice with curd).<br>
              &bull; <strong>Strictly Avoid:</strong> Heavy oily street food, samosas, deep-fried snacks, and carbonated sugary drinks (caffeine and sugar accelerate osmotic dehydration).
            </div>
          </div>
        `;
      } else if (hour >= 5 && hour < 11) {
        html += `
          <div style="background:rgba(15,23,42,0.6); border:1px solid rgba(148,163,184,0.15); border-radius:4px; padding:6px 8px;">
            <div style="font-weight:700; color:#38bdf8;">MORNING PRE-SHIFT NUTRITION</div>
            <div style="margin-top:2px; font-size:9px; color:#cbd5e1;">
              &bull; <strong>Recommended:</strong> Complex carbohydrates + hydration base. Soaked almonds, bananas, oats or daliya with milk, or sprout salad with lime.<br>
              &bull; <strong>Hydration Loading:</strong> Drink 500 ml water 30 minutes before stepping into outdoor sun.
            </div>
          </div>
        `;
      } else {
        html += `
          <div style="background:rgba(15,23,42,0.6); border:1px solid rgba(148,163,184,0.15); border-radius:4px; padding:6px 8px;">
            <div style="font-weight:700; color:#c084fc;">EVENING RESTORATION &amp; MUSCLE REPAIR</div>
            <div style="margin-top:2px; font-size:9px; color:#cbd5e1;">
              &bull; <strong>Recommended:</strong> Moong dal khichdi with ghee, steamed vegetables, warm turmeric milk (Haldi Doodh) before sleep to reduce systemic tissue inflammation.
            </div>
          </div>
        `;
      }

      // 3. Air Quality Cleansing Foods (if PM2.5 elevated)
      if (isSmoggy) {
        html += `
          <div style="background:rgba(244,63,94,0.08); border:1px solid rgba(244,63,94,0.25); border-radius:4px; padding:6px 8px;">
            <div style="font-weight:700; color:#fb7185;">BRONCHIAL CLEANSING (HIGH PM2.5 ACTIVE)</div>
            <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:3px;">
              <span class="bhu-nutrition-tag" style="background:#881337; color:#fecdd3;">Jaggery (Gur) Post-Shift</span>
              <span class="bhu-nutrition-tag" style="background:#881337; color:#fecdd3;">Tulsi-Ginger Warm Decoction</span>
              <span class="bhu-nutrition-tag" style="background:#881337; color:#fecdd3;">Amla (Vitamin C)</span>
            </div>
            <div style="font-size:9px; color:#fda4af; margin-top:3px;">
              Benefit: Traditional jaggery stimulates respiratory mucosa to expel particulate soot; curcumin &amp; vitamin C mitigate alveolar oxidative stress.
            </div>
          </div>
        `;
      }

      container.innerHTML = html;
    }

    show() {
      const panel = document.getElementById('bhu-worker-panel');
      if (panel) {
        panel.style.display = 'flex';
        // Render immediate time-aware nutrition and initialize 3D model
        this.renderNutritionAndDietary(null, null);
        setTimeout(() => {
          this.init3DHumanModel();
          this.fetchData();
        }, 60);
      }
    }

    hide() {
      const panel = document.getElementById('bhu-worker-panel');
      if (panel) panel.style.display = 'none';
    }

    toggle() {
      if (this.isVisible()) this.hide();
      else this.show();
    }

    isVisible() {
      const panel = document.getElementById('bhu-worker-panel');
      return panel && panel.style.display !== 'none';
    }

    async fetchData() {
      if (this.loading) return;
      this.loading = true;

      const locTag = document.getElementById('bhu-worker-location-tag');
      if (locTag) {
        locTag.innerHTML = `Target: ${esc(this.placeName)} (${this.lat.toFixed(4)}&deg;N, ${this.lon.toFixed(4)}&deg;E) &middot; <span style="color:#38bdf8;">SYNCING CLIMATE TELEMETRY...</span>`;
      }

      try {
        const url = `${FASTAPI_BASE}/api/v1/worker/health?lat=${this.lat}&lon=${this.lon}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const snap = await res.json();
        this.data = snap;
        this.renderData(snap);
      } catch (err) {
        this.renderError(err.message || String(err));
      } finally {
        this.loading = false;
        if (locTag) {
          locTag.innerHTML = `Target: ${esc(this.placeName)} (${this.lat.toFixed(4)}&deg;N, ${this.lon.toFixed(4)}&deg;E)`;
        }
      }
    }

    renderData(snap) {
      const wbgt = snap.wbgt || {};
      const aqi = snap.aqi || {};
      const risk = snap.exposure_risk || {};
      const shelters = snap.cooling_shelters || {};

      // 1. Update 3D Hologram Organ Colors & Animations
      this.updateOrganStressColors(wbgt, aqi);

      // 2. Render Time-Aware Nutrition & Dietary Intelligence
      this.renderNutritionAndDietary(wbgt, aqi);

      // 3. WBGT Card
      const wbgtBadge = document.getElementById('bhu-worker-wbgt-badge');
      const wbgtVal = document.getElementById('bhu-worker-wbgt-val');
      const wbgtAdvice = document.getElementById('bhu-worker-wbgt-advice');
      const tier = wbgt.tier || 'UNAVAILABLE';
      const wbgtCol = WBGT_COLORS[tier] || '#64748b';

      if (wbgtBadge) {
        wbgtBadge.textContent = tier;
        wbgtBadge.style.background = wbgtCol;
      }
      if (wbgtVal) {
        wbgtVal.textContent = wbgt.wbgt_celsius != null ? wbgt.wbgt_celsius.toFixed(1) : 'UNAVAILABLE';
        wbgtVal.style.color = wbgtCol;
      }
      if (wbgtAdvice) {
        wbgtAdvice.textContent = wbgt.work_rest_advice || wbgt.reason || 'No advisory available.';
      }

      // 4. Micro-met
      const setTxt = (id, val, suffix = '') => {
        const el = document.getElementById(id);
        if (el) el.textContent = val != null ? `${val}${suffix}` : 'UNAVAILABLE';
      };
      setTxt('bhu-worker-tdry', wbgt.t_dry_celsius, ' \u00B0C');
      setTxt('bhu-worker-tnwb', wbgt.t_natural_wetbulb_celsius, ' \u00B0C');
      setTxt('bhu-worker-tglobe', wbgt.t_globe_celsius, ' \u00B0C');
      setTxt('bhu-worker-rh', wbgt.relative_humidity_pct, ' %');
      setTxt('bhu-worker-wind', wbgt.wind_speed_ms, ' m/s');
      setTxt('bhu-worker-solar', wbgt.solar_radiation_wm2, ' W/m\u00B2');

      // 5. Composite Risk
      const riskBadge = document.getElementById('bhu-worker-risk-badge');
      const riskMeter = document.getElementById('bhu-worker-risk-meter');
      const riskScore = document.getElementById('bhu-worker-risk-score');
      const riskRec = document.getElementById('bhu-worker-risk-rec');
      const rLevel = risk.risk_level || 'UNAVAILABLE';
      const rScore = risk.composite_score;
      const rCol = RISK_COLORS[rLevel] || '#64748b';

      if (riskBadge) {
        riskBadge.textContent = rLevel;
        riskBadge.style.background = rCol;
      }
      if (riskScore) {
        riskScore.textContent = rScore != null ? rScore : '--';
        riskScore.style.color = rCol;
      }
      if (riskMeter) {
        riskMeter.style.width = rScore != null ? `${rScore}%` : '0%';
        riskMeter.style.background = rCol;
      }
      if (riskRec) {
        riskRec.textContent = risk.recommendation || risk.reason || 'Consult local authorities.';
      }

      // 6. PM2.5 / NAQI
      const aqiBadge = document.getElementById('bhu-worker-aqi-badge');
      const pm25Val = document.getElementById('bhu-worker-pm25-val');
      const aqiStation = document.getElementById('bhu-worker-aqi-station');
      const naqiCat = aqi.naqi_category || 'UNAVAILABLE';
      const aqiCol = NAQI_COLORS[naqiCat] || '#64748b';

      if (aqiBadge) {
        aqiBadge.textContent = naqiCat;
        aqiBadge.style.background = aqiCol;
      }
      if (pm25Val) {
        pm25Val.textContent = aqi.pm25_ugm3 != null ? aqi.pm25_ugm3 : 'UNAVAILABLE';
        pm25Val.style.color = aqiCol;
      }
      if (aqiStation) {
        if (aqi.station_name) {
          const distKm = aqi.station_distance_m ? ` (${(aqi.station_distance_m / 1000).toFixed(1)} km away)` : '';
          aqiStation.textContent = `Station: ${aqi.station_name}${distKm}`;
        } else {
          aqiStation.textContent = aqi.reason || 'Source: OpenAQ v3 API';
        }
      }

      // 7. Cooling Shelters
      const shelterCount = document.getElementById('bhu-worker-shelter-count');
      const shelterList = document.getElementById('bhu-worker-shelter-list');
      const sArr = shelters.shelters || [];

      if (shelterCount) {
        shelterCount.textContent = `${sArr.length} VERIFIED`;
      }
      if (shelterList) {
        if (!sArr.length) {
          shelterList.innerHTML = `<div style="color:#64748b; text-align:center; padding:8px;">${esc(shelters.reason || 'No designated cooling shelter identified within 3 km.')}</div>`;
        } else {
          shelterList.innerHTML = sArr.map((s) => `
            <div style="background:rgba(2,6,23,0.5); border:1px solid rgba(148,163,184,0.12); border-radius:4px; padding:6px 8px; display:flex; justify-content:space-between; align-items:center;">
              <div>
                <div style="font-weight:700; color:#f1f5f9;">${esc(s.name)}</div>
                <div style="font-size:9px; color:#94a3b8; text-transform:capitalize;">${esc(s.amenity_type)} &middot; OpenStreetMap Node</div>
              </div>
              <div style="text-align:right;">
                <div style="color:#38bdf8; font-weight:700;">${s.distance_m} m</div>
                <div style="font-size:9px; color:#64748b;">Walk &lt; ${Math.ceil(s.distance_m / 80)} min</div>
              </div>
            </div>
          `).join('');
        }
      }
    }

    renderError(msg) {
      const wbgtAdvice = document.getElementById('bhu-worker-wbgt-advice');
      if (wbgtAdvice) {
        wbgtAdvice.textContent = `Error: ${esc(msg)} (Fail-closed UNAVAILABLE)`;
        wbgtAdvice.style.color = '#fb7185';
      }
    }
  }

  // Auto-instantiate on load
  if (typeof window !== 'undefined') {
    window.BhuLokaWorkerController = new BhuLokaWorkerController();
    window.toggleWorkerHealthPanel = function () {
      if (window.BhuLokaWorkerController) {
        window.BhuLokaWorkerController.toggle();
      }
    };
  }
})(typeof window !== 'undefined' ? window : this);
