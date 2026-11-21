const fs = require('fs');
const path = require('path');

const targetFile = path.resolve(__dirname, '../Assets/vendor/bhu_loka_urban_studio.js');
let rawCode = fs.readFileSync(targetFile, 'utf8');
let code = rawCode.replace(/\r\n/g, '\n');

console.log('Original length (normalized):', code.length);

// 1. Fix createGlassPlate to support isCircle and radius
const oldCreateGlassPlate = `    createGlassPlate(w, d, tintHex, labelText, labelCssHex) {
      const grp = new THREE.Group();
      const geom = new THREE.PlaneGeometry(w * 1.03, d * 1.03);
      geom.rotateX(-Math.PI / 2);
      const mesh = new THREE.Mesh(geom, new THREE.MeshLambertMaterial({ color: tintHex, transparent: true, opacity: 0.09, depthWrite: false, side: THREE.DoubleSide }));
      mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geom), new THREE.LineBasicMaterial({ color: tintHex, transparent: true, opacity: 0.58 })));
      grp.add(mesh);
      if (labelText) {
        const spr = this._createLabelSprite(labelText, labelCssHex || '#38bdf8');
        spr.position.set(w * 0.56 + 3.4, 0.35, -d * 0.32);
        grp.add(spr);
      }
      this.glassPlates.push(grp);
      return grp;
    }`;

const newCreateGlassPlate = `    createGlassPlate(w, d, tintHex, labelText, labelCssHex, isCircle = false, radius = 0) {
      const grp = new THREE.Group();
      let geom;
      if (isCircle && radius > 0) {
        geom = new THREE.CircleGeometry(radius * 1.03, 64);
        geom.rotateX(-Math.PI / 2);
      } else {
        geom = new THREE.PlaneGeometry(w * 1.03, d * 1.03);
        geom.rotateX(-Math.PI / 2);
      }
      const mesh = new THREE.Mesh(geom, new THREE.MeshLambertMaterial({ color: tintHex, transparent: true, opacity: 0.09, depthWrite: false, side: THREE.DoubleSide }));
      if (isCircle && radius > 0) {
        const ringGeom = new THREE.RingGeometry(radius * 1.022, radius * 1.034, 64);
        ringGeom.rotateX(-Math.PI / 2);
        mesh.add(new THREE.Mesh(ringGeom, new THREE.MeshBasicMaterial({ color: tintHex, transparent: true, opacity: 0.65, side: THREE.DoubleSide })));
      } else {
        mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geom), new THREE.LineBasicMaterial({ color: tintHex, transparent: true, opacity: 0.58 })));
      }
      grp.add(mesh);
      if (labelText) {
        const spr = this._createLabelSprite(labelText, labelCssHex || '#38bdf8');
        if (isCircle && radius > 0) {
          spr.position.set(radius * 1.06 + 3.2, 0.35, -radius * 0.32);
        } else {
          spr.position.set(w * 0.56 + 3.4, 0.35, -d * 0.32);
        }
        grp.add(spr);
      }
      this.glassPlates.push(grp);
      return grp;
    }`;

if (code.includes(oldCreateGlassPlate)) {
  code = code.replace(oldCreateGlassPlate, newCreateGlassPlate);
  console.log('✓ Patched createGlassPlate');
} else {
  console.warn('! Could not find oldCreateGlassPlate');
}

// 2. Patch rebuildFromDataset
const startMarker = `    rebuildFromDataset(dataset) {
      if (!this.rootGroup || !dataset) return;
      this.lastDataset = dataset;
      while (this.rootGroup.children.length > 0) this.rootGroup.remove(this.rootGroup.children[0]);
      this.tiers = []; this.glassPlates = []; this.labelSprites = []; this.guidePillars = null;

      const { project, scale, plateW, plateD } = this._makeProjector(dataset.bounds);`;

const endMarker = `      this.tiers = [t0, t1, t2, t3, t4, t5, t6, t7, t8];
      this.tiers.forEach((t) => this.rootGroup.add(t));
      this.updateExplodeSpacing();
    }`;

const sIdx = code.indexOf(startMarker);
const eIdx = code.indexOf(endMarker, sIdx);

