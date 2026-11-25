import * as THREE from 'three';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import { CONFIG } from '../config.js';

const UP = new THREE.Vector3(0, 1, 0);

// Điều khiển góc nhìn thứ nhất: WASD, Alt khoá chuột, va chạm và
// vòng lặp không gian ở hai đầu vườn.
export class Player {
  constructor(camera, { colliders, floors = [], onLock, onUnlock, onLoop, onFootstep }) {
    this.camera = camera;
    this.colliders = colliders;
    this.floors = floors;
    this.onLock = onLock;
    this.onUnlock = onUnlock;
    this.onLoop = onLoop;
    this.onFootstep = onFootstep;

    this.velocity = new THREE.Vector3();
    this.keys = new Set();
    this.bobPhase = 0;
    this.lastFootstep = 0;
    this.loopCooldown = 0;

    this.controls = new PointerLockControls(camera, document.body);
    this.controls.minPolarAngle = 0.12;
    this.controls.maxPolarAngle = Math.PI - 0.12;
    this.controls.addEventListener('lock', () => this.onLock?.());
    this.controls.addEventListener('unlock', () => {
      this.keys.clear();
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
    this.camera.position.set(x, CONFIG.eyeHeight + this._floorHeight(x, z), z);
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
    const moving = this.controls.isLocked && planarSpeed > 0.35;
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

    const { x, z } = this.camera.position;
    const targetHeight = CONFIG.eyeHeight + this._floorHeight(x, z) + bob;
    this.camera.position.y = THREE.MathUtils.damp(this.camera.position.y, targetHeight, 18, dt);
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
    for (const floor of this.floors) {
      if (x >= floor.minX && x <= floor.maxX && z >= floor.minZ && z <= floor.maxZ) {
        const t = (x - floor.minX) / (floor.maxX - floor.minX);
        return THREE.MathUtils.lerp(floor.start, floor.end, t);
      }
    }
    return 0;
  }

  _blocked(x, z, radius) {
    for (const c of this.colliders) {
      if (c.type === 'circle') {
        const dx = x - c.x;
        const dz = z - c.z;
        const reach = c.r + radius;
        if (dx * dx + dz * dz < reach * reach) return true;
      } else {
        if (
          x > c.minX - radius &&
          x < c.maxX + radius &&
          z > c.minZ - radius &&
          z < c.maxZ + radius
        ) {
          return true;
        }
      }
    }
    return false;
  }

  // "Ma che mắt": đi hết đầu vườn sẽ tỉnh dậy ở đầu bên kia,
  // kèm tiếng xì radio do audio system phát.
  _handleSpatialLoop(dt) {
    this.loopCooldown = Math.max(0, this.loopCooldown - dt);
    if (this.loopCooldown > 0) return;

    const z = this.camera.position.z;
    const limit = CONFIG.bounds.zLoop;

    if (z > limit) {
      this.camera.position.z = z - limit * 2;
      this.loopCooldown = 1.2;
      this.onLoop?.();
    } else if (z < -limit) {
      this.camera.position.z = z + limit * 2;
      this.loopCooldown = 1.2;
      this.onLoop?.();
    }
  }

  _onKeyDown(event) {
    if (event.code === 'AltLeft' || event.code === 'AltRight') {
      event.preventDefault();
      event.stopPropagation();
      if (this.controls.isLocked) this.controls.unlock();
      else this.lock();
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
