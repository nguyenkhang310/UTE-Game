import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { CONFIG } from '../config.js';

// Tải khu B đã dựng trong Blender và tự sinh collider từ tên object.

export async function loadWorld(scene, renderer, onProgress) {
  const loader = new GLTFLoader();
  const gltf = await loader.loadAsync(CONFIG.modelUrl, (event) => {
    if (event.total > 0) onProgress(Math.min(0.98, event.loaded / event.total));
  });

  const root = gltf.scene;
  const anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const shrineName = 'tripo_node_9f7';
  root.traverse((object) => {
    if (!object.isMesh) return;

    const topName = topLevelName(object, root);
    const isGrass = /^Grass/.test(topName);
    const isGround = /^Plane/.test(topName);

    object.castShadow = !isGrass && !isGround;
    object.receiveShadow = true;

    const materials = Array.isArray(object.material) ? object.material : [object.material];
    for (const material of materials) {
      if (!material) continue;
      for (const key of ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'emissiveMap']) {
        if (material[key]) material[key].anisotropy = anisotropy;
      }
      if (/Leaves/i.test(material.name || '')) material.side = THREE.DoubleSide;

      // Cỏ trong file gốc dùng màu phẳng rất chói dưới đèn pin.
      if ((material.name === 'mat9' || material.name === 'mat10') && !material.userData.tuned) {
        material.userData.tuned = true;
        material.color.setRGB(0.16, 0.21, 0.13);
        material.roughness = 1;
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

  // Bỏ node bench bị scale z = 0 (mesh méo, không nhìn thấy).
  for (const child of root.children) {
    if (child.scale.z === 0 || child.scale.x === 0) child.visible = false;
  }

  scene.add(root);
  scene.updateMatrixWorld(true);

  const colliders = [];
  const box = new THREE.Box3();
  const center = new THREE.Vector3();

  root.traverse((child) => {
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

  onProgress(1);

  return {
    root,
    shrine,
    colliders,
    // Khe giữa hai thân cây phía sau miếu, nơi bóng đen sẽ lướt qua.
    shadowPath: { xFrom: -3.8, xTo: 4.8, z: -16.3 },
  };
}

function topLevelName(object, root) {
  let node = object;
  while (node.parent && node.parent !== root) node = node.parent;
  return node.name || '';
}

function findByNamePrefix(root, prefix) {
  let found = null;
  root.traverse((object) => {
    if (!found && object.name?.startsWith(prefix)) found = object;
  });
  return found;
}