if (sIdx !== -1 && eIdx !== -1) {
  const newRebuildFromDataset = `    rebuildFromDataset(dataset) {
      if (!this.rootGroup || !dataset) return;
      this.lastDataset = dataset;
      while (this.rootGroup.children.length > 0) this.rootGroup.remove(this.rootGroup.children[0]);
      this.tiers = []; this.glassPlates = []; this.labelSprites = []; this.guidePillars = null;

      const { project, scale, plateW, plateD } = this._makeProjector(dataset.bounds);
      const isCircle = Boolean(dataset.isCircle || (dataset.aoiGeoJson && dataset.aoiGeoJson.properties && (dataset.aoiGeoJson.properties.shape === 'circle' || dataset.aoiGeoJson.properties.isCircle)));
      const radius3D = isCircle ? (dataset.circleRadiusM ? dataset.circleRadiusM * scale : Math.min(plateW, plateD) / 2) : 0;
      const dem = dataset.dem, b = dataset.buckets;
      const elevToY = (mVal) => (!dem || dem.reliefM < 0.2) ? 0 : ((mVal - dem.minM) / dem.reliefM) * 2.6 * this.verticalExag;

      // L01: TERRAIN DEM + SATELLITE DRAPE (Circular disc or rectangular plane)
      const t0 = new THREE.Group();
      let tGeom;
      if (isCircle && radius3D > 0) {
        tGeom = new THREE.CircleGeometry(radius3D, 64);
        tGeom.rotateX(-Math.PI / 2);
        const pos = tGeom.attributes.position, cols = [];
        const cLow = new THREE.Color(0x143827), cMid = new THREE.Color(0x2f5e42), cHigh = new THREE.Color(0x9e7e4f);
        for (let i = 0; i < pos.count; i++) {
          const x = pos.getX(i), z = pos.getZ(i);
          const u = (x + radius3D) / Math.max(0.01, 2 * radius3D);
          const v = (z + radius3D) / Math.max(0.01, 2 * radius3D);
          const elev = dem ? sampleDemBilinear(dem, u, v) : 0;
          pos.setY(i, elevToY(elev));
          const norm = dem && dem.reliefM > 0.2 ? (elev - dem.minM) / dem.reliefM : 0.35;
          const c = norm < 0.5 ? cLow.clone().lerp(cMid, norm * 2) : cMid.clone().lerp(cHigh, (norm - 0.5) * 2);
          cols.push(c.r, c.g, c.b);
        }
        tGeom.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
      } else {
        tGeom = new THREE.PlaneGeometry(plateW, plateD, 36, 36);
        tGeom.rotateX(-Math.PI / 2);
        const pos = tGeom.attributes.position, cols = [];
        const cLow = new THREE.Color(0x143827), cMid = new THREE.Color(0x2f5e42), cHigh = new THREE.Color(0x9e7e4f);
        for (let i = 0; i < pos.count; i++) {
          const u = (pos.getX(i) + plateW / 2) / Math.max(0.01, plateW);
          const v = (pos.getZ(i) + plateD / 2) / Math.max(0.01, plateD);
          const elev = dem ? sampleDemBilinear(dem, u, v) : 0;
          pos.setY(i, elevToY(elev));
          const norm = dem && dem.reliefM > 0.2 ? (elev - dem.minM) / dem.reliefM : 0.35;
          const c = norm < 0.5 ? cLow.clone().lerp(cMid, norm * 2) : cMid.clone().lerp(cHigh, (norm - 0.5) * 2);
          cols.push(c.r, c.g, c.b);
        }
        tGeom.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
      }
      tGeom.computeVertexNormals();
      const tMesh = new THREE.Mesh(tGeom, new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide }));
      tMesh.receiveShadow = true;
      this.terrainMesh = tMesh;
      t0.add(tMesh);

      // Plinth geometry (Cylinder for circular disc, Box for rectangular plate)
      const plinthGeom = (isCircle && radius3D > 0)
        ? new THREE.CylinderGeometry(radius3D * 1.02, radius3D * 1.02, 0.5, 64)
        : new THREE.BoxGeometry(plateW * 1.02, 0.5, plateD * 1.02);
      const plinth = new THREE.Mesh(plinthGeom, new THREE.MeshLambertMaterial({ color: 0x0f172a }));
      plinth.position.y = -0.35;
      t0.add(plinth);

      const lbl0 = this._createLabelSprite('L01 TERRAIN DEM', '#3f6e4d');
      if (isCircle && radius3D > 0) {
        lbl0.position.set(radius3D * 1.06 + 3.2, 0.4, -radius3D * 0.32);
      } else {
        lbl0.position.set(plateW * 0.56 + 3.4, 0.4, -plateD * 0.32);
      }
      t0.add(lbl0);

      if (this.drapeSatellite) {
        buildSatelliteTextureForBounds(dataset.bounds).then((tex) => {
          if (tex && this.terrainMesh === tMesh) {
            tMesh.material = new THREE.MeshLambertMaterial({ map: tex, side: THREE.DoubleSide });
            tMesh.material.needsUpdate = true;
          }
        });
      }

      // L02: CONTOURS
      const t1 = new THREE.Group();
      t1.add(this.createGlassPlate(plateW, plateD, 0xc29b61, 'L02 CONTOURS', '#c29b61', isCircle, radius3D));
      if (dem && dem.contoursRasterUrl) {
        const cGeom = (isCircle && radius3D > 0)
          ? new THREE.CircleGeometry(radius3D, 64).rotateX(-Math.PI / 2)
          : new THREE.PlaneGeometry(plateW, plateD).rotateX(-Math.PI / 2);
        const cPlane = new THREE.Mesh(
          cGeom,
          new THREE.MeshBasicMaterial({ map: new THREE.TextureLoader().load(dem.contoursRasterUrl), transparent: true, depthWrite: false, side: THREE.DoubleSide })
        );
        cPlane.position.y = 0.08; t1.add(cPlane);
      }

      // L03: FLOOD / SAR
      const t2 = new THREE.Group();
      t2.add(this.createGlassPlate(plateW, plateD, 0x4f46e5, 'L03 FLOOD / SAR', '#818cf8', isCircle, radius3D));
      if (dem && dem.floodRasterUrl) {
        const fGeom = (isCircle && radius3D > 0)
          ? new THREE.CircleGeometry(radius3D, 64).rotateX(-Math.PI / 2)
          : new THREE.PlaneGeometry(plateW, plateD).rotateX(-Math.PI / 2);
        const fPlane = new THREE.Mesh(
          fGeom,
          new THREE.MeshBasicMaterial({ map: new THREE.TextureLoader().load(dem.floodRasterUrl), transparent: true, opacity: 0.9, depthWrite: false, side: THREE.DoubleSide })
        );
        fPlane.position.y = 0.08; t2.add(fPlane);
      }

      // L04: LAND USE
      const t3 = new THREE.Group();
      t3.add(this.createGlassPlate(plateW, plateD, 0xd97706, 'L04 LAND USE', '#fbbf24', isCircle, radius3D));
      const luCol = { residential: 0xd97706, commercial: 0xe11d48, retail: 0xe11d48, industrial: 0x7c3aed, institutional: 0x0284c7, farmland: 0x65a30d };
      b.landuse.slice(0, 200).forEach((f) => {
        if (f.geometry.type !== 'Polygon') return;
        const ring = f.geometry.coordinates[0];
        if (!ring || ring.length < 3) return;
        if (isCircle && radius3D > 0) {
          const [cx, cz] = project(ring[0][0], ring[0][1]);
          if (Math.hypot(cx, cz) > radius3D) return;
        }
        const shape = new THREE.Shape();
        ring.forEach(([lon, lat], i) => { const [x, z] = project(lon, lat); if (i === 0) shape.moveTo(x, -z); else shape.lineTo(x, -z); });
        const g = new THREE.ShapeGeometry(shape); g.rotateX(-Math.PI / 2);
        const m = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ color: luCol[f.properties.landuse] || 0xb45309, transparent: true, opacity: 0.62, depthWrite: false, side: THREE.DoubleSide }));
        m.position.y = 0.08; t3.add(m);
      });

      // L05: WATER
      const t4 = new THREE.Group();
      t4.add(this.createGlassPlate(plateW, plateD, 0x0284c7, 'L05 WATER', '#38bdf8', isCircle, radius3D));
      const wPolyMat = new THREE.MeshLambertMaterial({ color: 0x0284c7, transparent: true, opacity: 0.82, depthWrite: false, side: THREE.DoubleSide });
      const wLineMat = new THREE.LineBasicMaterial({ color: 0x38bdf8 });
      b.water.slice(0, 240).forEach((f) => {
        if (f.geometry.type === 'Polygon') {
          const ring = f.geometry.coordinates[0];
          if (!ring || ring.length < 3) return;
          if (isCircle && radius3D > 0) {
            const [cx, cz] = project(ring[0][0], ring[0][1]);
            if (Math.hypot(cx, cz) > radius3D) return;
          }
          const shape = new THREE.Shape();
          ring.forEach(([lon, lat], i) => { const [x, z] = project(lon, lat); if (i === 0) shape.moveTo(x, -z); else shape.lineTo(x, -z); });
          const g = new THREE.ShapeGeometry(shape); g.rotateX(-Math.PI / 2);
          const m = new THREE.Mesh(g, wPolyMat); m.position.y = 0.09; t4.add(m);
        } else if (f.geometry.type === 'LineString') {
          const pts = f.geometry.coordinates.map(([lon, lat]) => { const [x, z] = project(lon, lat); return new THREE.Vector3(x, 0.1, z); });
          if (pts.length >= 2) {
            if (isCircle && radius3D > 0 && Math.hypot(pts[0].x, pts[0].z) > radius3D) return;
            t4.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), wLineMat));
          }
        }
      });

      // L06: GREENERY
      const t5 = new THREE.Group();
      t5.add(this.createGlassPlate(plateW, plateD, 0x059669, 'L06 GREENERY', '#34d399', isCircle, radius3D));
      const parkMat = new THREE.MeshLambertMaterial({ color: 0x059669, transparent: true, opacity: 0.75, depthWrite: false, side: THREE.DoubleSide });
      const canopyMat = new THREE.MeshLambertMaterial({ color: 0x10b981 });
      const coneGeom = new THREE.ConeGeometry(0.26, 0.8, 6);
      b.greenery.slice(0, 320).forEach((f) => {
        if (f.geometry.type === 'Polygon') {
          const ring = f.geometry.coordinates[0];
          if (!ring || ring.length < 3) return;
          if (isCircle && radius3D > 0) {
            const [cx, cz] = project(ring[0][0], ring[0][1]);
            if (Math.hypot(cx, cz) > radius3D) return;
          }
          const shape = new THREE.Shape();
          ring.forEach(([lon, lat], i) => { const [x, z] = project(lon, lat); if (i === 0) shape.moveTo(x, -z); else shape.lineTo(x, -z); });
          const g = new THREE.ShapeGeometry(shape); g.rotateX(-Math.PI / 2);
          const m = new THREE.Mesh(g, parkMat); m.position.y = 0.08; t5.add(m);
        } else if (f.geometry.type === 'Point') {
          const [x, z] = project(f.geometry.coordinates[0], f.geometry.coordinates[1]);
          if (isCircle && radius3D > 0 && Math.hypot(x, z) > radius3D) return;
          const c = new THREE.Mesh(coneGeom, canopyMat); c.position.set(x, 0.45, z); t5.add(c);
        }
      });

      // L07: ROADS
      const t6 = new THREE.Group();
      t6.add(this.createGlassPlate(plateW, plateD, 0x94a3b8, 'L07 ROADS', '#e2e8f0', isCircle, radius3D));
      const roadLineMats = {
        arterial: new THREE.LineBasicMaterial({ color: 0xf8fafc }),
        collector: new THREE.LineBasicMaterial({ color: 0x38bdf8 }),
        local: new THREE.LineBasicMaterial({ color: 0x64748b })
      };
      const ribbonArt = new THREE.MeshLambertMaterial({ color: 0xf8fafc, side: THREE.DoubleSide });
      const ribbonCol = new THREE.MeshLambertMaterial({ color: 0x38bdf8, side: THREE.DoubleSide });
      b.roads.slice(0, 700).forEach((f) => {
        const coords = f.geometry.coordinates;
        if (!coords || coords.length < 2) return;
        const rc = f.properties._roadClass || 'local';
        const pts = coords.map(([lon, lat]) => { const [x, z] = project(lon, lat); return new THREE.Vector3(x, rc === 'arterial' ? 0.14 : 0.09, z); });
        if (isCircle && radius3D > 0) {
          const filteredPts = pts.filter(p => Math.hypot(p.x, p.z) <= radius3D * 1.01);
          if (filteredPts.length < 2) return;
          t6.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(filteredPts), roadLineMats[rc] || roadLineMats.local));
        } else {
          t6.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), roadLineMats[rc] || roadLineMats.local));
        }
        if (rc === 'arterial' || rc === 'collector') {
          const rw = rc === 'arterial' ? 0.28 : 0.15, rm = rc === 'arterial' ? ribbonArt : ribbonCol;
          for (let i = 0; i < pts.length - 1; i++) {
            if (isCircle && radius3D > 0 && (Math.hypot(pts[i].x, pts[i].z) > radius3D || Math.hypot(pts[i + 1].x, pts[i + 1].z) > radius3D)) continue;
            const segLen = pts[i].distanceTo(pts[i + 1]);
            if (segLen < 0.06) continue;
            const strip = new THREE.Mesh(new THREE.PlaneGeometry(segLen, rw).rotateX(-Math.PI / 2), rm);
            strip.position.set((pts[i].x + pts[i + 1].x) / 2, 0.11, (pts[i].z + pts[i + 1].z) / 2);
            strip.rotation.y = -Math.atan2(pts[i + 1].z - pts[i].z, pts[i + 1].x - pts[i].x);
            t6.add(strip);
          }
        }
      });

      // L08: BUILDINGS (REAL EXTRUDED FOOTPRINTS WITH CIRCULAR DISC CLIPPING)
      const t7 = new THREE.Group();
      t7.add(this.createGlassPlate(plateW, plateD, 0xf8fafc, 'L08 BUILDINGS', '#f8fafc', isCircle, radius3D));
      const bldgObsMat = new THREE.MeshLambertMaterial({ color: 0xf8fafc });
      const bldgEstMat = new THREE.MeshLambertMaterial({ color: 0x94a3b8 });
      const bldgMsftMat = new THREE.MeshLambertMaterial({ color: 0x38bdf8 });
      const bldgVisMat = new THREE.MeshLambertMaterial({ color: 0xfbbf24 });
      const edgeMat = new THREE.LineBasicMaterial({ color: 0x475569, transparent: true, opacity: 0.45 });
      const bldgRelMat = new THREE.MeshLambertMaterial({ color: 0x38bdf8 });
      b.buildings.slice(0, 3500).forEach((f) => {
        const polyCoords = f.geometry.type === 'MultiPolygon' ? f.geometry.coordinates : [f.geometry.coordinates];
        polyCoords.forEach((coords) => {
          const ring = coords[0];
          if (!ring || ring.length < 4) return;
          if (isCircle && radius3D > 0) {
            const [bx, bz] = project(ring[0][0], ring[0][1]);
            if (Math.hypot(bx, bz) > radius3D) return;
          }
          const shape = new THREE.Shape();
          ring.forEach(([lon, lat], i) => { const [x, z] = project(lon, lat); if (i === 0) shape.moveTo(x, -z); else shape.lineTo(x, -z); });
          for (let h = 1; h < coords.length; h++) {
            const hole = coords[h];
            if (hole && hole.length >= 4) {
              const hPath = new THREE.Path();
              hole.forEach(([lon, lat], i) => { const [x, z] = project(lon, lat); if (i === 0) hPath.moveTo(x, -z); else hPath.lineTo(x, -z); });
              shape.holes.push(hPath);
            }
          }
          const extrudeH = Math.max(0.24, (f.properties._height_m || 7.5) * scale * 2.4 * this.heightScale);
          try {
            const geom = new THREE.ExtrudeGeometry(shape, { depth: extrudeH, bevelEnabled: false });
            geom.rotateX(-Math.PI / 2);
            let mat = bldgEstMat;
            if (f.properties._vision_ml) mat = bldgVisMat;
            else if (f.properties._height_observed) mat = bldgObsMat;
            const src = f.properties.source;
            if (src === 'microsoft_ml') mat = bldgMsftMat;
            else if (src === 'ml' || f.properties._vision_ml) mat = bldgVisMat;
            else if (src === 'open_buildings' || f.properties.building_id) mat = bldgEstMat;
            else if (src === 'osm' || f.properties._height_observed) mat = bldgObsMat;
            else if (f.properties.provenance === 'OBSERVED_OSM_RELATION') mat = bldgRelMat;
            const mesh = new THREE.Mesh(geom, mat);
            mesh.position.y = 0.08; mesh.castShadow = true; mesh.receiveShadow = true;
            mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geom, 35), edgeMat));
            t7.add(mesh);
          } catch (_) { }
        });
      });

      // L09: INFRASTRUCTURE
      const t8 = new THREE.Group();
      t8.add(this.createGlassPlate(plateW, plateD, 0x38bdf8, 'L09 INFRASTRUCTURE', '#38bdf8', isCircle, radius3D));
      const pinMat = new THREE.MeshLambertMaterial({ color: 0x38bdf8 });
      const pinGeom = new THREE.CylinderGeometry(0.18, 0.06, 1.2, 8);
      b.infrastructure.slice(0, 120).forEach((f) => {
        let lon, lat;
        if (f.geometry.type === 'Point') [lon, lat] = f.geometry.coordinates;
        else if (f.geometry.type === 'Polygon' && f.geometry.coordinates[0]?.[0]) [lon, lat] = f.geometry.coordinates[0][0];
        else return;
        const [x, z] = project(lon, lat);
        if (isCircle && radius3D > 0 && Math.hypot(x, z) > radius3D) return;
        const pin = new THREE.Mesh(pinGeom, pinMat); pin.position.set(x, 0.7, z); t8.add(pin);
      });

      // 4 Vertical Alignment Guide Pillars (Circular angles or corner columns)
      const guideGroup = new THREE.Group();
      const gMat = new THREE.LineBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.25 });
      if (isCircle && radius3D > 0) {
        const angles = [0, Math.PI / 2, Math.PI, 3 * Math.PI / 2];
        angles.forEach((a) => {
          const cx = radius3D * 1.025 * Math.cos(a);
          const cz = radius3D * 1.025 * Math.sin(a);
          guideGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(cx, 0, cz), new THREE.Vector3(cx, 1, cz)]), gMat));
        });
      } else {
        const hw = plateW * 0.515, hd = plateD * 0.515;
        [[-hw, -hd], [hw, -hd], [hw, hd], [-hw, hd]].forEach(([cx, cz]) => {
          guideGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(cx, 0, cz), new THREE.Vector3(cx, 1, cz)]), gMat));
        });
      }
      this.guidePillars = guideGroup;
      this.rootGroup.add(guideGroup);

      this.tiers = [t0, t1, t2, t3, t4, t5, t6, t7, t8];
      this.tiers.forEach((t) => this.rootGroup.add(t));
      this.updateExplodeSpacing();
    }`;

  code = code.slice(0, sIdx) + newRebuildFromDataset + code.slice(eIdx + endMarker.length);
  console.log('✓ Patched rebuildFromDataset for Circular 3D Twin & Clipping');
} else {
  console.error('! Failed to match rebuildFromDataset block', { sIdx, eIdx });
}

