import * as THREE from "three";

import { animalParts } from "./animals.js";
import { carnivoreParts } from "./carnivores.js";
import { plantParts } from "./plants.js";
import { mergeParts } from "./shape.js";
import { terrainParts } from "./terrain.js";

const cache = new Map();

export function kitParts(name) {
  return plantParts(name) || carnivoreParts(name) || animalParts(name) || terrainParts(name);
}

export function kitGeometry(name) {
  if (cache.has(name)) return cache.get(name);
  const parts = kitParts(name);
  if (!parts) throw new Error(`unknown kit ${name}`);
  const geometry = mergeParts(parts);
  cache.set(name, geometry);
  return geometry;
}

export function makeKit(name) {
  const geometry = kitGeometry(name);
  const material = new THREE.MeshLambertMaterial({ vertexColors: true });
  return new THREE.Mesh(geometry, material);
}
