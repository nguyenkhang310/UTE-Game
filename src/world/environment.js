import * as THREE from 'three';
import { CONFIG } from '../config.js';

export function createEnvironment(scene) {
  scene.background = new THREE.Color(CONFIG.backgroundColor);
  scene.fog = new THREE.FogExp2(CONFIG.fogColor, CONFIG.fogDensity);

  scene.add(new THREE.HemisphereLight(0x8ca5c4, 0x382c24, 0.64));
  const moon = new THREE.DirectionalLight(0xb7cdec, 0.80);
  moon.position.set(-14, 24, -10);
  scene.add(moon);
}
