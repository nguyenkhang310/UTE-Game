import * as THREE from 'three';
import { CONFIG } from './config.js';
import { createEnvironment } from './world/environment.js';
import { loadWorld } from './world/worldLoader.js';
import { Player } from './player/player.js';
import { Flashlight } from './player/flashlight.js';
import { AudioSystem } from './audio/audio.js';
import { ShrineSystem } from './world/shrine.js';
import { HUD } from './ui/hud.js';

const canvas = document.getElementById('game');
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  powerPreference: 'high-performance',
});
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(72, window.innerWidth / window.innerHeight, 0.05, 160);
scene.add(camera);

const hud = new HUD();
createEnvironment(scene);
const flashlight = new Flashlight(camera);
const audio = new AudioSystem(scene, camera);

let player = null;
let shrine = null;
let world = null;
let ready = false;
let hasShownIntro = false;
let hasShownLoopHint = false;

function resize() {
  const { innerWidth: width, innerHeight: height } = window;
  const { maxPixelRatio, maxPixels } = CONFIG.render;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, maxPixelRatio, Math.sqrt(maxPixels / (width * height))));
  renderer.setSize(width, height);
}
window.addEventListener('resize', resize);
resize();

try {
  world = await loadWorld(scene, renderer, (progress) => hud.setLoading(progress));

  shrine = new ShrineSystem(scene, world, audio, hud);

  player = new Player(camera, {
    colliders: world.colliders,
    floors: world.floors,
    onLock: () => {
      hud.hideOverlay();
      if (!hasShownIntro) {
        hasShownIntro = true;
        hud.showSubtitle('WASD di chuyển · F bật đèn pin · E tương tác', 5200);
      }
    },
    onUnlock: () => {
      hud.showPause();
    },
    onLoop: () => {
      hud.glitch();
      audio.staticBurst(0.24);
      if (!hasShownLoopHint) {
        hasShownLoopHint = true;
        hud.showSubtitle('Bạn đã đi quá xa. Khu B đưa bạn trở lại.', 3000);
      }
    },
    onFootstep: (running) => audio.footstep(running),
  });

  ready = true;
  hud.setReady();
  hud.setEnterHandler(() => {
    if (!ready) return;
    audio.init();
    player.lock();
  });

  // Tiện cho việc chỉnh sửa/kiểm tra cục bộ trong DevTools.
  window.__demo = { scene, camera, player, shrine, flashlight, hud, audio, renderer, world };
} catch (error) {
  console.error(error);
  hud.showError(error?.message || 'Lỗi không xác định');
}

// Chạm vào màn hình cũng vào game được, đề phòng phím Alt bị trình duyệt chặn.
canvas.addEventListener('click', () => {
  if (!ready) return;
  if (!player.isLocked) {
    audio.init();
    player.lock();
  }
});

window.addEventListener('keydown', (event) => {
  if (event.repeat) return;
  if (!player || !player.isLocked) return;

  if (event.code === 'KeyF') {
    hud.setTorch(flashlight.toggle());
  } else if (event.code === 'KeyE') {
    shrine?.tryInteract();
  }
});

const clock = new THREE.Clock();

renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.05);

  if (ready) {
    player?.update(dt);
    world.updateLighting(camera.position);
    flashlight.update(dt);
    shrine?.update(dt, camera.position, clock.elapsedTime);
  }

  renderer.render(scene, camera);
});
