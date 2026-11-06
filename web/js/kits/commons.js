import * as THREE from "three";

import { piece } from "./shape.js";

function flower(color) {
  return [
    piece(new THREE.CylinderGeometry(0.02, 0.03, 0.45, 5), 0x3e6b45, 0, 0.22, 0),
    piece(new THREE.SphereGeometry(0.14, 7, 5), color, 0, 0.5, 0),
    piece(new THREE.SphereGeometry(0.06, 5, 4), 0xf2e27a, 0, 0.56, 0.04),
  ];
}

function mushroom(cap, stem) {
  return [
    piece(new THREE.CylinderGeometry(0.05, 0.08, 0.28, 6), stem, 0, 0.14, 0),
    piece(new THREE.SphereGeometry(0.18, 8, 6), cap, 0, 0.32, 0, 0, 0, 0, 1.2, 0.45, 1.2),
  ];
}

function canopyTree(leaf, trunkScale = 1) {
  return [
    piece(new THREE.CylinderGeometry(0.18 * trunkScale, 0.42 * trunkScale, 8 * trunkScale, 7), 0x4a382c, 0, 4 * trunkScale, 0),
    piece(new THREE.SphereGeometry(2.4 * trunkScale, 10, 8), leaf, 0, 7.2 * trunkScale, 0),
    piece(new THREE.SphereGeometry(1.6 * trunkScale, 8, 6), leaf, 1.2 * trunkScale, 6.2 * trunkScale, 0.4),
    piece(new THREE.SphereGeometry(1.5 * trunkScale, 8, 6), leaf, -1.1 * trunkScale, 6.4 * trunkScale, -0.3),
  ];
}

export function commonParts(name) {
  if (name === "flower_pink") return flower(0xd47aa6);
  if (name === "flower_blue") return flower(0x7ec8e3);
  if (name === "flower_gold") return flower(0xe6c85a);
  if (name === "flower_white") return flower(0xf4f1ea);
  if (name === "mushroom_brown") return mushroom(0x8a5a32, 0xefe6d4);
  if (name === "mushroom_gold") return mushroom(0xe6c85a, 0xf2e6c8);
  if (name === "mushroom_white") return mushroom(0xf7f4ee, 0xefe6d4);
  if (name === "grass_patch") {
    return [piece(new THREE.CircleGeometry(0.8, 8), 0x7ea15a, 0, 0.02, 0, -Math.PI / 2, 0, 0)];
  }
  if (name === "dirt_patch") {
    return [piece(new THREE.CircleGeometry(0.7, 7), 0x8a6a45, 0, 0.02, 0, -Math.PI / 2, 0, 0)];
  }
  if (name === "mud_patch") {
    return [piece(new THREE.CircleGeometry(0.75, 8), 0x5c4632, 0, 0.03, 0, -Math.PI / 2, 0, 0)];
  }
  if (name === "water_puddle") {
    return [piece(new THREE.CircleGeometry(0.6, 10), 0x6e9aa3, 0, 0.02, 0, -Math.PI / 2, 0, 0)];
  }
  if (name === "fallen_leaves") {
    return [
      piece(new THREE.CircleGeometry(0.55, 6), 0xc47a3a, 0, 0.02, 0, -Math.PI / 2, 0.2, 0),
      piece(new THREE.CircleGeometry(0.28, 5), 0xd47aa6, 0.2, 0.03, 0.1, -Math.PI / 2, 0.8, 0),
    ];
  }
  if (name === "rabbit") {
    return [
      piece(new THREE.SphereGeometry(0.16, 7, 5), 0xf4f1ea, 0, 0.18, 0),
      piece(new THREE.SphereGeometry(0.08, 6, 4), 0xf4f1ea, 0, 0.32, 0.1),
      piece(new THREE.CylinderGeometry(0.015, 0.02, 0.18, 4), 0xf4f1ea, -0.04, 0.48, 0.08),
      piece(new THREE.CylinderGeometry(0.015, 0.02, 0.18, 4), 0xf4f1ea, 0.04, 0.48, 0.08),
    ];
  }
  if (name === "worm") {
    return [piece(new THREE.CapsuleGeometry(0.03, 0.16, 3, 6), 0xc47a6a, 0, 0.04, 0, 0, 0, Math.PI / 2)];
  }
  if (name === "monkey") {
    return [
      piece(new THREE.SphereGeometry(0.18, 8, 6), 0x8a5a32, 0, 0.45, 0),
      piece(new THREE.SphereGeometry(0.12, 7, 5), 0xc48a62, 0, 0.68, 0.08),
      piece(new THREE.CylinderGeometry(0.03, 0.04, 0.35, 5), 0x8a5a32, 0.16, 0.35, 0),
      piece(new THREE.CylinderGeometry(0.03, 0.04, 0.35, 5), 0x8a5a32, -0.16, 0.35, 0),
    ];
  }
  if (name === "songbird") {
    return [
      piece(new THREE.SphereGeometry(0.1, 7, 5), 0xe6c85a, 0, 0.15, 0),
      piece(new THREE.ConeGeometry(0.16, 0.08, 3), 0xd47aa6, 0.12, 0.16, 0, 0, 0, Math.PI / 2),
    ];
  }
  if (name === "butterfly") {
    return [
      piece(new THREE.SphereGeometry(0.04, 5, 4), 0x2a2440, 0, 0.12, 0),
      piece(new THREE.CircleGeometry(0.16, 6), 0x7ec8e3, 0.12, 0.14, 0),
      piece(new THREE.CircleGeometry(0.16, 6), 0xe6c85a, -0.12, 0.14, 0),
    ];
  }
  if (name === "tree_tall") return canopyTree(0x1d3328, 1.7);
  if (name === "tree_dead") {
    return [
      piece(new THREE.CylinderGeometry(0.12, 0.28, 7, 6), 0x6a5344, 0, 3.5, 0),
      piece(new THREE.CylinderGeometry(0.04, 0.06, 2.2, 4), 0x6a5344, 0.4, 5.2, 0.2, 0, 0, 0.8),
      piece(new THREE.CylinderGeometry(0.04, 0.06, 1.8, 4), 0x6a5344, -0.35, 4.8, -0.1, 0, 0, -0.7),
    ];
  }
  if (name === "tree_yellow") return canopyTree(0xe6c85a, 1);
  if (name === "tree_branched") {
    return [
      piece(new THREE.CylinderGeometry(0.16, 0.34, 6, 6), 0x4a382c, 0, 3, 0),
      piece(new THREE.CylinderGeometry(0.06, 0.1, 2.4, 5), 0x4a382c, 0.7, 4.6, 0.3, 0.4, 0, 0.7),
      piece(new THREE.CylinderGeometry(0.06, 0.1, 2.2, 5), 0x4a382c, -0.6, 4.4, -0.2, -0.3, 0, -0.8),
      piece(new THREE.SphereGeometry(0.7, 7, 5), 0x2f4a34, 1.3, 5.6, 0.5),
      piece(new THREE.SphereGeometry(0.65, 7, 5), 0x2f4a34, -1.1, 5.3, -0.3),
    ];
  }
  if (name === "tree_broad") return canopyTree(0x244232, 1.35);
  return null;
}
