import * as THREE from "three";

import { piece } from "./shape.js";

export function animalParts(name) {
  if (name === "heron") {
    return [
      piece(new THREE.CylinderGeometry(0.02, 0.02, 0.7, 4), 0xefe6d4, -0.05, 0.35, 0),
      piece(new THREE.CylinderGeometry(0.02, 0.02, 0.7, 4), 0xefe6d4, 0.05, 0.35, 0),
      piece(new THREE.SphereGeometry(0.12, 6, 5), 0x4e6d78, 0, 0.85, 0),
      piece(new THREE.CylinderGeometry(0.015, 0.02, 0.35, 4), 0x4e6d78, 0, 1.05, 0.12, 0.6, 0, 0),
    ];
  }
  if (name === "grazer") {
    return [
      piece(new THREE.SphereGeometry(0.45, 8, 6), 0xc47a3a, 0, 0.7, 0, 0, 0, 0, 1.6, 0.7, 0.8),
      piece(new THREE.SphereGeometry(0.22, 7, 5), 0xc47a3a, 0, 0.55, 0.7),
      piece(new THREE.CylinderGeometry(0.05, 0.06, 0.55, 4), 0x8a5a2a, -0.28, 0.28, 0.35),
      piece(new THREE.CylinderGeometry(0.05, 0.06, 0.55, 4), 0x8a5a2a, 0.28, 0.28, 0.35),
      piece(new THREE.CylinderGeometry(0.05, 0.06, 0.55, 4), 0x8a5a2a, -0.28, 0.28, -0.35),
      piece(new THREE.CylinderGeometry(0.05, 0.06, 0.55, 4), 0x8a5a2a, 0.28, 0.28, -0.35),
    ];
  }
  if (name === "loris") {
    return [
      piece(new THREE.SphereGeometry(0.16, 7, 6), 0x8a6a4a, 0, 0.2, 0),
      piece(new THREE.SphereGeometry(0.04, 5, 4), 0xf2c9ff, -0.05, 0.26, 0.12),
      piece(new THREE.SphereGeometry(0.04, 5, 4), 0xf2c9ff, 0.05, 0.26, 0.12),
    ];
  }
  if (name === "dragonfly") {
    return [
      piece(new THREE.CylinderGeometry(0.02, 0.03, 0.5, 5), 0x2f6f66, 0, 0.2, 0, Math.PI / 2, 0, 0),
      piece(new THREE.PlaneGeometry(0.35, 0.12), 0x9fd8c8, 0.12, 0.22, 0),
      piece(new THREE.PlaneGeometry(0.35, 0.12), 0x9fd8c8, -0.12, 0.22, 0),
    ];
  }
  if (name === "kite_bird") {
    return [piece(new THREE.ConeGeometry(0.45, 0.12, 3), 0xe25b4a, 0, 0.4, 0, 0, 0, Math.PI / 2)];
  }
  if (name === "glow_moth") {
    return [
      piece(new THREE.SphereGeometry(0.08, 6, 5), 0xf2c9ff, 0, 0.2, 0),
      piece(new THREE.PlaneGeometry(0.35, 0.18), 0xf2c9ff, 0.12, 0.22, 0),
      piece(new THREE.PlaneGeometry(0.35, 0.18), 0xf2c9ff, -0.12, 0.22, 0),
    ];
  }
  if (name === "lantern_frog") {
    return [
      piece(new THREE.SphereGeometry(0.16, 7, 5), 0x6f8f3a, 0, 0.14, 0),
      piece(new THREE.SphereGeometry(0.07, 6, 4), 0xd7f28a, 0, 0.16, 0.1),
    ];
  }
  if (name === "beetle_lamp") {
    return [
      piece(new THREE.SphereGeometry(0.16, 8, 6), 0x1c3b36, 0, 0.12, 0, 0, 0, 0, 1.3, 0.7, 1),
      piece(new THREE.SphereGeometry(0.05, 5, 4), 0xd7f28a, 0, 0.2, 0.05),
    ];
  }
  if (name === "brine_skipper") {
    return [piece(new THREE.ConeGeometry(0.05, 0.2, 4), 0xe7a0b4, 0, 0.08, 0, Math.PI / 2, 0, 0)];
  }
  return null;
}
