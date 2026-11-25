import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';

const canvas = document.querySelector('#scene');
const menu = document.querySelector('#menu');
const notice = document.querySelector('#notice');
const enter = document.querySelector('#enter');
const viewpointButtons = [...document.querySelectorAll('[data-view]')];

try {
  await start();
} catch (error) {
  console.error(error);
  enter.textContent = 'Không tải được';
  notice.textContent = 'Hãy mở bản đồ qua máy chủ của game (npm run dev).';
}

async function start() {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.setSize(innerWidth, innerHeight, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.09;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.shadowMap.autoUpdate = false;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(62, innerWidth / innerHeight, 0.08, 290);
  const controls = new PointerLockControls(camera, canvas);
  controls.minPolarAngle = 0.12;
  controls.maxPolarAngle = Math.PI - 0.10;
  const sun = illuminate(scene, renderer);
  const model = await new GLTFLoader().loadAsync('./trung-tam.glb', (event) => {
    if (event.total > 0) enter.textContent = `Đang tải… ${Math.min(99, Math.round(100 * event.loaded / event.total))}%`;
  });

  const { colliders, floors, views } = prepareCampus(scene, model.scene, renderer);
  const keys = new Set();
  const clock = new THREE.Clock();
  const eyeHeight = 1.69;
  const radius = 0.32;
  const forward = new THREE.Vector3(), right = new THREE.Vector3(), move = new THREE.Vector3();
  const up = new THREE.Vector3(0, 1, 0);
  let lastShadowArea = '';
  let needsRender = true;

  function floorHeight(x, z) {
    for (const floor of floors) {
      if (x < floor.minX || x > floor.maxX || z < floor.minZ || z > floor.maxZ) continue;
      const across = floor.axis === 'x';
      const distance = across ? x - floor.minX : floor.maxZ - z;
      const span = across ? floor.maxX - floor.minX : floor.maxZ - floor.minZ;
      return THREE.MathUtils.lerp(floor.start, floor.end, distance / span);
    }
    return 0;
  }

  function blocked(x, z) {
    return colliders.some((area) => {
      const dx = x - THREE.MathUtils.clamp(x, area.minX, area.maxX);
      const dz = z - THREE.MathUtils.clamp(z, area.minZ, area.maxZ);
      return dx * dx + dz * dz < radius * radius;
    });
  }

  function updateShadow() {
    const x = Math.round(camera.position.x / 12) * 12;
    const z = Math.round(camera.position.z / 12) * 12;
    const area = `${x},${z}`;
    if (lastShadowArea === area) return;
    lastShadowArea = area;
    sun.target.position.set(x, 0, z);
    sun.position.set(x - 57, 78, z + 40);
    sun.target.updateMatrixWorld();
    renderer.shadowMap.needsUpdate = true;
  }

  function goTo(viewKey) {
    const view = views.get(viewKey);
    if (!view) return;
    camera.position.copy(view.position);
    camera.rotation.set(view.pitch, view.yaw, 0, 'YXZ');
    for (const button of viewpointButtons) button.setAttribute('aria-pressed', String(button.dataset.view === viewKey));
    updateShadow();
    needsRender = true;
  }

  function resize() {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight, false);
    needsRender = true;
  }

  const movementKeys = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown',
    'ArrowLeft', 'ArrowRight', 'ShiftLeft', 'ShiftRight']);
  window.addEventListener('resize', resize);
  window.addEventListener('blur', () => keys.clear());
  window.addEventListener('keydown', (event) => {
    if (!controls.isLocked || !movementKeys.has(event.code)) return;
    event.preventDefault();
    keys.add(event.code);
  });
  window.addEventListener('keyup', (event) => keys.delete(event.code));
  controls.addEventListener('change', () => { needsRender = true; });
  controls.addEventListener('lock', () => {
    notice.textContent = '';
    menu.hidden = true;
  });
  controls.addEventListener('unlock', () => {
    keys.clear();
    menu.hidden = false;
    enter.textContent = 'Tiếp tục';
    enter.focus();
  });
  document.addEventListener('pointerlockerror', () => {
    notice.textContent = 'Trình duyệt chưa khóa được chuột. Bấm nút vào bản đồ để thử lại.';
  });
  enter.addEventListener('click', () => controls.lock());
  for (const button of viewpointButtons) {
    button.disabled = false;
    button.addEventListener('click', () => goTo(button.dataset.view));
  }

  goTo('cong');
  enter.textContent = 'Đi bộ';
  enter.disabled = false;

  renderer.setAnimationLoop(() => {
    const dt = Math.min(clock.getDelta(), .045);
    if (controls.isLocked && keys.size > 0) {
      camera.getWorldDirection(forward);
      forward.y = 0;
      forward.normalize();
      right.crossVectors(forward, up);
      move.set(0, 0, 0);
      if (keys.has('KeyW') || keys.has('ArrowUp')) move.add(forward);
      if (keys.has('KeyS') || keys.has('ArrowDown')) move.sub(forward);
      if (keys.has('KeyD') || keys.has('ArrowRight')) move.add(right);
      if (keys.has('KeyA') || keys.has('ArrowLeft')) move.sub(right);
      const running = keys.has('ShiftLeft') || keys.has('ShiftRight');
      move.normalize().multiplyScalar(dt * (running ? 7.7 : 4.5));
      const nextX = THREE.MathUtils.clamp(camera.position.x + move.x, -103.5, 67.5);
      const nextZ = THREE.MathUtils.clamp(camera.position.z + move.z, -86.5, 24);
      if (!blocked(nextX, camera.position.z)) camera.position.x = nextX;
      if (!blocked(camera.position.x, nextZ)) camera.position.z = nextZ;
      updateShadow();
      needsRender = true;
    }
    if (controls.isLocked) {
      const target = eyeHeight + floorHeight(camera.position.x, camera.position.z);
      if (Math.abs(camera.position.y - target) > .001) {
        camera.position.y = THREE.MathUtils.damp(camera.position.y, target, 15, dt);
        needsRender = true;
      }
    }
    if (needsRender) {
      renderer.render(scene, camera);
      needsRender = false;
    }
  });
}

