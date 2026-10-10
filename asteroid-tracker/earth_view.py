"""3D Earth view: realistic textured Earth with asteroids linked by distance lines.

Rendered with three.js inside a Streamlit component. Distances are on a log scale
and asteroid sizes are exaggerated so everything fits on one screen.
"""
from __future__ import annotations

import hashlib
import json

import pandas as pd

THREE = "https://cdn.jsdelivr.net/npm/three@0.147.0/build/three.min.js"
ORBIT = "https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/controls/OrbitControls.js"
TEX = "https://cdn.jsdelivr.net/gh/mrdoob/three.js@r147/examples/textures/planets/"


def _angles(obj_id: str) -> tuple[int, int]:
    """Deterministic (illustrative) direction for each asteroid, from its ID."""
    h = hashlib.md5(str(obj_id).encode()).hexdigest()
    return int(h[:8], 16) % 360, (int(h[8:16], 16) % 100) - 50


def build_html(df: pd.DataFrame, height: int = 680) -> str:
    objects = []
    for row in df.itertuples():
        az, el = _angles(row.id)
        objects.append(
            {
                "name": row.name, "date": row.date, "diam": round(row.diameter_avg_m),
                "speed": round(row.velocity_kmh), "ld": round(row.miss_lunar, 1),
                "km": round(row.miss_km / 1e6, 1), "haz": bool(row.hazardous),
                "az": az, "el": el,
            }
        )
    data = json.dumps(objects).replace("</", "<\\/")
    return (
        _TEMPLATE.replace("__DATA__", data)
        .replace("__THREE__", THREE).replace("__ORBIT__", ORBIT)
        .replace("__TEX__", TEX).replace("__H__", str(height))
    )


