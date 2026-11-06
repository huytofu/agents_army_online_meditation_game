import * as THREE from "three";

import { groundHeight } from "./ground.js";
import { kitGeometry, makeKit } from "./kits/index.js";
import { loadCatalogGltf } from "./kits/gltf.js";
import { biomeAt, chunkIndex, paletteOf, riverZ } from "./meta.js";

const GROUND = {
  moss_plain: 0x6f8f62,
  cathedral_trees: 0x3e4a40,
  river: 0x6e8f62,
  waterfall_gorge: 0x6d7270,
  valley_bloom: 0x8aaa62,
  strange_fauna: 0x3a3550,
  carnivorous_bog: 0x4d5a32,
  lantern_orchard: 0x6d7344,
  fern_sea: 0x4f7a4a,
  hanging_vines: 0x4a6844,
  amber_herd: 0xc4a36a,
  salt_mirror: 0xe4dcc8,
};

const shared = new THREE.MeshLambertMaterial({ vertexColors: true });
const sheetMaterial = new THREE.MeshLambertMaterial({
  color: 0xc5ddd8,
  transparent: true,
  opacity: 0.45,
  side: THREE.DoubleSide,
  vertexColors: true,
});

export function createChunkWorld(scene, meta) {
  const loaded = new Map();
  let token = 0;
  let center = "";

  return {
    update(x, z) {
      const cx = chunkIndex(meta, x);
      const cz = chunkIndex(meta, z);
      const here = `${cx},${cz}`;
      if (here === center) return;
      center = here;
      const wanted = new Set();
      for (let ix = cx - 1; ix <= cx + 1; ix += 1) {
        for (let iz = cz - 1; iz <= cz + 1; iz += 1) {
          if (ix < 0 || iz < 0 || ix > 62 || iz > 62) continue;
          wanted.add(`${ix},${iz}`);
        }
      }
      for (const key of [...loaded.keys()]) {
        if (!wanted.has(key)) {
          loaded.get(key).dispose();
          loaded.delete(key);
        }
      }
      const generation = ++token;
      for (const key of wanted) {
        if (loaded.has(key)) continue;
        loaded.set(key, { ready: false, dispose() {} });
        const [ix, iz] = key.split(",").map(Number);
        buildChunk(scene, meta, ix, iz).then((chunk) => {
          if (generation !== token && !wanted.has(key)) {
            chunk.dispose();
            return;
          }
          if (!loaded.has(key)) {
            chunk.dispose();
            return;
          }
          loaded.set(key, chunk);
        }).catch(() => {
          loaded.delete(key);
        });
      }
    },
    animate(time) {
      for (const chunk of loaded.values()) chunk.animate?.(time);
    },
  };
}

async function buildChunk(scene, meta, cx, cz) {
  const response = await fetch(`/api/world/chunks/${cx}/${cz}`);
  if (!response.ok) throw new Error(`chunk ${cx},${cz}`);
  const payload = await response.json();
  const group = new THREE.Group();
  const motions = [];
  group.add(buildGround(meta, cx, cz));
  await addInstances(group, motions, payload.scatter);
  await addInstances(group, motions, payload.spots.map((spot) => ({
    kit: "seat_cushion",
    x: spot.x,
    y: spot.y,
    z: spot.z,
    rot_y: spot.yaw,
    scale: 1,
    motion: "none",
    motion_amount: 0,
    motion_period: 1,
  })));
  if (payload.water.length) group.add(buildWater(meta, payload.water));
  await addLandmarks(group, payload.landmarks);
  scene.add(group);
  return {
    animate(time) {
      const dummy = new THREE.Object3D();
      const touched = new Set();
      for (const item of motions) {
        const wave = Math.sin((time / item.period) * Math.PI * 2 + item.phase);
        dummy.position.set(item.x, item.y, item.z);
        dummy.rotation.set(0, item.rot, 0);
        dummy.scale.setScalar(item.scale);
        if (item.motion === "sway") dummy.rotation.z = item.amount * wave;
        if (item.motion === "bob" || item.motion === "uv_scroll") dummy.position.y += item.amount * wave;
        if (item.motion === "hop") dummy.position.y += item.amount * Math.max(0, wave) ** 2;
        if (item.motion === "drift" || item.motion === "path_circle") {
          dummy.position.x += item.amount * Math.sin(time / item.period);
          dummy.position.z += item.amount * Math.cos(time / item.period);
        }
        dummy.updateMatrix();
        item.mesh.setMatrixAt(item.index, dummy.matrix);
        touched.add(item.mesh);
      }
      for (const mesh of touched) mesh.instanceMatrix.needsUpdate = true;
      sheetMaterial.emissive?.setScalar?.(0);
    },
    dispose() {
      scene.remove(group);
      group.traverse((obj) => {
        if (!obj.userData.owned) return;
        obj.geometry?.dispose();
        if (obj.material && obj.material !== shared && obj.material !== sheetMaterial) obj.material.dispose?.();
      });
    },
  };
}

