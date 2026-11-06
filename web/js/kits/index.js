import * as THREE from "three";

import { canopy, moss, mushroomCap, stem, trunk } from "./materials.js";

function mossMound() {
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 12), moss);
  mesh.scale.set(1.4, 0.45, 1.2);
  mesh.position.y = 0.45;
  return mesh;
}

function mushroom() {
  const group = new THREE.Group();
  const stalk = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.1, 0.38, 8), stem);
  stalk.position.y = 0.19;
  const cap = new THREE.Mesh(new THREE.SphereGeometry(0.28, 12, 8), mushroomCap);
  cap.scale.set(1, 0.42, 1);
  cap.position.y = 0.42;
  group.add(stalk, cap);
  return group;
}

function fern() {
  const group = new THREE.Group();
  const fans = [
    [-0.55, -0.35],
    [0, 0],
    [0.55, 0.35],
  ];
  for (const [tilt, yaw] of fans) {
    const leaf = new THREE.Mesh(new THREE.ConeGeometry(0.09, 0.8, 5), moss);
    leaf.geometry.translate(0, 0.4, 0);
    leaf.rotation.z = tilt;
    leaf.rotation.y = yaw;
    group.add(leaf);
  }
  return group;
}

function tree() {
  const group = new THREE.Group();
  const bole = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.55, 10, 8), trunk);
  bole.position.y = 5;
  group.add(bole);
  const blobs = [
    [0, 8.5, 0, 2.2],
    [1.5, 7.2, 0.35, 1.7],
    [-1.35, 7.4, -0.4, 1.75],
  ];
  for (const [x, y, z, radius] of blobs) {
    const crown = new THREE.Mesh(new THREE.SphereGeometry(radius, 12, 10), canopy);
    crown.position.set(x, y, z);
    group.add(crown);
  }
  return group;
}

const BUILDERS = {
  moss_mound: mossMound,
  mushroom,
  fern,
  tree,
};

export function makeKit(name) {
  const build = BUILDERS[name];
  if (!build) throw new Error(`unknown kit ${name}`);
  return build();
}