_TEMPLATE = r"""
<style>
  html, body {margin:0; background:#000; font-family: Inter, Segoe UI, sans-serif;}
  #c {position:relative; width:100%; height:__H__px; overflow:hidden; border-radius:14px;
      background: radial-gradient(ellipse at center, #0a1020 0%, #000 70%);}
  #legend {position:absolute; top:14px; left:16px; color:#cfd6e6; font-size:13px;
      background:rgba(8,12,24,.72); border:1px solid #222c45; border-radius:10px; padding:10px 14px;}
  #legend div {margin:3px 0; display:flex; align-items:center; gap:8px;}
  .dot {width:10px; height:10px; border-radius:50%; display:inline-block;}
  #legend small {color:#7d89a6; display:block; margin-top:6px; max-width:230px; line-height:1.35;}
  #hint {position:absolute; bottom:12px; left:50%; transform:translateX(-50%); color:#7d89a6; font-size:12px;}
  #tip {position:absolute; pointer-events:none; display:none; color:#e6e9f2; font-size:12px; line-height:1.5;
      background:rgba(8,12,24,.92); border:1px solid #333f60; border-radius:8px; padding:8px 10px; white-space:nowrap;}
  #load {position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:#7d89a6;}
</style>
<div id="c">
  <div id="load">Loading Earth...</div>
  <div id="legend">
    <div><span class="dot" style="background:#ff3b3b"></span>Potentially hazardous</div>
    <div><span class="dot" style="background:#2ecc71"></span>Not hazardous</div>
    <small>Distance scale is logarithmic. Asteroid sizes are exaggerated. Directions are illustrative.</small>
  </div>
  <div id="hint">Drag to rotate &middot; Scroll to zoom &middot; Hover an asteroid for details</div>
  <div id="tip"></div>
</div>
<script src="__THREE__"></script>
<script src="__ORBIT__"></script>
<script>
const DATA = __DATA__;
const TEX = "__TEX__";
const R = 1.6;                                   // Earth radius in scene units
const dist = ld => 3.4 + 4.2 * Math.log10(1 + ld);
const RED = 0xff3b3b, GREEN = 0x2ecc71;

const box = document.getElementById('c');
const W = () => box.clientWidth, H = () => box.clientHeight;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, W() / H(), 0.1, 3000);
camera.position.set(0, 7, 22);
const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(W(), H());
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
box.appendChild(renderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.06;
controls.enablePan = false; controls.minDistance = 6; controls.maxDistance = 45;

// ---- Lighting (sun from the left)
const sun = new THREE.DirectionalLight(0xffffff, 1.6);
sun.position.set(-30, 8, 20); scene.add(sun);
scene.add(new THREE.AmbientLight(0x6f86b8, 0.18));

// ---- Starfield
const sp = [];
for (let i = 0; i < 4500; i++) {
  const u = Math.random() * 2 - 1, t = Math.random() * Math.PI * 2, s = Math.sqrt(1 - u * u);
  const r = 800 + Math.random() * 400;
  sp.push(r * s * Math.cos(t), r * u, r * s * Math.sin(t));
}
const sg = new THREE.BufferGeometry();
sg.setAttribute('position', new THREE.Float32BufferAttribute(sp, 3));
scene.add(new THREE.Points(sg, new THREE.PointsMaterial({color: 0xffffff, size: 1.5, sizeAttenuation: false, transparent: true, opacity: 0.85})));

// ---- Textures
const loader = new THREE.TextureLoader();
loader.setCrossOrigin('anonymous');
const tex = (name, cb, fail) => loader.load(TEX + name, t => { t.encoding = THREE.sRGBEncoding; t.anisotropy = 8; cb(t); document.getElementById('load').style.display = 'none'; }, undefined, fail || (() => {}));

// ---- Earth
const earthGroup = new THREE.Group();
earthGroup.rotation.z = 23.4 * Math.PI / 180;
scene.add(earthGroup);
const earthMat = new THREE.MeshPhongMaterial({color: 0xffffff, specular: new THREE.Color(0x333333), shininess: 14});
const earth = new THREE.Mesh(new THREE.SphereGeometry(R, 128, 128), earthMat);
earthGroup.add(earth);
tex('earth_atmos_2048.jpg', t => { earthMat.map = t; earthMat.needsUpdate = true; },
    () => { earthMat.color.set(0x2a5caa); document.getElementById('load').style.display = 'none'; });
loader.load(TEX + 'earth_normal_2048.jpg', t => { earthMat.normalMap = t; earthMat.normalScale = new THREE.Vector2(0.6, 0.6); earthMat.needsUpdate = true; });
loader.load(TEX + 'earth_specular_2048.jpg', t => { earthMat.specularMap = t; earthMat.needsUpdate = true; });

const cloudMat = new THREE.MeshPhongMaterial({transparent: true, opacity: 0.75, depthWrite: false});
const clouds = new THREE.Mesh(new THREE.SphereGeometry(R * 1.012, 96, 96), cloudMat);
earthGroup.add(clouds);
loader.load(TEX + 'earth_clouds_1024.png', t => { cloudMat.map = t; cloudMat.needsUpdate = true; });

// Atmosphere glow
const atm = new THREE.Mesh(new THREE.SphereGeometry(R * 1.14, 64, 64), new THREE.ShaderMaterial({
  vertexShader: 'varying vec3 vN; void main(){ vN = normalize(normalMatrix * normal); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: 'varying vec3 vN; void main(){ float i = pow(0.68 - dot(vN, vec3(0.0, 0.0, 1.0)), 3.0); gl_FragColor = vec4(0.28, 0.58, 1.0, 1.0) * i * 1.5; }',
  blending: THREE.AdditiveBlending, side: THREE.BackSide, transparent: true, depthWrite: false,
}));
scene.add(atm);

// ---- Moon + its orbit ring (1 lunar distance), for scale
const moonD = dist(1);
const moonMat = new THREE.MeshPhongMaterial({color: 0xbbbbbb, shininess: 2});
const moon = new THREE.Mesh(new THREE.SphereGeometry(R * 0.27, 48, 48), moonMat);
moon.position.set(moonD * Math.cos(0.5), 0.2, moonD * Math.sin(0.5));
scene.add(moon);
loader.load(TEX + 'moon_1024.jpg', t => { t.encoding = THREE.sRGBEncoding; moonMat.map = t; moonMat.color.set(0xffffff); moonMat.needsUpdate = true; });
const ring = new THREE.Mesh(new THREE.RingGeometry(moonD - 0.012, moonD + 0.012, 256),
  new THREE.MeshBasicMaterial({color: 0x8892b0, transparent: true, opacity: 0.35, side: THREE.DoubleSide}));
ring.rotation.x = Math.PI / 2; ring.position.y = 0.2; scene.add(ring);

function makeLabel(l1, l2, color) {
  const c = document.createElement('canvas'); c.width = 360; c.height = 120;
  const g = c.getContext('2d'), x = 4, y = 4, w = 352, h = 112, r = 22;
  g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
  g.fillStyle = 'rgba(8,12,24,0.85)'; g.fill();
  g.lineWidth = 4; g.strokeStyle = '#' + color.toString(16).padStart(6, '0'); g.stroke();
  g.textAlign = 'center'; g.fillStyle = '#ffffff'; g.font = 'bold 42px Segoe UI, Arial'; g.fillText(l1, 180, 55);
  g.fillStyle = '#9aa5c2'; g.font = '30px Segoe UI, Arial'; g.fillText(l2, 180, 95);
  const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({map: t, transparent: true}));
  s.scale.set(2.5, 0.83, 1); return s;
}

function makeRock(size, color) {
  const geo = new THREE.IcosahedronGeometry(1, 2);
  const p = geo.attributes.position, v = new THREE.Vector3();
  const seed = Math.random() * 100;
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    const n = 0.78 + 0.34 * Math.abs(Math.sin(v.x * 3.1 + seed) * Math.cos(v.y * 2.7 + seed) + Math.sin(v.z * 3.7 + seed) * 0.5);
    v.multiplyScalar(n); p.setXYZ(i, v.x, v.y * 0.8, v.z);
  }
  geo.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({color: 0x8c8277, roughness: 0.95, metalness: 0.05, flatShading: true, emissive: color, emissiveIntensity: 0.35});
  const m = new THREE.Mesh(geo, mat); m.scale.setScalar(size); return m;
}

// ---- Asteroids, links and distance labels
const rocks = [], mats = [];
DATA.forEach(o => {
  const az = o.az * Math.PI / 180, el = o.el * Math.PI / 180, d = dist(o.ld);
  const pos = new THREE.Vector3(d * Math.cos(el) * Math.cos(az), d * Math.sin(el), d * Math.cos(el) * Math.sin(az));
  const color = o.haz ? RED : GREEN;

  const size = Math.min(0.34, Math.max(0.1, Math.sqrt(o.diam) * 0.011));
  const rock = makeRock(size, color); rock.position.copy(pos); rock.userData = o;
  scene.add(rock); rocks.push(rock); if (o.haz) mats.push(rock.material);

  const start = pos.clone().normalize().multiplyScalar(R);
  const dir = pos.clone().sub(start), len = dir.length();
  const link = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, len, 6, 1, true),
    new THREE.MeshBasicMaterial({color, transparent: true, opacity: 0.8}));
  link.position.copy(start).addScaledVector(dir, 0.5);
  link.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
  scene.add(link);

  const lab = makeLabel(o.ld + ' LD', o.km + 'M km', color);
  lab.position.copy(start).addScaledVector(dir, 0.55).add(new THREE.Vector3(0, 0.3, 0));
  scene.add(lab);
});

// ---- Hover tooltip
const tip = document.getElementById('tip'), ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
renderer.domElement.addEventListener('mousemove', e => {
  const b = renderer.domElement.getBoundingClientRect();
  mouse.set(((e.clientX - b.left) / b.width) * 2 - 1, -((e.clientY - b.top) / b.height) * 2 + 1);
  ray.setFromCamera(mouse, camera);
  const hit = ray.intersectObjects(rocks)[0];
  if (hit) {
    const o = hit.object.userData;
    tip.innerHTML = '<b>' + o.name + '</b><br>' + (o.haz ? '<span style="color:#ff6b6b">Potentially hazardous</span>' : '<span style="color:#2ecc71">Not hazardous</span>') +
      '<br>Date: ' + o.date + '<br>Diameter: ~' + o.diam.toLocaleString() + ' m<br>Speed: ' + o.speed.toLocaleString() + ' km/h<br>Miss distance: ' + o.ld + ' LD (' + o.km + 'M km)';
    tip.style.display = 'block';
    tip.style.left = Math.min(e.clientX - b.left + 14, b.width - 230) + 'px';
    tip.style.top = Math.max(e.clientY - b.top - 10, 6) + 'px';
    renderer.domElement.style.cursor = 'pointer';
  } else { tip.style.display = 'none'; renderer.domElement.style.cursor = 'grab'; }
});

window.addEventListener('resize', () => { camera.aspect = W() / H(); camera.updateProjectionMatrix(); renderer.setSize(W(), H()); });

// ---- Animate
const clock = new THREE.Clock();
(function loop() {
  requestAnimationFrame(loop);
  const t = clock.getElapsedTime();
  earth.rotation.y += 0.0012; clouds.rotation.y += 0.0016;
  rocks.forEach((r, i) => { r.rotation.y += 0.004; r.rotation.x += 0.002; });
  mats.forEach(m => { m.emissiveIntensity = 0.5 + 0.35 * Math.sin(t * 3); });
  controls.update();
  renderer.render(scene, camera);
})();
</script>
"""