function buildGround(meta, cx, cz) {
  const x0 = meta.world_min + cx * meta.chunk_size;
  const z0 = meta.world_min + cz * meta.chunk_size;
  const width = Math.min(meta.chunk_size, meta.world_max - x0);
  const depth = Math.min(meta.chunk_size, meta.world_max - z0);
  const geometry = new THREE.PlaneGeometry(width, depth, 32, 32);
  geometry.rotateX(-Math.PI / 2);
  const position = geometry.attributes.position;
  const colors = new Float32Array(position.count * 3);
  for (let i = 0; i < position.count; i += 1) {
    const wx = x0 + width / 2 + position.getX(i);
    const wz = z0 + depth / 2 + position.getZ(i);
    position.setY(i, groundHeight(wx, wz));
    const biome = biomeAt(meta, wx, wz) || "moss_plain";
    const color = new THREE.Color(GROUND[biome] || 0x6f8f62);
    colors[i * 3] = color.r;
    colors[i * 3 + 1] = color.g;
    colors[i * 3 + 2] = color.b;
  }
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(geometry, shared);
  mesh.position.set(x0 + width / 2, 0, z0 + depth / 2);
  mesh.userData.owned = true;
  return mesh;
}

function bakedGeometry(root) {
  root.updateMatrixWorld(true);
  const geometries = [];
  root.traverse((obj) => {
    if (!obj.isMesh) return;
    const geometry = obj.geometry.clone();
    geometry.applyMatrix4(obj.matrixWorld);
    geometries.push(geometry);
  });
  if (!geometries.length) return null;
  if (geometries.length === 1) return geometries[0];
  return mergeBufferGeometries(geometries);
}

function mergeBufferGeometries(geometries) {
  let vertices = 0;
  let indexes = 0;
  for (const geometry of geometries) {
    vertices += geometry.attributes.position.count;
    indexes += geometry.index ? geometry.index.count : geometry.attributes.position.count;
  }
  const positions = new Float32Array(vertices * 3);
  const colors = new Float32Array(vertices * 3);
  const indices = new Uint32Array(indexes);
  let vertexBase = 0;
  let indexBase = 0;
  for (const geometry of geometries) {
    const position = geometry.attributes.position;
    const color = geometry.getAttribute("color");
    for (let i = 0; i < position.count; i += 1) {
      positions[(vertexBase + i) * 3] = position.getX(i);
      positions[(vertexBase + i) * 3 + 1] = position.getY(i);
      positions[(vertexBase + i) * 3 + 2] = position.getZ(i);
      if (color) {
        colors[(vertexBase + i) * 3] = color.getX(i);
        colors[(vertexBase + i) * 3 + 1] = color.getY(i);
        colors[(vertexBase + i) * 3 + 2] = color.getZ(i);
      } else {
        colors[(vertexBase + i) * 3] = 0.75;
        colors[(vertexBase + i) * 3 + 1] = 0.7;
        colors[(vertexBase + i) * 3 + 2] = 0.6;
      }
    }
    if (geometry.index) {
      for (let i = 0; i < geometry.index.count; i += 1) {
        indices[indexBase + i] = geometry.index.getX(i) + vertexBase;
      }
      indexBase += geometry.index.count;
    } else {
      for (let i = 0; i < position.count; i += 1) indices[indexBase + i] = vertexBase + i;
      indexBase += position.count;
    }
    vertexBase += position.count;
  }
  const merged = new THREE.BufferGeometry();
  merged.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  merged.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  merged.setIndex(new THREE.BufferAttribute(indices, 1));
  merged.computeVertexNormals();
  return merged;
}

