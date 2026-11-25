import * as THREE from 'three';
import { CONFIG } from '../config.js';

// Toàn bộ âm thanh nền được tổng hợp bằng Web Audio (gió, dế, drone,
// bước chân, xì radio). Giọng thì thầm ở miếu dùng file .wav thật.

const rand = (min, max) => min + Math.random() * (max - min);

export class AudioSystem {
  constructor(scene, camera) {
    this.scene = scene;
    this.listener = new THREE.AudioListener();
    camera.add(this.listener);
    this.ctx = this.listener.context;

    this.ready = false;
    this.voice = null;
    this.voiceRequested = false;
    this.ambience = null;
    this.master = null;
    this.cricketTimer = null;

    this.noiseBuffer = null;
  }

  async init() {
    if (this.ready) {
      await this.ctx.resume();
      return;
    }

    await this.ctx.resume();

    this.master = this.ctx.createGain();
    this.master.gain.value = 0.9;
    this.master.connect(this.listener.getInput());

    this.ambience = this.ctx.createGain();
    this.ambience.gain.value = 0.55;
    this.ambience.connect(this.master);

    this.noiseBuffer = this._makeNoiseBuffer(2);

    this._buildWind();
    this._buildDrone();
    this._scheduleCrickets();
    this._loadVoice();

    this.ready = true;
  }

  // ---------- Nền ----------

