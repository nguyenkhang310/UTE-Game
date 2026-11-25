import * as THREE from 'three';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import { CONFIG } from '../config.js';
import { sampleFloor } from '../world/worldLoader.js';

const UP = new THREE.Vector3(0, 1, 0);
// Chênh lệch nhỏ hơn mức này coi như bước lên được, không cần nhảy.
const STEP_HEIGHT = 0.08;
// Sàn hụt xuống quá mức này thì rơi theo trọng lực thay vì trượt mượt xuống.
const FALL_DROP = 0.3;

// Điều khiển góc nhìn thứ nhất: WASD, Space nhảy, Alt khoá chuột, va chạm và
// vòng lặp không gian ở hai đầu vườn.
export class Player {
  constructor(camera, { colliders, floors = [], measureTop, onLock, onUnlock, onLoop, onFootstep }) {
    this.camera = camera;
    this.colliders = colliders;
    this.floors = floors;
    this.measureTop = measureTop;
    this.onLock = onLock;
    this.onUnlock = onUnlock;
    this.onLoop = onLoop;
    this.onFootstep = onFootstep;

    this.velocity = new THREE.Vector3();
    this.keys = new Set();
    this.bobPhase = 0;
    this.lastFootstep = 0;
    this.loopCooldown = 0;
    // Chuyển động dọc: cao độ bàn chân, vận tốc rơi và trạng thái chạm đất.
    this.feetY = 0;
    this.verticalVelocity = 0;
    this.grounded = true;
    this.jumpQueued = false;

    this.controls = new PointerLockControls(camera, document.body);
    this.controls.minPolarAngle = 0.12;
    this.controls.maxPolarAngle = Math.PI - 0.12;
    this.controls.addEventListener('lock', () => this.onLock?.());
    this.controls.addEventListener('unlock', () => {
      this.keys.clear();
      this.jumpQueued = false;
      this.velocity.set(0, 0, 0);
      this.onUnlock?.();
    });

    this._onKeyDown = this._onKeyDown.bind(this);
    this._onKeyUp = this._onKeyUp.bind(this);
    this._onBlur = this._onBlur.bind(this);
    window.addEventListener('keydown', this._onKeyDown, { capture: true });
    window.addEventListener('keyup', this._onKeyUp);
    window.addEventListener('blur', this._onBlur);

    this.teleport(CONFIG.spawn.x, CONFIG.spawn.z, CONFIG.spawn.yaw);
  }

  get isLocked() {
    return this.controls.isLocked;
  }

  lock() {
    if (document.pointerLockElement !== document.body) this.controls.lock();
  }

  teleport(x, z, yaw = 0) {
    this.feetY = sampleFloor(this.floors, x, z);
    this.verticalVelocity = 0;
    this.grounded = true;
    this.camera.position.set(x, this.feetY + CONFIG.eyeHeight, z);
    this.camera.rotation.set(0, yaw, 0, 'YXZ');
    this.velocity.set(0, 0, 0);
  }

  update(dt) {
    if (!this.camera) return;

    const move = new THREE.Vector3();
    const forward = new THREE.Vector3();
    const right = new THREE.Vector3();

    if (this.controls.isLocked) {
      this.camera.getWorldDirection(forward);
      forward.y = 0;
      if (forward.lengthSq() < 1e-6) forward.set(0, 0, -1);
      forward.normalize();
      right.crossVectors(forward, UP).normalize();

      if (this.keys.has('KeyW')) move.add(forward);
      if (this.keys.has('KeyS')) move.sub(forward);
      if (this.keys.has('KeyD')) move.add(right);
      if (this.keys.has('KeyA')) move.sub(right);
    }

    const sprinting = this.keys.has('ShiftLeft') || this.keys.has('ShiftRight');
    const speed = sprinting ? CONFIG.runSpeed : CONFIG.walkSpeed;

    if (move.lengthSq() > 0) {
      move.normalize().multiplyScalar(speed);
    }

    // Gia tốc mượt, không trượt băng.
    const t = 1 - Math.exp(-CONFIG.acceleration * dt);
    this.velocity.x += (move.x - this.velocity.x) * t;
    this.velocity.z += (move.z - this.velocity.z) * t;

    this._moveWithCollisions(this.velocity.x * dt, this.velocity.z * dt);

    // Nhịp bước chân + nhấp nhô đầu.
    const planarSpeed = Math.hypot(this.velocity.x, this.velocity.z);
    const moving = this.controls.isLocked && planarSpeed > 0.35 && this.grounded;
    if (moving) {
      this.bobPhase += dt * planarSpeed * 2.1;
      if (this.bobPhase - this.lastFootstep > Math.PI) {
        this.lastFootstep = this.bobPhase;
        this.onFootstep?.(planarSpeed > CONFIG.walkSpeed + 0.4);
      }
    } else {
      this.bobPhase += (0 - this.bobPhase) * Math.min(1, dt * 4);
    }

    const bob = Math.sin(this.bobPhase * 2) * 0.035 * Math.min(1, planarSpeed / 2);
    this._handleSpatialLoop(dt);
    this._updateVertical(dt);
    this.camera.position.y = this.feetY + CONFIG.eyeHeight + bob;
  }

