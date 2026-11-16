import * as THREE from "three";

import { kitGeometry } from "../js/kits/index.js";

const geometry = kitGeometry("seat_cushion");
geometry.computeBoundingBox();
const box = geometry.boundingBox;
const height = box.max.y;
const below = box.min.y;
let failed = false;
function expect(condition, message) {
  if (!condition) {
    failed = true;
    process.stderr.write(`${message}\n`);
  }
}
expect(height <= 0.25, `cushion top is ${height.toFixed(2)} m, high enough to block a seated view`);
expect(below >= -0.02, `cushion extends to ${below.toFixed(2)} m, so the moss ring stands through the ground`);

const eye = new THREE.Vector3(0, 1.5, -0.85);
const look = new THREE.Vector3(0, 1.5 + Math.sin((-6 * Math.PI) / 180), 1);
const camera = new THREE.PerspectiveCamera(60, 16 / 9, 0.1, 600);
camera.position.copy(eye);
camera.lookAt(look);
camera.updateMatrixWorld();
const mesh = new THREE.Mesh(geometry);
const ray = new THREE.Raycaster();
let hits = 0;
for (let y = -1; y <= 1; y += 0.25) {
  for (let x = -1; x <= 1; x += 0.25) {
    ray.setFromCamera(new THREE.Vector2(x, y), camera);
    if (ray.intersectObject(mesh).length) hits += 1;
  }
}
expect(hits === 0, `seated view hits the cushion ${hits} times`);

if (failed) process.exit(1);
process.stdout.write(`cushion: top ${height.toFixed(2)} m, view is clear\n`);
