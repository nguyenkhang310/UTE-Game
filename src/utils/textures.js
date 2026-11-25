import * as THREE from 'three';

// Các texture nhỏ được vẽ bằng Canvas 2D để không cần thêm file ảnh.

export function makeGlowTexture() {
  const size = 128;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d');
  const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  g.addColorStop(0, 'rgba(255, 235, 190, 1)');
  g.addColorStop(0.25, 'rgba(255, 120, 40, 0.85)');
  g.addColorStop(0.6, 'rgba(190, 40, 10, 0.28)');
  g.addColorStop(1, 'rgba(0, 0, 0, 0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

export function makeSmokeTexture() {
  const size = 128;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d');
  const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  g.addColorStop(0, 'rgba(210, 205, 195, 0.65)');
  g.addColorStop(0.45, 'rgba(170, 168, 162, 0.22)');
  g.addColorStop(1, 'rgba(120, 120, 120, 0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

export function makeSilhouetteTexture() {
  const w = 128;
  const h = 256;
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = 'rgba(0, 0, 0, 0.96)';
  ctx.beginPath();
  // đầu
  ctx.arc(64, 38, 18, 0, Math.PI * 2);
  ctx.fill();
  // thân + vai
  ctx.beginPath();
  ctx.moveTo(50, 56);
  ctx.quadraticCurveTo(34, 66, 30, 104);
  ctx.lineTo(26, 170);
  ctx.lineTo(42, 170);
  ctx.lineTo(48, 118);
  ctx.lineTo(48, 196);
  ctx.lineTo(40, 248);
  ctx.lineTo(57, 250);
  ctx.lineTo(64, 190);
  ctx.lineTo(71, 250);
  ctx.lineTo(88, 248);
  ctx.lineTo(80, 196);
  ctx.lineTo(80, 118);
  ctx.lineTo(86, 170);
  ctx.lineTo(102, 170);
  ctx.lineTo(98, 104);
  ctx.quadraticCurveTo(94, 66, 78, 56);
  ctx.closePath();
  ctx.fill();

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}
