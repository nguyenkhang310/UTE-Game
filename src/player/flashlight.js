import * as THREE from 'three';
import { CONFIG } from '../config.js';

const rand = (min, max) => min + Math.random() * (max - min);

// Đèn pin gắn theo camera. Không sáng đều: thỉnh thoảng chập chờn
// vài nhịp rồi mới ổn định lại.
export class Flashlight {
  constructor(camera) {
    this.on = false;
    this.base = CONFIG.flashlight.intensity;
    this.nextFlicker = rand(4, 8);
    this.flickerTime = null;
    this.flickerDuration = 0;

    const { color, distance, angle, penumbra, decay } = CONFIG.flashlight;
    this.spot = new THREE.SpotLight(color, 0, distance, angle, penumbra, decay);
    this.spot.position.set(0.18, -0.12, 0);
    this.spot.castShadow = true;
    this.spot.shadow.mapSize.set(1024, 1024);
    this.spot.shadow.camera.near = 0.2;
    this.spot.shadow.camera.far = 30;
    this.spot.shadow.bias = -0.0009;
    this.spot.shadow.normalBias = 0.025;
    this.spot.shadow.radius = 2;

    this.target = new THREE.Object3D();
    this.target.position.set(0.1, -0.03, -8);
    this.spot.target = this.target;

    // Ánh sáng hắt yếu quanh chân để không bị đen tuyệt đối.
    this.fill = new THREE.PointLight(0xffe9c4, 0, 4.5, 2);
    this.fill.position.set(0.1, -0.25, 0.2);

    camera.add(this.spot);
    camera.add(this.target);
    camera.add(this.fill);
  }

  toggle() {
    this.on = !this.on;
    if (this.on) {
      this.spot.intensity = this.base;
      this.fill.intensity = 1.1;
      this.flickerTime = null;
      this.nextFlicker = rand(3.5, 7);
    } else {
      this.spot.intensity = 0;
      this.fill.intensity = 0;
    }
    return this.on;
  }

  update(dt) {
    if (!this.on) return;

    if (this.flickerTime !== null) {
      this.flickerTime += dt;
      if (this.flickerTime >= this.flickerDuration) {
        this.flickerTime = null;
        this.flickerDuration = 0;
        this.nextFlicker = rand(4, 10);
        this.spot.intensity = this.base;
        this.fill.intensity = 1.1;
      } else {
        // Nháy rất nhanh, có lúc tắt hẳn một nhịp.
        const gate = Math.sin(this.flickerTime * 145) + Math.sin(this.flickerTime * 71 + 1.3);
        const factor = gate > 0.2 ? 0.02 : 0.9;
        this.spot.intensity = this.base * factor;
        this.fill.intensity = 1.1 * factor;
      }
      return;
    }

    this.nextFlicker -= dt;
    if (this.nextFlicker <= 0) {
      this.flickerTime = 0;
      this.flickerDuration = rand(0.22, 0.55);
    }
  }
}