// 3. Add getCropBounds and setCropCircleAroundCenter to UrbanLeafletEngine
const oldSetCropAroundCenter = `    setCropAroundCenter(lat, lon, sizeMeters) {
      if (!this.map) return null;
      this.stopDraw();
      const dLat = metersToDegLat(sizeMeters / 2), dLon = metersToDegLon(sizeMeters / 2, lat);
      const bounds = { south: lat - dLat, north: lat + dLat, west: lon - dLon, east: lon + dLon };
      this.setAoiBounds(bounds, true);
      return bounds;
    }`;

const newSetCropMethods = `    getCropBounds() {
      return this.aoiBounds || (this.map ? { south: this.map.getBounds().getSouth(), west: this.map.getBounds().getWest(), north: this.map.getBounds().getNorth(), east: this.map.getBounds().getEast() } : null);
    }

    setCropAroundCenter(lat, lon, sizeMeters) {
      if (!this.map) return null;
      this.stopDraw();
      this.activeShape = 'rect';
      const dLat = metersToDegLat(sizeMeters / 2), dLon = metersToDegLon(sizeMeters / 2, lat);
      const bounds = { south: lat - dLat, north: lat + dLat, west: lon - dLon, east: lon + dLon };
      this.setAoiBounds(bounds, true);
      return bounds;
    }

    setCropCircleAroundCenter(lat, lon, radiusMeters) {
      if (!this.map) return null;
      this.stopDraw();
      this.activeShape = 'circle';
      const dLat = metersToDegLat(radiusMeters);
      const dLon = metersToDegLon(radiusMeters, lat);
      const bounds = { south: lat - dLat, north: lat + dLat, west: lon - dLon, east: lon + dLon };
      this.aoiBounds = bounds;

      if (this.aoiLayer) { this.map.removeLayer(this.aoiLayer); this.aoiLayer = null; }

      this.aoiLayer = L.circle([lat, lon], {
        radius: radiusMeters,
        color: '#38bdf8',
        weight: 2.2,
        opacity: 0.95,
        fillColor: '#0284c7',
        fillOpacity: 0.05,
        dashArray: '6 4'
      }).addTo(this.map);

      const coords = [];
      const steps = 64;
      const mLat = 111132.92;
      const mLon = 111412.84 * Math.cos(lat * Math.PI / 180);
      for (let i = 0; i < steps; i++) {
        const angle = (i / steps) * 2 * Math.PI;
        const dY = (radiusMeters * Math.cos(angle)) / mLat;
        const dX = (radiusMeters * Math.sin(angle)) / mLon;
        coords.push([lon + dX, lat + dY]);
      }
      coords.push(coords[0]);

      this.aoiGeoJson = {
        type: 'Feature',
        properties: { shape: 'circle', isCircle: true, radius_m: Math.round(radiusMeters), radiusM: Math.round(radiusMeters), center: [lat, lon] },
        geometry: { type: 'Polygon', coordinates: [coords] }
      };

      this._bindAoiGeomanEvents(this.aoiLayer);
      this._updatePhotoshopCropper(bounds, this.aoiGeoJson);
      if (this.aoiLayer && typeof this.aoiLayer.bringToFront === 'function') this.aoiLayer.bringToFront();
      this._renderAoiSummary(bounds, this.aoiGeoJson);
      return bounds;
    }`;

