import * as THREE from "three";

import { piece } from "./shape.js";

export function carnivoreParts(name) {
  if (name === "pitcher") {
    return [
      piece(new THREE.CylinderGeometry(0.18, 0.28, 1.6, 8), 0x6f8f3a, 0, 0.8, 0),
      piece(new THREE.CylinderGeometry(0.2, 0.16, 0.28, 8), 0xc4554a, 0, 1.55, 0),
      piece(new THREE.SphereGeometry(0.22, 8, 6), 0xd7e29a, 0.12, 1.75, 0),
    ];
  }
  if (name === "sundew") {
    const parts = [piece(new THREE.SphereGeometry(0.12, 6, 5), 0xe7a0b4, 0, 0.08, 0)];
    for (let i = 0; i < 6; i += 1) {
      const angle = (i / 6) * Math.PI * 2;
      parts.push(piece(new THREE.SphereGeometry(0.05, 5, 4), 0xf6f2c4, Math.cos(angle) * 0.22, 0.18, Math.sin(angle) * 0.22));
    }
    return parts;
  }
  if (name === "snap_maw") {
    return [
      piece(new THREE.SphereGeometry(0.28, 8, 6), 0xc4554a, -0.12, 0.2, 0, 0, 0, 0.6, 1, 0.45, 0.8),
      piece(new THREE.SphereGeometry(0.28, 8, 6), 0xf2e0a0, 0.12, 0.2, 0, 0, 0, -0.6, 1, 0.45, 0.8),
    ];
  }
  if (name === "acid_cup") {
    return [piece(new THREE.CylinderGeometry(0.32, 0.2, 0.22, 10), 0xd6e25a, 0, 0.11, 0)];
  }
  if (name === "vine_noose") {
    return [piece(new THREE.TorusGeometry(0.28, 0.04, 6, 12), 0x6a4a78, 0, 1.1, 0)];
  }
  return null;
}
