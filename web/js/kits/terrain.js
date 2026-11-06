import * as THREE from "three";

import { piece } from "./shape.js";

export function terrainParts(name) {
  if (name === "dead_log") {
    return [piece(new THREE.CylinderGeometry(0.16, 0.18, 1.4, 7), 0x4a382c, 0, 0.16, 0, 0, 0, Math.PI / 2)];
  }
  if (name === "boulder") {
    return [piece(new THREE.IcosahedronGeometry(0.7, 0), 0x8a8178, 0, 0.45, 0)];
  }
  if (name === "river_stone") {
    return [piece(new THREE.IcosahedronGeometry(0.28, 0), 0x8a8178, 0, 0.16, 0)];
  }
  if (name === "cliff_wall") {
    return [piece(new THREE.BoxGeometry(2.2, 6, 0.6), 0x6d7270, 0, 3, 0)];
  }
  if (name === "waterfall_sheet") {
    return [piece(new THREE.PlaneGeometry(1.2, 1), 0xc5ddd8, 0, 0.5, 0)];
  }
  if (name === "mist_card") {
    return [piece(new THREE.PlaneGeometry(1.4, 0.8), 0xffffff, 0, 0.6, 0)];
  }
  if (name === "pool_disc") {
    return [piece(new THREE.CircleGeometry(1, 16), 0x6e9aa3, 0, 0.02, 0, -Math.PI / 2, 0, 0)];
  }
  if (name === "ridge_card") {
    return [piece(new THREE.PlaneGeometry(1.2, 2.4), 0x9aa7b0, 0, 1.2, 0)];
  }
  if (name === "rainbow_card") {
    return [piece(new THREE.TorusGeometry(1, 0.08, 6, 16, Math.PI), 0xf2c9ff, 0, 1.2, 0)];
  }
  if (name === "spiral_tree") {
    const parts = [];
    for (let i = 0; i < 6; i += 1) {
      parts.push(piece(new THREE.BoxGeometry(0.45, 0.35, 0.45), 0x6a4a78, Math.sin(i) * 0.15, 0.3 + i * 0.45, Math.cos(i) * 0.15, 0, i * 0.6, 0));
    }
    return parts;
  }
  if (name === "spore") {
    return [piece(new THREE.SphereGeometry(0.22, 8, 6), 0xd7f28a, 0, 0.3, 0)];
  }
  if (name === "crystal_shard") {
    return [piece(new THREE.ConeGeometry(0.12, 0.9, 4), 0xd7f0ff, 0, 0.45, 0)];
  }
  if (name === "salt_crust") {
    return [piece(new THREE.CircleGeometry(0.7, 7), 0xefe6d4, 0, 0.02, 0, -Math.PI / 2, 0, 0)];
  }
  if (name === "bone_rib") {
    return [piece(new THREE.TorusGeometry(0.45, 0.06, 5, 10, Math.PI), 0xefe6d4, 0, 0.45, 0)];
  }
  if (name === "seat_cushion") {
    return [
      piece(new THREE.CylinderGeometry(0.7, 0.7, 0.08, 12), 0x8a8178, 0, 0.04, 0),
      piece(new THREE.TorusGeometry(0.55, 0.08, 6, 12), 0x3e6b45, 0, 0.08, 0),
    ];
  }
  return null;
}