if (code.includes(oldSetCropAroundCenter)) {
  code = code.replace(oldSetCropAroundCenter, newSetCropMethods);
  console.log('✓ Added getCropBounds & setCropCircleAroundCenter');
} else {
  console.warn('! Could not find oldSetCropAroundCenter');
}

// 4. Update _emitAoiFromLayer for activeShape and bringToFront
const oldEmitAoi = `    _emitAoiFromLayer(layer) {
      if (!layer || !layer.getBounds) return;
      const b = layer.getBounds();
      const bounds = { south: b.getSouth(), west: b.getWest(), north: b.getNorth(), east: b.getEast() };
      let gj = null;
      if (typeof layer.getRadius === 'function') {
        // Circle AOI: convert to 64-vertex smooth polygon ring for extraction & clipping
        const center = layer.getLatLng();
        const rM = layer.getRadius();
        const coords = [];
        const steps = 64;
        const mLat = 111132.92;
        const mLon = 111412.84 * Math.cos(center.lat * Math.PI / 180);
        for (let i = 0; i < steps; i++) {
          const angle = (i / steps) * 2 * Math.PI;
          const dY = (rM * Math.cos(angle)) / mLat;
          const dX = (rM * Math.sin(angle)) / mLon;
          coords.push([center.lng + dX, center.lat + dY]);
        }
        coords.push(coords[0]);
        gj = {
          type: 'Feature',
          properties: { shape: 'circle', radius_m: Math.round(rM), center: [center.lat, center.lng] },
          geometry: { type: 'Polygon', coordinates: [coords] }
        };
      } else if (typeof layer.toGeoJSON === 'function') {
        gj = layer.toGeoJSON();
      }
      this.aoiBounds = bounds;
      this.aoiGeoJson = gj;
      this._updatePhotoshopCropper(bounds, gj);
      this._renderAoiSummary(bounds, gj);
      if (this.onAoiReady) this.onAoiReady(bounds, gj);
    }`;

