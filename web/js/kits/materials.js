import * as THREE from "three";

function lambert(color) {
  return new THREE.MeshLambertMaterial({ color, vertexColors: false });
}

export const moss = lambert(0x3e6b45);
export const mushroomCap = lambert(0xc4554a);
export const stem = lambert(0xefe6d4);
export const trunk = lambert(0x4a382c);
export const canopy = lambert(0x1d3328);
export const ground = lambert(0x6f8f62);
export const fog = 0xd5e2d2;
export const sun = 0xffe0b0;
