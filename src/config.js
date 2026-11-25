// Cấu hình trung tâm cho bản demo Khu B & Miếu thờ HCMUTE.
// Mọi toạ độ tính bằng mét, hệ trục của Three.js.

export const CONFIG = {
  // Tài nguyên
  voiceUrl: './mieu-tho-audio.wav',
  modelUrl: './assets/khu-b-courtyard.glb',

  // Người chơi
  spawn: { x: -10.02, y: 0, z: 28.13, yaw: 0.337 },
  eyeHeight: 1.65,
  playerRadius: 0.34,
  walkSpeed: 3.1,
  runSpeed: 4.8,
  acceleration: 11,
  // Đỉnh nhảy = jumpSpeed² / (2 · gravity) ≈ 1,0 m, đủ qua lan can hành lang cao ~0,9 m.
  jumpSpeed: 6.6,
  gravity: 22,

  // Không gian chơi
  bounds: {
    xMin: -56.4,
    xMax: 23.8,
    zMin: -46.2,
    zMax: 82,
  },

  // Bầu không khí
  fogColor: 0x0b0e14,
  fogDensity: 0.027,
  backgroundColor: 0x07090d,
  render: {
    maxPixelRatio: 1.5,
    maxPixels: 1920 * 1080,
    localLightCount: 6,
  },

  // Chấm đỏ trong vườn giữa C và D, lệch trái thư viện.
  shrine: { x: -34.4, y: 0.03, z: 34.65 },
  shrineVoiceRadius: 5,
  shrineInteractRadius: 2.6,

  // Đèn pin
  flashlight: {
    color: 0xfff1d2,
    intensity: 30,
    distance: 28,
    angle: Math.PI / 6,
    penumbra: 0.4,
    decay: 1.35,
    shadowSize: 512,
  },
};