const newEmitAoi = `    _emitAoiFromLayer(layer) {
      if (!layer || !layer.getBounds) return;
      const b = layer.getBounds();
      const bounds = { south: b.getSouth(), west: b.getWest(), north: b.getNorth(), east: b.getEast() };
      let gj = null;
      if (typeof layer.getRadius === 'function') {
        // Circle AOI: convert to 64-vertex smooth polygon ring for extraction & clipping
        const center = layer.getLatLng();
        const rM = layer.getRadius();
        const coords = [];
        const steps = 64;
        const mLat = 111132.92;
        const mLon = 111412.84 * Math.cos(center.lat * Math.PI / 180);
        for (let i = 0; i < steps; i++) {
          const angle = (i / steps) * 2 * Math.PI;
          const dY = (rM * Math.cos(angle)) / mLat;
          const dX = (rM * Math.sin(angle)) / mLon;
          coords.push([center.lng + dX, center.lat + dY]);
        }
        coords.push(coords[0]);
        gj = {
          type: 'Feature',
          properties: { shape: 'circle', isCircle: true, radius_m: Math.round(rM), radiusM: Math.round(rM), center: [center.lat, center.lng] },
          geometry: { type: 'Polygon', coordinates: [coords] }
        };
        this.activeShape = 'circle';
      } else if (typeof layer.toGeoJSON === 'function') {
        gj = layer.toGeoJSON();
        this.activeShape = 'rect';
      }
      this.aoiBounds = bounds;
      this.aoiGeoJson = gj;
      this._updatePhotoshopCropper(bounds, gj);
      if (this.aoiLayer && typeof this.aoiLayer.bringToFront === 'function') this.aoiLayer.bringToFront();
      this._renderAoiSummary(bounds, gj);
      if (this.onAoiReady) this.onAoiReady(bounds, gj);
    }`;

if (code.includes(oldEmitAoi)) {
  code = code.replace(oldEmitAoi, newEmitAoi);
  console.log('✓ Patched _emitAoiFromLayer');
} else {
  console.warn('! Could not find oldEmitAoi');
}

// 5. Update _updatePhotoshopCropper for Circle vs Rect and bringToFront
const oldCropperStart = `    _updatePhotoshopCropper(bounds, aoiGeoJson = null) {
      if (!this.map || !bounds) return;
      const { south, west, north, east } = bounds;

      // 1. Dark Vignette Scrim (Photoshop outer dark mask)
      const worldOuter = [
        [-89.99, -179.99],
        [-89.99, 179.99],
        [89.99, 179.99],
        [89.99, -179.99],
        [-89.99, -179.99]
      ];
      let aoiHole = [];
      if (aoiGeoJson && aoiGeoJson.geometry && aoiGeoJson.geometry.type === 'Polygon' && Array.isArray(aoiGeoJson.geometry.coordinates[0])) {
        aoiHole = aoiGeoJson.geometry.coordinates[0].map(([lon, lat]) => [lat, lon]);
      } else {
        aoiHole = [
          [south, west],
          [north, west],
          [north, east],
          [south, east],
          [south, west]
        ];
      }

      if (this.scrimLayer && this.map.hasLayer(this.scrimLayer)) {
        this.map.removeLayer(this.scrimLayer);
      }
      this.scrimLayer = L.polygon([worldOuter, aoiHole], {
        stroke: false,
        fillColor: '#050811',
        fillOpacity: 0.62,
        interactive: false
      }).addTo(this.map);`;

