import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { CONFIG } from '../config.js';

// Tải khu B đã dựng trong Blender và tự sinh collider từ tên object.

export async function loadWorld(scene, renderer, onProgress) {
  const loader = new GLTFLoader();
  const { scene: root } = await loader.loadAsync(CONFIG.modelUrl, (event) => {
    if (event.total > 0) onProgress(Math.min(0.98, event.loaded / event.total));
  });
  const original = root.getObjectByName('OriginalKhuB');
  const anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const shrineName = 'tripo_node_9f7';
  root.traverse((object) => {
    if (!object.isMesh) return;

    object.castShadow = !object.userData.noShadow && !object.parent?.userData.noShadow;
    object.receiveShadow = true;

    const materials = Array.isArray(object.material) ? object.material : [object.material];
    for (const material of materials) {
      for (const key of ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'emissiveMap']) {
        if (material[key]) material[key].anisotropy = anisotropy;
      }
      if (material.name === 'Leaves_NormalTree') {
        material.side = THREE.DoubleSide;
        material.transparent = false;
        material.depthWrite = true;
        material.alphaTest = 0.36;
      }
    }
  });

  // Miếu thờ được tác giả đặt ở gốc toạ độ; dời về cuối vườn để
  // người chơi có một quãng đi bộ đủ dài trước khi chạm mặt.
  const shrine = findByNamePrefix(root, shrineName);
  if (shrine) {
    shrine.position.set(CONFIG.shrine.x, CONFIG.shrine.y, CONFIG.shrine.z);
  } else {
    console.warn('[world] Không tìm thấy node miếu thờ:', shrineName);
  }

  scene.add(root);
  scene.updateMatrixWorld(true);

  const colliders = [];
  const floors = [];
  const box = new THREE.Box3();
  const center = new THREE.Vector3();

  original.traverse((child) => {
    if (!child.visible) return;

    // Cây nằm trong RootNode nên phải duyệt sâu, không chỉ root.children.
    if (/^Tree\d*$/.test(child.name)) {
      child.getWorldPosition(center);
      const scale = Math.max(
        Math.abs(child.scale.x),
        Math.abs(child.scale.z),
        0.8,
      );
      colliders.push({ type: 'circle', x: center.x, z: center.z, r: 0.5 * scale });
      return;
    }

    if (/^Bench\d*$/.test(child.name) || child === shrine) {
      box.setFromObject(child);
      if (!Number.isFinite(box.min.x) || box.max.x - box.min.x < 0.1) return;
      colliders.push({
        type: 'box',
        minX: box.min.x,
        maxX: box.max.x,
        minZ: box.min.z,
        maxZ: box.max.z,
      });
    }
  });

  root.traverse((object) => {
    const data = object.userData;
    if (data.walkCollider || Number.isFinite(data.floorStart)) {
      object.getWorldPosition(center);
      const halfSize = object.getWorldScale(new THREE.Vector3());
      const area = {
        minX: center.x - halfSize.x,
        maxX: center.x + halfSize.x,
        minZ: center.z - halfSize.z,
        maxZ: center.z + halfSize.z,
      };
      if (data.walkCollider) colliders.push({ type: 'box', ...area });
      else floors.push({ ...area, start: data.floorStart, end: data.floorEnd });
    }

    if (data.courtyardLight) {
      const isPath = data.courtyardLight === 'path';
      const light = new THREE.PointLight(
        isPath ? 0xffda9e : 0xd3e7f2,
        isPath ? 21 : 12,
        isPath ? 10 : 6,
      );
      object.getWorldPosition(light.position);
      scene.add(light);
    }
  });

  onProgress(1);

  return {
    root,
    shrine,
    colliders,
    floors,
    // Khe giữa hai thân cây phía sau miếu, nơi bóng đen sẽ lướt qua.
    shadowPath: { xFrom: -3.8, xTo: 4.8, z: -16.3 },
  };
}

function findByNamePrefix(root, prefix) {
  let found = null;
  root.traverse((object) => {
    if (!found && object.name?.startsWith(prefix)) found = object;
  });
  return found;
}
