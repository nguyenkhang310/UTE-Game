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

  // Giữ vị trí tương tác cùng tọa độ miếu trong cảnh Blender.
  const shrine = findByNamePrefix(root, shrineName);
  if (shrine) {
    shrine.position.set(CONFIG.shrine.x, CONFIG.shrine.y, CONFIG.shrine.z);
  } else {
    console.warn('[world] Không tìm thấy node miếu thờ:', shrineName);
  }

  scene.add(root);
  scene.updateMatrixWorld(true);

  // Mặt thờ của mesh gốc hướng theo trục +Z cục bộ.
  const shrineFront = new THREE.Vector3(0, 0, 1);
  shrine?.getWorldDirection(shrineFront);

  const colliders = [];
  const floors = [];
  const lamps = [];
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
      else floors.push({
        ...area,
        start: data.floorStart,
        end: data.floorEnd,
        axis: data.floorAxis || 'x',
      });
    }

    if (data.courtyardLight) {
      const isPath = data.courtyardLight === 'path';
      lamps.push({
        position: object.getWorldPosition(new THREE.Vector3()),
        color: isPath ? 0xffda9e : 0xd3e7f2,
        intensity: isPath ? 21 : 12,
        range: isPath ? 10 : 6,
        distanceSquared: 0,
      });
    }
  });

  // Ưu tiên bậc thềm tại chỗ tiếp giáp với sàn hành lang.
  const floorArea = (floor) => (floor.maxX - floor.minX) * (floor.maxZ - floor.minZ);
  floors.sort((a, b) => floorArea(a) - floorArea(b));
  onProgress(1);

  return {
    root,
    shrine,
    shrineFront,
    colliders,
    floors,
    updateLighting: createLocalLighting(scene, lamps),
    // Khe giữa hai thân cây phía sau miếu, nơi bóng đen sẽ lướt qua.
    shadowPath: {
      xFrom: CONFIG.shrine.x - 3.8,
      xTo: CONFIG.shrine.x + 4.8,
      z: CONFIG.shrine.z - 2.3 * shrineFront.z,
    },
  };
}

function createLocalLighting(scene, lamps) {
  // Reuse the same lights so changing neighborhoods does not recompile materials.
  const activeLights = lamps.slice(0, CONFIG.render.localLightCount).map(() => {
    const light = new THREE.PointLight(0xffffff, 0);
    scene.add(light);
    return light;
  });
  const lastPosition = new THREE.Vector3(Infinity, Infinity, Infinity);

  return (cameraPosition) => {
    if (lastPosition.distanceToSquared(cameraPosition) < 0.5 ** 2) return;
    lastPosition.copy(cameraPosition);
    for (const lamp of lamps) lamp.distanceSquared = lamp.position.distanceToSquared(cameraPosition);
    lamps.sort((a, b) => a.distanceSquared - b.distanceSquared);
    for (let index = 0; index < activeLights.length; index++) {
      const light = activeLights[index];
      const lamp = lamps[index];
      light.position.copy(lamp.position);
      light.color.setHex(lamp.color);
      light.intensity = lamp.intensity;
      light.distance = lamp.range;
    }
  };
}

function findByNamePrefix(root, prefix) {
  let found = null;
  root.traverse((object) => {
    if (!found && object.name?.startsWith(prefix)) found = object;
  });
  return found;
}