const newCropperStart = `    _updatePhotoshopCropper(bounds, aoiGeoJson = null) {
      if (!this.map || !bounds) return;
      aoiGeoJson = aoiGeoJson || this.aoiGeoJson;
      const { south, west, north, east } = bounds;
      const isCircle = Boolean(aoiGeoJson && aoiGeoJson.properties && (aoiGeoJson.properties.shape === 'circle' || aoiGeoJson.properties.isCircle));

      // 1. Dark Vignette Scrim (Photoshop outer dark mask)
      const worldOuter = [
        [-89.99, -179.99],
        [-89.99, 179.99],
        [89.99, 179.99],
        [89.99, -179.99],
        [-89.99, -179.99]
      ];
      let aoiHole = [];
      if (aoiGeoJson && aoiGeoJson.geometry && aoiGeoJson.geometry.type === 'Polygon' && Array.isArray(aoiGeoJson.geometry.coordinates[0])) {
        aoiHole = aoiGeoJson.geometry.coordinates[0].map(([lon, lat]) => [lat, lon]);
      } else {
        aoiHole = [
          [south, west],
          [north, west],
          [north, east],
          [south, east],
          [south, west]
        ];
      }

      if (this.scrimLayer && this.map.hasLayer(this.scrimLayer)) {
        this.map.removeLayer(this.scrimLayer);
      }
      this.scrimLayer = L.polygon([worldOuter, aoiHole], {
        stroke: false,
        fillColor: '#050811',
        fillOpacity: 0.62,
        interactive: false
      }).addTo(this.map);
      if (this.aoiLayer && typeof this.aoiLayer.bringToFront === 'function') {
        this.aoiLayer.bringToFront();
      }`;

if (code.includes(oldCropperStart)) {
  code = code.replace(oldCropperStart, newCropperStart);
  console.log('✓ Patched cropper scrim & bringToFront');
}

// 6. Update Grid and HUD in _updatePhotoshopCropper
const oldGridSection = `      // 2. Rule of Thirds Grid & Corner L-Brackets Layer Group
      if (this.cropGridLayer && this.map.hasLayer(this.cropGridLayer)) {
        this.map.removeLayer(this.cropGridLayer);
      }
      const gridGroup = L.layerGroup();
      const dLat = (north - south);
      const dLon = (east - west);

      // Rule of thirds lines (Photoshop crop guide)
      const lat1 = south + dLat / 3;
      const lat2 = south + (2 * dLat) / 3;
      const lon1 = west + dLon / 3;
      const lon2 = west + (2 * dLon) / 3;

      const guideOpt = { color: 'rgba(255, 255, 255, 0.22)', weight: 1, dashArray: '4, 4', interactive: false };
      gridGroup.addLayer(L.polyline([[lat1, west], [lat1, east]], guideOpt));
      gridGroup.addLayer(L.polyline([[lat2, west], [lat2, east]], guideOpt));
      gridGroup.addLayer(L.polyline([[south, lon1], [north, lon1]], guideOpt));
      gridGroup.addLayer(L.polyline([[south, lon2], [north, lon2]], guideOpt));

      // Corner L-Bracket SVG markers (Photoshop handles)
      const lLenLat = dLat * 0.08;
      const lLenLon = dLon * 0.08;
      const lOpt = { color: '#38bdf8', weight: 3.5, lineCap: 'square', interactive: false };

      // Top-Left L
      gridGroup.addLayer(L.polyline([[north, west + lLenLon], [north, west], [north - lLenLat, west]], lOpt));
      // Top-Right L
      gridGroup.addLayer(L.polyline([[north, east - lLenLon], [north, east], [north - lLenLat, east]], lOpt));
      // Bottom-Left L
      gridGroup.addLayer(L.polyline([[south, west + lLenLon], [south, west], [south + lLenLat, west]], lOpt));
      // Bottom-Right L
      gridGroup.addLayer(L.polyline([[south, east - lLenLon], [south, east], [south + lLenLat, east]], lOpt));

      // Center Edge Ticks
      const midLat = (south + north) / 2;
      const midLon = (west + east) / 2;
      const tickOpt = { color: '#f8fafc', weight: 3, lineCap: 'round', interactive: false };
      gridGroup.addLayer(L.polyline([[north, midLon - lLenLon * 0.3], [north, midLon + lLenLon * 0.3]], tickOpt));
      gridGroup.addLayer(L.polyline([[south, midLon - lLenLon * 0.3], [south, midLon + lLenLon * 0.3]], tickOpt));
      gridGroup.addLayer(L.polyline([[midLat - lLenLat * 0.3, west], [midLat + lLenLat * 0.3, west]], tickOpt));
      gridGroup.addLayer(L.polyline([[midLat - lLenLat * 0.3, east], [midLat + lLenLat * 0.3, east]], tickOpt));

      gridGroup.addTo(this.map);
      this.cropGridLayer = gridGroup;

      // 3. Floating HUD Dimension Badge pinned to top center of crop box
      const areaM2 = calcBoundsAreaM2(bounds);
      const ha = (areaM2 / 10000).toFixed(1);
      const acres = (areaM2 * 0.000247105).toFixed(1);
      const kmWidth = (Math.abs(east - west) * 111.32 * Math.cos(((south + north) / 2) * (Math.PI / 180))).toFixed(2);
      const kmHeight = (Math.abs(north - south) * 110.57).toFixed(2);

      const hudHtml = \`
        <div style="transform:translate(-50%, -100%); margin-top:-10px; display:inline-flex; align-items:center; gap:8px; padding:5px 12px; background:rgba(10,15,26,0.92); border:1px solid rgba(56,189,248,0.55); border-radius:9999px; box-shadow:0 8px 24px rgba(0,0,0,0.7), 0 0 12px rgba(56,189,248,0.25); backdrop-filter:blur(12px); font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:600; color:#f8fafc; white-space:nowrap; pointer-events:none; user-select:none;">
          <span style="color:#38bdf8; display:inline-flex; align-items:center; gap:4px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 2v14a2 2 0 0 0 2 2h14"/><path d="M18 22V8a2 2 0 0 0-2-2H2"/></svg>
            <span>\` + kmWidth + \` km &times; \` + kmHeight + \` km</span>
          </span>
          <span style="color:rgba(255,255,255,0.3);">&middot;</span>
          <span style="color:#34d399;">\` + ha + \` ha</span>
          <span style="color:#94a3b8; font-size:10px;">(\` + acres + \` ac)</span>
        </div>
      \`;`;