function litMaterial(geometry, sourceMaterial) {
  const hasColor = Boolean(geometry.getAttribute("color"));
  return new THREE.MeshBasicMaterial({
    map: sourceMaterial?.map || null,
    vertexColors: hasColor && !sourceMaterial?.map,
    color: 0xffffff,
    side: THREE.DoubleSide,
  });
}

async function sourceFor(kit) {
  const gltf = await loadCatalogGltf("kits", kit);
  if (gltf) {
    const geometry = bakedGeometry(gltf.scene);
    if (geometry) {
      let sourceMaterial = null;
      gltf.scene.traverse((obj) => {
        if (obj.isMesh && !sourceMaterial) sourceMaterial = obj.material;
      });
      return { geometry, material: litMaterial(geometry, sourceMaterial) };
    }
  }
  return {
    geometry: kitGeometry(kit),
    material: kit === "waterfall_sheet" ? sheetMaterial : shared,
  };
}

async function addInstances(group, motions, blocks) {
  const byKit = new Map();
  for (const block of blocks) {
    if (!byKit.has(block.kit)) byKit.set(block.kit, []);
    byKit.get(block.kit).push(block);
  }
  for (const [kit, items] of byKit) {
    let geometry;
    let material;
    try {
      ({ geometry, material } = await sourceFor(kit));
    } catch {
      continue;
    }
    const mesh = new THREE.InstancedMesh(geometry, material, items.length);
    const dummy = new THREE.Object3D();
    items.forEach((block, index) => {
      dummy.position.set(block.x, block.y, block.z);
      dummy.rotation.y = block.rot_y || 0;
      dummy.scale.setScalar(block.scale || 1);
      dummy.updateMatrix();
      mesh.setMatrixAt(index, dummy.matrix);
      if (block.motion && block.motion !== "none") {
        motions.push({
          mesh,
          index,
          x: block.x,
          y: block.y,
          z: block.z,
          rot: block.rot_y || 0,
          scale: block.scale || 1,
          motion: block.motion,
          amount: block.motion_amount || 0,
          period: block.motion_period || 1,
          phase: index,
        });
      }
    });
    group.add(mesh);
  }
}

function buildWater(meta, samples) {
  const ordered = [...samples].sort((a, b) => a.x - b.x);
  const positions = [];
  for (let i = 0; i < ordered.length; i += 1) {
    const sample = ordered[i];
    const prev = ordered[Math.max(0, i - 1)];
    const next = ordered[Math.min(ordered.length - 1, i + 1)];
    const tx = next.x - prev.x || 1;
    const tz = next.z - prev.z;
    const length = Math.hypot(tx, tz) || 1;
    const px = (-tz / length) * 9;
    const pz = (tx / length) * 9;
    positions.push(sample.x + px, sample.y, sample.z + pz);
    positions.push(sample.x - px, sample.y, sample.z - pz);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  const indices = [];
  for (let i = 0; i < ordered.length - 1; i += 1) {
    const a = i * 2;
    indices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
  }
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  const material = new THREE.MeshLambertMaterial({
    color: 0x6e9aa3,
    transparent: true,
    opacity: 0.72,
    side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.userData.owned = true;
  return mesh;
}

async function addLandmarks(group, landmarks) {
  for (const landmark of landmarks) {
    const gltf = await loadCatalogGltf("landmarks", landmark.name);
    if (gltf) {
      gltf.scene.position.set(landmark.x, groundHeight(landmark.x, landmark.z), landmark.z);
      group.add(gltf.scene);
      continue;
    }
    for (const block of landmark.blocks) {
      const mesh = makeKit(block.kit);
      mesh.position.set(block.x, block.y, block.z);
      mesh.rotation.y = block.rot_y || 0;
      mesh.scale.setScalar(block.scale || 1);
      group.add(mesh);
    }
  }
}

export function riverDerivative(meta, x) {
  const river = meta.river;
  let slope = river.slope;
  for (const [amplitude, frequency] of river.sines) {
    slope += amplitude * frequency * Math.cos(x * frequency);
  }
  return slope;
}

export { biomeAt, paletteOf, riverZ };
