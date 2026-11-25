import * as THREE from 'three';
import { CONFIG } from '../config.js';

// Dựng phần không khí: sương mù, ánh trăng yếu, hai dãy tường gạch
// đóng khung khu B (thay cho phần tòa nhà không có trong file .glb).

export function createEnvironment(scene, renderer) {
  scene.background = new THREE.Color(CONFIG.backgroundColor);
  scene.fog = new THREE.FogExp2(CONFIG.fogColor, CONFIG.fogDensity);

  const hemi = new THREE.HemisphereLight(0x2e3d55, 0x050506, 0.5);
  scene.add(hemi);

  const moon = new THREE.DirectionalLight(0x93a7c9, 0.35);
  moon.position.set(-14, 24, -10);
  scene.add(moon);

  const colliders = [];

  // Hai dãy tường gạch của khu A/B, chỉ hiện lờ mờ trong sương.
  const brick = new THREE.TextureLoader().load(CONFIG.brickTextureUrl);
  brick.wrapS = brick.wrapT = THREE.RepeatWrapping;
  brick.repeat.set(9, 5);
  brick.colorSpace = THREE.SRGBColorSpace;
  brick.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());

  const wallMaterial = new THREE.MeshStandardMaterial({
    map: brick,
    color: 0x9c9086,
    roughness: 0.98,
    metalness: 0,
  });

  addBuilding(scene, wallMaterial, -17.2, -1);
  addBuilding(scene, wallMaterial, 16.4, 1);
  addEndWall(scene, wallMaterial, -24);
  addEndWall(scene, wallMaterial, 24);

  // Hộp va chạm cho hai bức tường (mặt trong).
  colliders.push({ type: 'box', minX: -25, maxX: -14.2, minZ: -30, maxZ: 30 });
  colliders.push({ type: 'box', minX: 13.4, maxX: 25, minZ: -30, maxZ: 30 });

  addWindowRows(scene, -14.17, 1, -1);
  addWindowRows(scene, 13.37, -1, 1);

  return { hemi, moon, colliders };
}

function addBuilding(scene, material, centerX, side) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(6, 16, 58), material);
  mesh.position.set(centerX, 8, 0);
  mesh.castShadow = false;
  mesh.receiveShadow = true;
  mesh.name = side < 0 ? 'BuildingLeft' : 'BuildingRight';
  scene.add(mesh);
}

// Tường đầu hồi, nằm ngoài mốc vòng lặp để che mép mặt đất khi nhìn ra xa.
function addEndWall(scene, material, z) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(34, 7, 1), material);
  mesh.position.set(0, 3.5, z);
  mesh.castShadow = false;
  mesh.receiveShadow = true;
  scene.add(mesh);
}

// Vài ô cửa sổ còn sáng, rải không đều để tòa nhà bớt "chết".
function addWindowRows(scene, x, rotationY, seedSign) {
  const lit = new THREE.MeshBasicMaterial({
    color: 0xd9a86a,
    transparent: true,
    opacity: 0.32,
    fog: true,
    depthWrite: false,
  });
  const dark = new THREE.MeshBasicMaterial({
    color: 0x0c0e11,
    fog: true,
  });
  const geometry = new THREE.PlaneGeometry(0.7, 1.05);

  const rows = [4.4, 7.2, 10, 12.8];
  rows.forEach((y, row) => {
    for (let i = -6; i <= 6; i++) {
      const on = ((i * 7 + row * 13 + (seedSign > 0 ? 5 : 0)) % 9 + 9) % 9 < 2;
      const win = new THREE.Mesh(geometry, on ? lit : dark);
      win.position.set(x, y, i * 3.6);
      win.rotation.y = rotationY * Math.PI * 0.5;
      scene.add(win);
    }
  });
}
