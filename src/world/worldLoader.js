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
      colliders.push({ type: 'circle', x: center.x, z: center.z, r: 0.5 * scale, top: Infinity });
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
        top: child === shrine ? Infinity : box.max.y,
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
    measureTop: createTopMeasure(root, floors),
    updateLighting: createLocalLighting(scene, lamps),
    // Khe giữa hai thân cây phía sau miếu, nơi bóng đen sẽ lướt qua.
    shadowPath: {
      xFrom: CONFIG.shrine.x - 3.8,
      xTo: CONFIG.shrine.x + 4.8,
      z: CONFIG.shrine.z - 2.3 * shrineFront.z,
    },
  };
}

// Cao độ sàn tại (x, z) theo các vùng floorStart/floorEnd, vùng nhỏ được ưu tiên.
export function sampleFloor(floors, x, z) {
  for (const floor of floors) {
    if (x >= floor.minX && x <= floor.maxX && z >= floor.minZ && z <= floor.maxZ) {
      const across = floor.axis !== 'depth';
      const offset = across ? x - floor.minX : floor.maxZ - z;
      const span = across ? floor.maxX - floor.minX : floor.maxZ - floor.minZ;
      return THREE.MathUtils.lerp(floor.start, floor.end, offset / span);
    }
  }
  return 0;
}

// walkCollider trong GLB chỉ có mặt bằng, không có chiều cao. Hàm này đo đỉnh vật cản
// từ tam giác thật nằm trong vùng va chạm, để người chơi nhảy qua được tường thấp,
// lan can, ghế, bồn cây. Tam giác nào kéo dài quá `reach` mét trên sàn (tường, cột,
// thân cây) làm vật cản thành không vượt được. Kết quả được Player lưu lại theo collider.
function createTopMeasure(root, floors, reach = 2.2) {
  let meshes = null;
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const c = new THREE.Vector3();

  const isVisible = (object) => {
    for (let node = object; node; node = node.parent) if (!node.visible) return false;
    return true;
  };

  return (area) => {
    if (!meshes) {
      meshes = [];
      root.traverse((object) => {
        if (object.isMesh && object.geometry?.attributes.position && isVisible(object)) {
          meshes.push({ object, box: new THREE.Box3().setFromObject(object) });
        }
      });
    }

    const inset = 0.02;
    const x0 = area.minX + inset, x1 = area.maxX - inset;
    const z0 = area.minZ + inset, z1 = area.maxZ - inset;
    const base = Math.min(
      sampleFloor(floors, x0, z0), sampleFloor(floors, x1, z0),
      sampleFloor(floors, x0, z1), sampleFloor(floors, x1, z1),
      sampleFloor(floors, (x0 + x1) / 2, (z0 + z1) / 2),
    );
    const cap = base + reach;
    let top = -Infinity;

    for (const { object, box } of meshes) {
      if (box.max.x < x0 || box.min.x > x1 || box.max.z < z0 || box.min.z > z1 || box.min.y > cap) continue;
      const position = object.geometry.attributes.position;
      const index = object.geometry.index;
      const count = index ? index.count : position.count;
      const matrix = object.matrixWorld;
      for (let i = 0; i < count; i += 3) {
        a.fromBufferAttribute(position, index ? index.getX(i) : i).applyMatrix4(matrix);
        b.fromBufferAttribute(position, index ? index.getX(i + 1) : i + 1).applyMatrix4(matrix);
        c.fromBufferAttribute(position, index ? index.getX(i + 2) : i + 2).applyMatrix4(matrix);
        if (Math.max(a.x, b.x, c.x) < x0 || Math.min(a.x, b.x, c.x) > x1) continue;
        if (Math.max(a.z, b.z, c.z) < z0 || Math.min(a.z, b.z, c.z) > z1) continue;
        const low = Math.min(a.y, b.y, c.y);
        const high = Math.max(a.y, b.y, c.y);
        if (low >= cap || high <= base + 0.03) continue;
        if (high > cap) return Infinity;
        top = Math.max(top, high);
      }
    }
    // Không thấy hình học nào: đây là vách chặn vô hình, giữ nguyên tác dụng chặn.
    return top === -Infinity ? Infinity : top;
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