const newGridSection = `      // 2. Rule of Thirds Grid & Corner L-Brackets Layer Group
      if (this.cropGridLayer && this.map.hasLayer(this.cropGridLayer)) {
        this.map.removeLayer(this.cropGridLayer);
      }
      const gridGroup = L.layerGroup();
      const dLat = (north - south);
      const dLon = (east - west);
      const midLat = (south + north) / 2;
      const midLon = (west + east) / 2;

      if (isCircle) {
        // Circular subtle guide ring and 4 cardinal ticks
        const rM = aoiGeoJson?.properties?.radiusM || aoiGeoJson?.properties?.radius_m || Math.round(dLat * 111132.92 / 2);
        gridGroup.addLayer(L.circle([midLat, midLon], {
          radius: rM,
          color: '#38bdf8',
          weight: 1.8,
          dashArray: '6, 6',
          fill: false,
          interactive: false
        }));
        const tickOpt = { color: '#38bdf8', weight: 3, lineCap: 'round', interactive: false };
        const tickLat = dLat * 0.04, tickLon = dLon * 0.04;
        gridGroup.addLayer(L.polyline([[north - tickLat, midLon], [north + tickLat, midLon]], tickOpt));
        gridGroup.addLayer(L.polyline([[south - tickLat, midLon], [south + tickLat, midLon]], tickOpt));
        gridGroup.addLayer(L.polyline([[midLat, west - tickLon], [midLat, west + tickLon]], tickOpt));
        gridGroup.addLayer(L.polyline([[midLat, east - tickLon], [midLat, east + tickLon]], tickOpt));
      } else {
        // Rule of thirds lines (Photoshop crop guide)
        const lat1 = south + dLat / 3;
        const lat2 = south + (2 * dLat) / 3;
        const lon1 = west + dLon / 3;
        const lon2 = west + (2 * dLon) / 3;

        const guideOpt = { color: 'rgba(255, 255, 255, 0.22)', weight: 1, dashArray: '4, 4', interactive: false };
        gridGroup.addLayer(L.polyline([[lat1, west], [lat1, east]], guideOpt));
        gridGroup.addLayer(L.polyline([[lat2, west], [lat2, east]], guideOpt));
        gridGroup.addLayer(L.polyline([[south, lon1], [north, lon1]], guideOpt));
        gridGroup.addLayer(L.polyline([[south, lon2], [north, lon2]], guideOpt));

        // Corner L-Bracket SVG markers (Photoshop handles)
        const lLenLat = dLat * 0.08;
        const lLenLon = dLon * 0.08;
        const lOpt = { color: '#38bdf8', weight: 3.5, lineCap: 'square', interactive: false };

        gridGroup.addLayer(L.polyline([[north, west + lLenLon], [north, west], [north - lLenLat, west]], lOpt));
        gridGroup.addLayer(L.polyline([[north, east - lLenLon], [north, east], [north - lLenLat, east]], lOpt));
        gridGroup.addLayer(L.polyline([[south, west + lLenLon], [south, west], [south + lLenLat, west]], lOpt));
        gridGroup.addLayer(L.polyline([[south, east - lLenLon], [south, east], [south + lLenLat, east]], lOpt));

        // Center Edge Ticks
        const tickOpt = { color: '#f8fafc', weight: 3, lineCap: 'round', interactive: false };
        gridGroup.addLayer(L.polyline([[north, midLon - lLenLon * 0.3], [north, midLon + lLenLon * 0.3]], tickOpt));
        gridGroup.addLayer(L.polyline([[south, midLon - lLenLon * 0.3], [south, midLon + lLenLon * 0.3]], tickOpt));
        gridGroup.addLayer(L.polyline([[midLat - lLenLat * 0.3, west], [midLat + lLenLat * 0.3, west]], tickOpt));
        gridGroup.addLayer(L.polyline([[midLat - lLenLat * 0.3, east], [midLat + lLenLat * 0.3, east]], tickOpt));
      }

      gridGroup.addTo(this.map);
      this.cropGridLayer = gridGroup;

      // 3. Floating HUD Dimension Badge pinned to top center of crop box
      const areaM2 = calcBoundsAreaM2(bounds);
      const ha = (areaM2 / 10000).toFixed(1);
      const acres = (areaM2 * 0.000247105).toFixed(1);
      const kmWidth = (Math.abs(east - west) * 111.32 * Math.cos(((south + north) / 2) * (Math.PI / 180))).toFixed(2);
      const kmHeight = (Math.abs(north - south) * 110.57).toFixed(2);

      let hudHtml;
      if (isCircle) {
        const rM = aoiGeoJson?.properties?.radiusM || aoiGeoJson?.properties?.radius_m || Math.round(dLat * 111132.92 / 2);
        const diamKm = ((rM * 2) / 1000).toFixed(2);
        hudHtml = \`
          <div style="transform:translate(-50%, -100%); margin-top:-10px; display:inline-flex; align-items:center; gap:8px; padding:5px 12px; background:rgba(10,15,26,0.92); border:1px solid rgba(56,189,248,0.55); border-radius:9999px; box-shadow:0 8px 24px rgba(0,0,0,0.7), 0 0 12px rgba(56,189,248,0.25); backdrop-filter:blur(12px); font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:600; color:#f8fafc; white-space:nowrap; pointer-events:none; user-select:none;">
            <span style="color:#38bdf8; display:inline-flex; align-items:center; gap:4px;">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="9"/></svg>
              <span>Ø \` + diamKm + \` km (R \` + rM + \`m)</span>
            </span>
            <span style="color:rgba(255,255,255,0.3);">&middot;</span>
            <span style="color:#34d399;">\` + ha + \` ha</span>
            <span style="color:#94a3b8; font-size:10px;">(\` + acres + \` ac)</span>
          </div>
        \`;
      } else {
        hudHtml = \`
          <div style="transform:translate(-50%, -100%); margin-top:-10px; display:inline-flex; align-items:center; gap:8px; padding:5px 12px; background:rgba(10,15,26,0.92); border:1px solid rgba(56,189,248,0.55); border-radius:9999px; box-shadow:0 8px 24px rgba(0,0,0,0.7), 0 0 12px rgba(56,189,248,0.25); backdrop-filter:blur(12px); font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:600; color:#f8fafc; white-space:nowrap; pointer-events:none; user-select:none;">
            <span style="color:#38bdf8; display:inline-flex; align-items:center; gap:4px;">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 2v14a2 2 0 0 0 2 2h14"/><path d="M18 22V8a2 2 0 0 0-2-2H2"/></svg>
              <span>\` + kmWidth + \` km &times; \` + kmHeight + \` km</span>
            </span>
            <span style="color:rgba(255,255,255,0.3);">&middot;</span>
            <span style="color:#34d399;">\` + ha + \` ha</span>
            <span style="color:#94a3b8; font-size:10px;">(\` + acres + \` ac)</span>
          </div>
        \`;
      }`;

