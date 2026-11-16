import * as THREE from "three";

const HEIGHT = 1.7;

export function createAvatar() {
  const material = new THREE.MeshLambertMaterial({ color: 0x6b5344 });
  const root = new THREE.Group();

  function arm(radius, length) {
    const pivot = new THREE.Group();
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, length, 6), material);
    mesh.position.y = -length / 2;
    pivot.add(mesh);
    return pivot;
  }

  function leg() {
    const hip = new THREE.Group();
    const thigh = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.4, 6), material);
    thigh.position.y = -0.2;
    const knee = new THREE.Group();
    knee.position.y = -0.4;
    const shin = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.05, 0.38, 6), material);
    shin.position.y = -0.19;
    knee.add(shin);
    hip.add(thigh, knee);
    return { hip, knee };
  }

  const legL = leg();
  legL.hip.position.set(-0.12, 0.78, 0);
  const legR = leg();
  legR.hip.position.set(0.12, 0.78, 0);
  const armL = arm(0.045, 0.55);
  armL.position.set(-0.24, 1.28, 0);
  const armR = arm(0.045, 0.55);
  armR.position.set(0.24, 1.28, 0);

  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.15, 0.5, 8), material);
  torso.position.set(0, 1.03, 0);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.16, 10, 8), material);
  head.position.set(0, HEIGHT - 0.16, 0);

  root.add(legL.hip, legR.hip, armL, armR, torso, head);

  let seated = false;

  function poseLeg(part, hipAngle, kneeAngle) {
    part.hip.rotation.x = hipAngle;
    part.knee.rotation.x = kneeAngle;
  }

  return {
    object: root,
    setColor(hex) {
      material.color.set(hex);
    },
    setWalkPhase(phase) {
      if (seated) return;
      const swing = Math.sin(phase) * 0.85;
      poseLeg(legL, swing, Math.max(0, swing) * 1.6);
      poseLeg(legR, -swing, Math.max(0, -swing) * 1.6);
      armL.rotation.x = -swing;
      armR.rotation.x = swing;
    },
    setSeated(value) {
      seated = Boolean(value);
      const hip = seated ? -1.15 : 0;
      const knee = seated ? 1.3 : 0;
      const arm = seated ? 0.15 : 0;
      poseLeg(legL, hip, knee);
      poseLeg(legR, hip, knee);
      armL.rotation.x = arm;
      armR.rotation.x = arm;
    },
  };
}
