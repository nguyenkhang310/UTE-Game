// Cấu hình trung tâm cho bản demo Khu B & Miếu thờ HCMUTE.
// Mọi toạ độ tính bằng mét, hệ trục của Three.js.

export const CONFIG = {
  // Tài nguyên
  voiceUrl: './mieu-tho-audio.wav',
  modelUrl: './assets/khu-b-courtyard.glb',

  // Người chơi
  spawn: { x: -9.35, y: 0, z: 18.9, yaw: -0.24 },
  eyeHeight: 1.65,
  playerRadius: 0.34,
  walkSpeed: 3.1,
  runSpeed: 4.8,
  acceleration: 11,

  // Không gian chơi
  bounds: {
    xMin: -18.1,
    xMax: 15.25,
    zLoop: 21.5, // vượt mốc này sẽ bị "ma che mắt" đưa về đầu bên kia
  },

  // Bầu không khí
  fogColor: 0x0b0e14,
  fogDensity: 0.034,
  backgroundColor: 0x07090d,

  // Miếu thờ (dịch về cuối vườn để có hành trình đi bộ)
  shrine: { x: 0, y: 0, z: -14 },
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
  },
};