  _makeNoiseBuffer(seconds) {
    const length = Math.floor(this.ctx.sampleRate * seconds);
    const buffer = this.ctx.createBuffer(1, length, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    let last = 0;
    for (let i = 0; i < length; i++) {
      const white = Math.random() * 2 - 1;
      last = last * 0.7 + white * 0.3; // làm mượt nhẹ, đỡ chói
      data[i] = last;
    }
    return buffer;
  }

  _buildWind() {
    const ctx = this.ctx;
    const source = ctx.createBufferSource();
    source.buffer = this.noiseBuffer;
    source.loop = true;

    const low = ctx.createBiquadFilter();
    low.type = 'lowpass';
    low.frequency.value = 380;

    const gain = ctx.createGain();
    gain.gain.value = 0.16;

    const lfo = ctx.createOscillator();
    lfo.frequency.value = 0.06;
    const lfoDepth = ctx.createGain();
    lfoDepth.gain.value = 0.07;
    lfo.connect(lfoDepth).connect(gain.gain);

    source.connect(low).connect(gain).connect(this.ambience);
    source.start();
    lfo.start();

    // Tiếng rít nhẹ phía trên gió.
    const hiss = ctx.createBufferSource();
    hiss.buffer = this.noiseBuffer;
    hiss.loop = true;
    const band = ctx.createBiquadFilter();
    band.type = 'bandpass';
    band.frequency.value = 1100;
    band.Q.value = 0.6;
    const hissGain = ctx.createGain();
    hissGain.gain.value = 0.022;
    hiss.connect(band).connect(hissGain).connect(this.ambience);
    hiss.start();
  }

  _buildDrone() {
    const ctx = this.ctx;
    const gain = ctx.createGain();
    gain.gain.value = 0.05;
    const low = ctx.createBiquadFilter();
    low.type = 'lowpass';
    low.frequency.value = 180;

    [46, 48.7, 92].forEach((freq, i) => {
      const osc = ctx.createOscillator();
      osc.type = 'sine';
      osc.frequency.value = freq;
      const g = ctx.createGain();
      g.gain.value = i === 2 ? 0.15 : 0.5;
      osc.connect(g).connect(low);
      osc.start();
    });

    low.connect(gain).connect(this.ambience);
  }

  _scheduleCrickets() {
    const delay = rand(650, 1900);
    this.cricketTimer = setTimeout(() => {
      this._chirp();
      this._scheduleCrickets();
    }, delay);
  }

  _chirp() {
    if (!this.ready && !this.ambience) return;
    const ctx = this.ctx;
    const now = ctx.currentTime;
    const pan = ctx.createStereoPanner();
    pan.pan.value = rand(-0.9, 0.9);
    pan.connect(this.ambience);

    const pulses = Math.floor(rand(2, 5));
    for (let i = 0; i < pulses; i++) {
      const t = now + i * 0.055 + rand(0, 0.012);
      const osc = ctx.createOscillator();
      osc.type = 'triangle';
      osc.frequency.value = rand(3600, 4400);
      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.0001, t);
      gain.gain.exponentialRampToValueAtTime(rand(0.012, 0.026), t + 0.008);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.045);
      osc.connect(gain).connect(pan);
      osc.start(t);
      osc.stop(t + 0.06);
    }
  }

  // ---------- Giọng thì thầm ở miếu ----------

  _loadVoice() {
    if (this.voiceRequested) return;
    this.voiceRequested = true;

    const loader = new THREE.AudioLoader();
    loader.load(
      CONFIG.voiceUrl,
      (buffer) => {
        const voice = new THREE.PositionalAudio(this.listener);
        voice.setBuffer(buffer);
        voice.setLoop(true);
        voice.setRefDistance(1.6);
        voice.setMaxDistance(12);
        voice.setRolloffFactor(1.5);
        voice.setDistanceModel('exponential');
        voice.setVolume(1.8);
        voice.position.set(CONFIG.shrine.x, 1.1, CONFIG.shrine.z);
        this.scene.add(voice);
        this.voice = voice;
      },
      undefined,
      (error) => console.warn('[audio] Không tải được giọng miếu:', error),
    );
  }

  playVoice() {
    if (!this.voice) return;
    if (!this.voice.isPlaying) this.voice.play();
  }

  stopVoice() {
    if (!this.voice || !this.voice.isPlaying) return;
    this.voice.stop();
  }

  // ---------- Hiệu ứng ----------

  _burst({ duration = 0.2, type = 'lowpass', freq = 500, q = 0.8, gain = 0.1, pan = 0, when = 0, target = null, attack = 0.006 }) {
    const ctx = this.ctx;
    const start = ctx.currentTime + when;
    const source = ctx.createBufferSource();
    source.buffer = this.noiseBuffer;

    const filter = ctx.createBiquadFilter();
    filter.type = type;
    filter.frequency.value = freq;
    filter.Q.value = q;

    const envelope = ctx.createGain();
    envelope.gain.setValueAtTime(0.0001, start);
    envelope.gain.exponentialRampToValueAtTime(Math.max(0.0002, gain), start + attack);
    envelope.gain.exponentialRampToValueAtTime(0.0001, start + duration);

    const panner = ctx.createStereoPanner();
    panner.pan.value = pan;

    source.connect(filter).connect(envelope).connect(panner).connect(target || this.master);
    const offset = Math.random() * 1.2;
    source.start(start, offset, duration + 0.05);
    source.stop(start + duration + 0.1);
  }

  footstep(running = false) {
    if (!this.ready) return;
    this._burst({
      duration: 0.12,
      type: 'lowpass',
      freq: running ? 420 : 330,
      gain: running ? 0.085 : 0.06,
      pan: rand(-0.25, 0.25),
    });
  }

  staticBurst(volume = 0.2) {
    if (!this.ready) return;
    this._burst({ duration: 0.5, type: 'bandpass', freq: 1500, q: 1.4, gain: volume, target: this.master });
    this._burst({ duration: 0.35, type: 'highpass', freq: 2600, q: 0.7, gain: volume * 0.6, when: 0.05 });
    for (let i = 0; i < 5; i++) {
      this._burst({
        duration: 0.03,
        type: 'highpass',
        freq: 3000,
        gain: volume * 0.7,
        pan: rand(-0.6, 0.6),
        when: rand(0.02, 0.42),
      });
    }
  }

  duck(duration = 1.5) {
    if (!this.ready) return;
    const now = this.ctx.currentTime;
    const gain = this.ambience.gain;
    gain.cancelScheduledValues(now);
    gain.setValueAtTime(Math.max(0.0001, gain.value), now);
    gain.linearRampToValueAtTime(0.0001, now + 0.12);
    gain.setValueAtTime(0.0001, now + duration);
    gain.linearRampToValueAtTime(0.55, now + duration + 0.9);
  }

  scareRun() {
    if (!this.ready) return;
    const ctx = this.ctx;
    // Tiếng chân chạy trên lá khô, quét từ trái sang phải.
    for (let i = 0; i < 10; i++) {
      this._burst({
        duration: 0.09,
        type: 'highpass',
        freq: rand(900, 1600),
        q: 0.7,
        gain: rand(0.05, 0.1),
        pan: -0.9 + (i / 9) * 1.8,
        when: 0.55 + i * 0.065 + rand(0, 0.02),
      });
    }
    // Tiếng bước nặng.
    [0.55, 0.85, 1.15].forEach((t) => {
      this._burst({ duration: 0.16, type: 'lowpass', freq: 180, gain: 0.12, when: t, pan: rand(-0.4, 0.4) });
    });

    // Một cú giật trầm.
    const start = ctx.currentTime;
    const osc = ctx.createOscillator();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(70, start);
    osc.frequency.exponentialRampToValueAtTime(38, start + 0.8);
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(0.15, start + 0.04);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.9);
    osc.connect(gain).connect(this.master);
    osc.start(start);
    osc.stop(start + 1);
  }

  dispose() {
    if (this.cricketTimer) clearTimeout(this.cricketTimer);
  }
}