function illuminate(scene, renderer) {
  scene.fog = new THREE.FogExp2(0xb4cedc, 0.0047);
  const sky = document.createElement('canvas');
  sky.width = 256;
  sky.height = 128;
  const ctx = sky.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, sky.height);
  gradient.addColorStop(0, '#6ca7d9');
  gradient.addColorStop(.32, '#9bc6e3');
  gradient.addColorStop(.50, '#c5dce7');
  gradient.addColorStop(.535, '#a1ac94');
  gradient.addColorStop(1, '#506452');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, sky.width, sky.height);
  const skyTexture = new THREE.CanvasTexture(sky);
  skyTexture.colorSpace = THREE.SRGBColorSpace;
  skyTexture.mapping = THREE.EquirectangularReflectionMapping;
  scene.background = skyTexture;
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromEquirectangular(skyTexture).texture;
  scene.environmentIntensity = .55;
  pmrem.dispose();

  scene.add(new THREE.HemisphereLight(0xdcebff, 0x858069, 1.06));
  const sun = new THREE.DirectionalLight(0xffeed9, 2.25);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.left = -55;
  sun.shadow.camera.right = 55;
  sun.shadow.camera.top = 63;
  sun.shadow.camera.bottom = -49;
  sun.shadow.camera.near = .5;
  sun.shadow.camera.far = 255;
  sun.shadow.normalBias = .056;
  sun.shadow.bias = -.00012;
  sun.shadow.camera.updateProjectionMatrix();
  scene.add(sun, sun.target);
  return sun;
}

function prepareCampus(scene, root, renderer) {
  const colliders = [];
  const floors = [];
  const views = new Map();
  const anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const scale = new THREE.Vector3();
  const position = new THREE.Vector3();
  scene.add(root);
  scene.updateMatrixWorld(true);

  root.traverse((object) => {
    const data = object.userData;
    if (object.isMesh) {
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      for (const material of materials) {
        if (material.map) material.map.anisotropy = anisotropy;
        if (material.userData.leafCutout) {
          material.alphaTest = 0.46;
          material.transparent = false;
          material.depthWrite = true;
        }
      }
      object.castShadow = !data.noShadow && !object.parent?.userData.noShadow
        && materials.every((material) => !material.transparent);
      object.receiveShadow = true;
    }
    if (data.walkCollider || Number.isFinite(data.floorStart)) {
      object.getWorldPosition(position);
      object.getWorldScale(scale);
      const area = {
        minX: position.x - scale.x,
        maxX: position.x + scale.x,
        minZ: position.z - scale.z,
        maxZ: position.z + scale.z,
      };
      if (data.walkCollider) colliders.push(area);
      else floors.push({ ...area, start: data.floorStart, end: data.floorEnd, axis: data.floorAxis });
    }
    if (data.centralLight) {
      const light = new THREE.PointLight(0xffeed7, data.centralLight, 10.0);
      object.getWorldPosition(light.position);
      scene.add(light);
    }
    if (data.viewKey) {
      views.set(data.viewKey, { position: object.getWorldPosition(new THREE.Vector3()),
        yaw: data.viewYaw, pitch: data.viewPitch });
    }
  });
  floors.sort((a, b) => (a.maxX - a.minX) * (a.maxZ - a.minZ)
    - (b.maxX - b.minX) * (b.maxZ - b.minZ));
  return { colliders, floors, views };
}