if (code.includes(oldGridSection)) {
  code = code.replace(oldGridSection, newGridSection);
  console.log('✓ Patched crop grid & HUD for circle vs rect');
} else {
  console.warn('! Could not find oldGridSection');
}

// 7. Update setCropSize in UrbanIntelligenceController to respect activeShape
const oldSetCropSize = `    setCropSize(meters) {
      this.activeCropM = Number(meters);
      document.querySelectorAll('.us3-crop-btn').forEach((btn) => btn.classList.toggle('active', Number(btn.dataset.crop) === this.activeCropM));
      const c = this.leaflet && this.leaflet.map ? this.leaflet.map.getCenter() : { lat: this.activeSite.lat, lng: this.activeSite.lon };
      if (this.leaflet) {
        const b = this.leaflet.setCropAroundCenter(c.lat, c.lng, this.activeCropM);
        this.extractForBounds(b, this.activeSite.name);
      }
    }`;

const newSetCropSize = `    setCropSize(meters) {
      this.activeCropM = Number(meters);
      document.querySelectorAll('.us3-crop-btn').forEach((btn) => btn.classList.toggle('active', Number(btn.dataset.crop) === this.activeCropM));
      const c = this.leaflet && this.leaflet.map ? this.leaflet.map.getCenter() : { lat: this.activeSite.lat, lng: this.activeSite.lon };
      if (this.leaflet) {
        let b;
        if (this.leaflet.activeShape === 'circle') {
          b = this.leaflet.setCropCircleAroundCenter(c.lat, c.lng, this.activeCropM / 2);
        } else {
          b = this.leaflet.setCropAroundCenter(c.lat, c.lng, this.activeCropM);
        }
        this.extractForBounds(b, this.activeSite.name);
      }
    }`;

if (code.includes(oldSetCropSize)) {
  code = code.replace(oldSetCropSize, newSetCropSize);
  console.log('✓ Patched setCropSize for circle vs rect');
} else {
  console.warn('! Could not find oldSetCropSize');
}

// 8. Patch switchTab to invoke renderSiteAnalyticsPanel when tab === 'site-ai'
const oldSwitchTabBranch = `      } else if (tab === 'ml' && window.BhuLokaSpatialML) {
        window.BhuLokaSpatialML.renderMlPanel(this.dataset);
      }
    }`;

const newSwitchTabBranch = `      } else if (tab === 'ml' && window.BhuLokaSpatialML) {
        window.BhuLokaSpatialML.renderMlPanel(this.dataset);
      } else if (tab === 'site-ai') {
        this.renderSiteAnalyticsPanel();
      }
    }`;

if (code.includes(oldSwitchTabBranch)) {
  code = code.replace(oldSwitchTabBranch, newSwitchTabBranch);
  console.log('✓ Patched switchTab for site-ai tab execution');
} else {
  console.warn('! Could not find oldSwitchTabBranch');
}

// 9. Update window exports at the bottom
const oldExports = `  window.startUrbanRectDraw = () => { if (ctrl.leaflet) ctrl.leaflet.startRectDraw(); };
  window.startUrbanCircleDraw = () => { if (ctrl.leaflet) ctrl.leaflet.startCircleDraw(); };`;

const newExports = `  window.startUrbanRectDraw = () => {
    if (!ctrl.leaflet) return;
    ctrl.leaflet.activeShape = 'rect';
    const btnC = document.getElementById('urban-draw-circle');
    const btnR = document.getElementById('urban-draw-rect');
    const btnP = document.getElementById('urban-draw-poly');
    if (btnR) btnR.classList.add('active');
    if (btnC) btnC.classList.remove('active');
    if (btnP) btnP.classList.remove('active');
    if (ctrl.leaflet.aoiBounds) {
      const b = ctrl.leaflet.aoiBounds;
      const cLat = (b.south + b.north) / 2, cLon = (b.west + b.east) / 2;
      const sizeM = ctrl.activeCropM || 1000;
      const newB = ctrl.leaflet.setCropAroundCenter(cLat, cLon, sizeM);
      ctrl.extractForBounds(newB, ctrl.activeSite.name);
      ctrl._toast('Set AOI to Rectangle (' + sizeM + 'm)', 'info');
    } else {
      ctrl.leaflet.startRectDraw();
    }
  };

  window.startUrbanCircleDraw = () => {
    if (!ctrl.leaflet) return;
    ctrl.leaflet.activeShape = 'circle';
    const btnC = document.getElementById('urban-draw-circle');
    const btnR = document.getElementById('urban-draw-rect');
    const btnP = document.getElementById('urban-draw-poly');
    if (btnC) btnC.classList.add('active');
    if (btnR) btnR.classList.remove('active');
    if (btnP) btnP.classList.remove('active');
    if (ctrl.leaflet.aoiBounds) {
      const b = ctrl.leaflet.aoiBounds;
      const cLat = (b.south + b.north) / 2, cLon = (b.west + b.east) / 2;
      const radiusM = ctrl.activeCropM ? ctrl.activeCropM / 2 : 500;
      const newB = ctrl.leaflet.setCropCircleAroundCenter(cLat, cLon, radiusM);
      ctrl.extractForBounds(newB, ctrl.activeSite.name);
      ctrl._toast('Set AOI to Circular Buffer (Radius ' + radiusM + 'm)', 'info');
    } else {
      ctrl.leaflet.startCircleDraw();
    }
  };`;

if (code.includes(oldExports)) {
  code = code.replace(oldExports, newExports);
  console.log('✓ Patched startUrbanRectDraw & startUrbanCircleDraw exports');
} else {
  console.warn('! Could not find oldExports');
}

// Convert back to CRLF before writing
fs.writeFileSync(targetFile, code.replace(/\n/g, '\r\n'), 'utf8');
console.log('Saved updated file with CRLF. Final length:', code.length);
