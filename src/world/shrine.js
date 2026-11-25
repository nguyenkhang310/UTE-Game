import * as THREE from 'three';
import { CONFIG } from '../config.js';
import { makeGlowTexture, makeSmokeTexture, makeSilhouetteTexture } from '../utils/textures.js';

// Miếu thờ: ánh lửa đỏ nhấp nháy, khói nhang, giọng thì thầm và
// màn jump scare nhẹ khi người chơi nhấn E.

const rand = (min, max) => min + Math.random() * (max - min);

export class ShrineSystem {
  constructor(scene, world, audio, hud) {
    this.scene = scene;
    this.audio = audio;
    this.hud = hud;
    this.center = new THREE.Vector3(CONFIG.shrine.x, 0, CONFIG.shrine.z);
    this.path = world.shadowPath;

    this.near = false;
    this.voiceNear = false;
    this.hintCooldown = 0;
    this.scareCooldown = 0;
    this.flare = 0;
    this.smokeLife = 0;
    this.shadowActive = false;
    this.shadowTime = 0;

    this._buildLight();
    this._buildGlow();
    this._buildSmoke();
    this._buildShadow();
  }

  _buildLight() {
    this.light = new THREE.PointLight(0xff3300, 7, 15, 2);
    this.light.position.set(CONFIG.shrine.x, 1.15, CONFIG.shrine.z + 0.2);
    this.scene.add(this.light);
  }

  _buildGlow() {
    const material = new THREE.SpriteMaterial({
      map: makeGlowTexture(),
      color: 0xffb27a,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      fog: false,
    });
    this.glow = new THREE.Sprite(material);
    this.glow.position.set(CONFIG.shrine.x, 1.5, CONFIG.shrine.z + 0.35);
    this.glow.scale.setScalar(2.2);
    this.scene.add(this.glow);
  }

  _buildSmoke() {
    const count = 46;
    const positions = new Float32Array(count * 3);
    this.smokeVel = [];
    for (let i = 0; i < count; i++) {
      positions[i * 3] = CONFIG.shrine.x + rand(-0.07, 0.07);
      positions[i * 3 + 1] = 1.15;
      positions[i * 3 + 2] = CONFIG.shrine.z + 0.3 + rand(-0.07, 0.07);
      this.smokeVel.push(new THREE.Vector3(rand(-0.08, 0.08), rand(0.2, 0.45), rand(-0.08, 0.08)));
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
      map: makeSmokeTexture(),
      size: 0.3,
      transparent: true,
      opacity: 0,
      depthWrite: false,
      color: 0xbfb9ae,
      blending: THREE.NormalBlending,
    });

