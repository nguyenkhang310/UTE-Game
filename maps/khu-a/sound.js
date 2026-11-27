import * as THREE from 'three';

// Both sounds use local synthesis, so sound can start without a network request.
function insects(context) {
  const rate = context.sampleRate;
  const buffer = context.createBuffer(1, rate * 2, rate);
  const samples = buffer.getChannelData(0);
  for (let i = 0; i < samples.length; i++) {
    const t = i / rate;
    const pulse = Math.pow(Math.max(0, Math.sin(2 * Math.PI * 9 * t)), 3);
    const phrase = .5 + .5 * Math.sin(Math.PI * t);
    samples[i] = .09 * pulse * phrase * (Math.sin(2 * Math.PI * 3680 * t)
      + .4 * Math.sin(2 * Math.PI * 4250 * t));
  }
  return buffer;
}

function footstep(context) {
  const rate = context.sampleRate;
  const buffer = context.createBuffer(1, Math.ceil(rate * .45), rate);
  const samples = buffer.getChannelData(0);
  let grit = 0;
  for (let i = 0; i < samples.length; i++) {
    const t = i / rate;
    grit = .91 * grit + .09 * (Math.random() * 2 - 1);
    samples[i] = Math.min(1, t * 220) * Math.exp(-12 * t)
      * (.7 * Math.sin(2 * Math.PI * (77 * t + .7 * (1 - Math.exp(-28 * t)))) + grit);
  }
  return buffer;
}

export function courtyardSound(camera, model) {
  const roofs = [];
  let garden, corridor;
  model.traverse(node => {
    if (node.userData.zoneSound === 'insects') garden = node;
    if (node.userData.zoneSound === 'step') corridor = node;
    if (node.userData.zoneSound === 'trigger') {
      const center = node.getWorldPosition(new THREE.Vector3());
      const half = node.getWorldScale(new THREE.Vector3());
      roofs.push(new THREE.Box3(center.clone().sub(half), center.clone().add(half)));
    }
  });
  let listener, ambience, step;
  let played = false;
  let active = false;
  const previous = new THREE.Vector3();

  function start() {
    try {
      if (!garden || !corridor) return;
      if (!listener) {
        listener = new THREE.AudioListener();
        camera.add(listener);
        ambience = new THREE.PositionalAudio(listener);
        ambience.setBuffer(insects(listener.context)).setRefDistance(7).setLoop(true);
        garden.add(ambience);
        step = new THREE.PositionalAudio(listener);
        step.setBuffer(footstep(listener.context)).setRefDistance(11);
        corridor.add(step);
        model.updateMatrixWorld(true);
      }
      listener.context.resume().catch(() => {});
    } catch (error) {
      console.warn('Không thể mở âm thanh Khu A', error);
    }
  }

  return {
    start,
    enter() {
      active = true;
      previous.copy(camera.position);
      if (ambience?.buffer && !ambience.isPlaying) ambience.play();
    },
    pause() {
      active = false;
      if (ambience?.isPlaying) ambience.pause();
      if (step?.isPlaying) step.stop();
    },
    move(position) {
      // +Y in Blender is -Z in Three. Cross the edge facing the small court.
      if (active && !played && step?.buffer && listener.context.state === 'running'
          && roofs.some(box => previous.z > box.max.z && box.containsPoint(position))) {
        played = true;
        const gain = ambience.gain.gain;
        const now = listener.context.currentTime;
        gain.cancelScheduledValues(now);
        gain.setTargetAtTime(.18, now, .12);
        gain.setTargetAtTime(1, now + 1.4, .35);
        step.play(.18);
      }
      previous.copy(position);
    },
  };
}