  _updateVertical(dt) {
    const { x, z } = this.camera.position;
    const support = this._supportHeight(x, z);

    if (this.grounded) {
      if (this.jumpQueued && this.controls.isLocked) {
        this.grounded = false;
        this.verticalVelocity = CONFIG.jumpSpeed;
      } else if (support < this.feetY - FALL_DROP) {
        // Bước ra khỏi mép bồn, ghế, lan can: rơi xuống.
        this.grounded = false;
        this.verticalVelocity = 0;
      } else {
        this.feetY = THREE.MathUtils.damp(this.feetY, support, 18, dt);
      }
    }
    this.jumpQueued = false;
    if (this.grounded) return;

    this.verticalVelocity -= CONFIG.gravity * dt;
    this.feetY += this.verticalVelocity * dt;
    if (this.verticalVelocity <= 0 && this.feetY <= support) {
      this.feetY = support;
      this.verticalVelocity = 0;
      this.grounded = true;
      // Tiếng tiếp đất.
      this.onFootstep?.(true);
    }
  }

  _moveWithCollisions(dx, dz) {
    const position = this.camera.position;
    const r = CONFIG.playerRadius;

    let nextX = THREE.MathUtils.clamp(position.x + dx, CONFIG.bounds.xMin, CONFIG.bounds.xMax);
    if (!this._blocked(nextX, position.z, r)) position.x = nextX;

    let nextZ = position.z + dz;
    if (!this._blocked(position.x, nextZ, r)) position.z = nextZ;
  }

  _floorHeight(x, z) {
    return sampleFloor(this.floors, x, z);
  }

  // Mặt đứng dưới chân: sàn, hoặc đỉnh vật thấp (ghế, bồn, lan can) mà chân đang ở trên.
  _supportHeight(x, z) {
    let height = this._floorHeight(x, z);
    const margin = CONFIG.playerRadius * 0.5;
    for (const c of this.colliders) {
      if (c.type === 'circle' || !Number.isFinite(c.top)) continue;
      if (c.top <= height || c.top > this.feetY + STEP_HEIGHT) continue;
      if (x > c.minX - margin && x < c.maxX + margin && z > c.minZ - margin && z < c.maxZ + margin) {
        height = c.top;
      }
    }
    return height;
  }

  _topOf(c) {
    if (c.top === undefined) c.top = this.measureTop ? this.measureTop(c) : Infinity;
    return c.top;
  }

  _overlaps(c, x, z, radius) {
    if (c.type === 'circle') {
      const dx = x - c.x;
      const dz = z - c.z;
      const reach = c.r + radius;
      return dx * dx + dz * dz < reach * reach;
    }
    return x > c.minX - radius && x < c.maxX + radius && z > c.minZ - radius && z < c.maxZ + radius;
  }

  _blocked(x, z, radius) {
    const { x: currentX, z: currentZ } = this.camera.position;
    for (const c of this.colliders) {
      if (!this._overlaps(c, x, z, radius)) continue;
      // Chân đã cao hơn đỉnh vật cản: nhảy qua hoặc đang đứng trên nó.
      if (this._topOf(c) <= this.feetY + STEP_HEIGHT) continue;
      // Lỡ đang chồng lên vật cản (vừa rơi xuống sát mép) thì vẫn cho đi ra.
      if (this._overlaps(c, currentX, currentZ, radius)) continue;
      return true;
    }
    return false;
  }

  // "Ma che mắt": đi hết đầu vườn sẽ tỉnh dậy ở đầu bên kia,
  // kèm tiếng xì radio do audio system phát.
  _handleSpatialLoop(dt) {
    this.loopCooldown = Math.max(0, this.loopCooldown - dt);
    const position = this.camera.position;
    const { zMin, zMax } = CONFIG.bounds;
    if (position.z >= zMin && position.z <= zMax) return;

    if (this.loopCooldown > 0) {
      position.z = THREE.MathUtils.clamp(position.z, zMin, zMax);
      return;
    }

    position.z += (zMax - zMin) * (position.z < zMin ? 1 : -1);
    this.loopCooldown = 1.2;
    this.onLoop?.();
  }

  _onKeyDown(event) {
    if (event.code === 'AltLeft' || event.code === 'AltRight') {
      event.preventDefault();
      event.stopPropagation();
      if (this.controls.isLocked) this.controls.unlock();
      else this.lock();
      return;
    }

    if (event.code === 'Space') {
      if (this.controls.isLocked) {
        event.preventDefault();
        if (!event.repeat) this.jumpQueued = true;
      }
      return;
    }

    if (['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ShiftLeft', 'ShiftRight'].includes(event.code)) {
      this.keys.add(event.code);
      if (event.code.startsWith('Key')) event.preventDefault();
    }
  }

  _onKeyUp(event) {
    this.keys.delete(event.code);
  }

  _onBlur() {
    this.keys.clear();
  }
}