    this.smoke = new THREE.Points(geometry, material);
    this.smoke.visible = false;
    this.smoke.frustumCulled = false;
    this.scene.add(this.smoke);
  }

  _buildShadow() {
    const material = new THREE.MeshBasicMaterial({
      map: makeSilhouetteTexture(),
      transparent: true,
      opacity: 0,
      depthWrite: false,
      side: THREE.DoubleSide,
      color: 0x080808,
      fog: true,
    });
    this.shadow = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 2.2), material);
    this.shadow.position.set(this.path.xFrom, 1.1, this.path.z);
    this.shadow.visible = false;
    this.scene.add(this.shadow);
  }

  update(dt, playerPosition, elapsed) {
    const distance = Math.hypot(
      playerPosition.x - this.center.x,
      playerPosition.z - this.center.z,
    );

    this.flare = Math.max(0, this.flare - dt * 1.1);
    this.hintCooldown = Math.max(0, this.hintCooldown - dt);
    this.scareCooldown = Math.max(0, this.scareCooldown - dt);

    // Lửa miếu: nhấp nháy chậm, thỉnh thoảng bùng lên.
    const pulse = 0.8 + 0.2 * Math.sin(elapsed * 5.1) + 0.06 * Math.sin(elapsed * 17.3);
    this.light.intensity = 7.5 * pulse * (1 + this.flare * 2.6);
    this.glow.material.opacity = 0.58 + 0.18 * Math.sin(elapsed * 4.2) + this.flare * 0.3;
    this.glow.scale.setScalar(2.05 + 0.16 * Math.sin(elapsed * 3.4) + this.flare * 0.8);

    // Giọng thì thầm chỉ nổi lên khi tới gần.
    const voiceNear = distance < CONFIG.shrineVoiceRadius;
    if (voiceNear && !this.voiceNear) {
      this.audio.playVoice();
      if (this.hintCooldown <= 0) {
        this.hud.showSubtitle('“Cầu cho con qua môn…”', 2600);
        this.hintCooldown = 24;
      }
    } else if (!voiceNear && this.voiceNear) {
      this.audio.stopVoice();
    }
    this.voiceNear = voiceNear;

    this.near = distance < CONFIG.shrineInteractRadius;
    if (this.scareCooldown > 0) {
      this.hud.setPrompt(null);
    } else {
      this.hud.setPrompt(this.near ? '[E] Thắp nhang' : null);
    }

    this._updateSmoke(dt);
    this._updateShadow(dt);
  }

  _updateSmoke(dt) {
    if (this.smokeLife <= 0) return;
    this.smokeLife -= dt;

    const position = this.smoke.geometry.attributes.position;
    for (let i = 0; i < position.count; i++) {
      const velocity = this.smokeVel[i];
      velocity.x += rand(-0.02, 0.02) * dt;
      velocity.z += rand(-0.02, 0.02) * dt;
      position.array[i * 3] += velocity.x * dt;
      position.array[i * 3 + 1] += velocity.y * dt;
      position.array[i * 3 + 2] += velocity.z * dt;
    }
    position.needsUpdate = true;

    this.smoke.material.opacity = Math.min(0.55, this.smokeLife * 0.35);
    this.smoke.material.size = 0.3 + (2.6 - this.smokeLife) * 0.08;

    if (this.smokeLife <= 0) {
      this.smoke.visible = false;
      this.smoke.material.opacity = 0;
    }
  }

  _updateShadow(dt) {
    if (!this.shadowActive) return;
    this.shadowTime += dt;
    const t = this.shadowTime / 0.75;

    if (t >= 1) {
      this.shadowActive = false;
      this.shadow.visible = false;
      this.shadow.material.opacity = 0;
      return;
    }

    this.shadow.visible = true;
    this.shadow.position.x = THREE.MathUtils.lerp(this.path.xFrom, this.path.xTo, t);
    this.shadow.position.z = this.path.z;
    this.shadow.position.y = 1.08 + Math.sin(t * Math.PI) * 0.08;
    this.shadow.material.opacity = 0.95 * Math.min(1, 0.25 + Math.sin(t * Math.PI) * 2.4);
  }

  startSmoke() {
    const position = this.smoke.geometry.attributes.position;
    for (let i = 0; i < position.count; i++) {
      position.array[i * 3] = CONFIG.shrine.x + rand(-0.06, 0.06);
      position.array[i * 3 + 1] = 1.12;
      position.array[i * 3 + 2] = CONFIG.shrine.z + 0.3 + rand(-0.06, 0.06);
      this.smokeVel[i].set(rand(-0.08, 0.08), rand(0.2, 0.45), rand(-0.08, 0.08));
    }
    position.needsUpdate = true;
    this.smokeLife = 2.8;
    this.smoke.material.opacity = 0.5;
    this.smoke.material.size = 0.3;
    this.smoke.visible = true;
  }

  tryInteract() {
    if (!this.near || this.scareCooldown > 0) return false;

    this.scareCooldown = 5.5;
    this.flare = 1.35;
    this.hud.setPrompt(null);
    this.hud.showSubtitle('Bạn thắp ba nén nhang. Khói không bay lên.', 2600);
    this.audio.duck(1.5);
    this.audio.stopVoice();
    this.startSmoke();

    setTimeout(() => {
      this.audio.scareRun();
      this.shadowActive = true;
      this.shadowTime = 0;
    }, 520);

    setTimeout(() => {
      this.hud.showSubtitle('Có gì đó vừa lướt qua khe cây…', 3200);
    }, 1500);

    setTimeout(() => {
      if (this.voiceNear) this.audio.playVoice();
    }, 3400);

    return true;
  }
}
