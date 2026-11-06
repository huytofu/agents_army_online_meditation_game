import * as THREE from "three";

import { piece } from "./shape.js";

const moss = 0x3e6b45;
const cap = 0xc4554a;
const stem = 0xefe6d4;
const trunk = 0x4a382c;
const canopy = 0x1d3328;
const flowerA = 0xd47aa6;
const flowerB = 0xe6c85a;
const flowerC = 0x7ec8e3;
const fern = 0x3e6b45;
const stag = 0x7ea15a;
const blossomA = 0xe25b8a;
const blossomB = 0xf2c14e;
const glassA = 0x7ee0c8;
const glassB = 0xf2a3c7;

export function plantParts(name) {
  if (name === "moss_mound") {
    return [piece(new THREE.SphereGeometry(1, 12, 8), moss, 0, 0.45, 0, 0, 0, 0, 1.4, 0.45, 1.2)];
  }
  if (name === "cushion_moss") {
    return [piece(new THREE.SphereGeometry(1, 10, 6), 0x7ea15a, 0, 0.22, 0, 0, 0, 0, 1.3, 0.22, 1.1)];
  }
  if (name === "mushroom") {
    return [
      piece(new THREE.CylinderGeometry(0.07, 0.1, 0.38, 7), stem, 0, 0.19, 0),
      piece(new THREE.SphereGeometry(0.28, 10, 6), cap, 0, 0.42, 0, 0, 0, 0, 1, 0.42, 1),
    ];
  }
  if (name === "fern" || name === "fiddlehead") {
    const parts = [];
    const fans = name === "fiddlehead" ? [[0.8, 0.4]] : [[-0.5, -0.3], [0, 0], [0.5, 0.3]];
    for (const [tilt, yaw] of fans) {
      const cone = new THREE.ConeGeometry(name === "fiddlehead" ? 0.12 : 0.09, 0.8, 5);
      cone.translate(0, 0.4, 0);
      parts.push(piece(cone, fern, 0, 0, 0, 0, yaw, tilt));
    }
    return parts;
  }
  if (name === "tree" || name === "blossom_tree") {
    const leafA = name === "blossom_tree" ? blossomA : canopy;
    const leafB = name === "blossom_tree" ? blossomB : canopy;
    return [
      piece(new THREE.CylinderGeometry(0.22, 0.55, 10, 7), trunk, 0, 5, 0),
      piece(new THREE.SphereGeometry(2.2, 10, 8), leafA, 0, 8.5, 0),
      piece(new THREE.SphereGeometry(1.7, 8, 6), leafB, 1.5, 7.2, 0.35),
      piece(new THREE.SphereGeometry(1.75, 8, 6), leafA, -1.35, 7.4, -0.4),
    ];
  }
  if (name === "staghorn") {
    return [
      piece(new THREE.BoxGeometry(0.15, 1.1, 0.7), stag, -0.25, 0.7, 0, 0, 0.4, 0.5),
      piece(new THREE.BoxGeometry(0.15, 1.1, 0.7), stag, 0.25, 0.7, 0, 0, -0.4, -0.5),
    ];
  }
  if (name === "wildflower" || name === "seed_head" || name === "reed") {
    const head = name === "seed_head" ? flowerB : name === "reed" ? 0x7ea15a : flowerA;
    return [
      piece(new THREE.CylinderGeometry(0.02, 0.03, 0.7, 4), 0x3e6b45, 0, 0.35, 0),
      piece(new THREE.SphereGeometry(name === "reed" ? 0.05 : 0.12, 6, 5), head, 0, 0.75, 0),
      piece(new THREE.SphereGeometry(0.08, 5, 4), flowerC, 0.1, 0.7, 0.05),
    ];
  }
  if (name === "glass_leaf") {
    return [piece(new THREE.PlaneGeometry(0.8, 0.35), glassA, 0, 0.4, 0, 0.4, 0.2, 0)];
  }
  if (name === "epiphyte") {
    return [
      piece(new THREE.SphereGeometry(0.25, 8, 6), moss, 0, 0.3, 0),
      piece(new THREE.ConeGeometry(0.12, 0.45, 5), cap, 0, 0.55, 0),
    ];
  }
  if (name === "lily_pad") {
    return [
      piece(new THREE.CircleGeometry(0.55, 10), moss, 0, 0.02, 0, -Math.PI / 2, 0, 0),
      piece(new THREE.SphereGeometry(0.08, 6, 4), flowerA, 0.1, 0.08, 0),
    ];
  }
  if (name === "vine_strand") {
    return [piece(new THREE.CylinderGeometry(0.03, 0.04, 2.2, 5), moss, 0, 1.1, 0)];
  }
  return null;
}
