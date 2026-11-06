import * as THREE from "three";

import { groundHeight } from "./ground.js";
import { makeKit } from "./kits/index.js";
import { loadCatalogGltf } from "./kits/gltf.js";

export async function createDiorama(spot, blocks) {
  const root = new THREE.Group();
  const items = [];
  for (const block of blocks) {
    const mesh = await piece(block.kit);
    mesh.scale.setScalar(block.scale || 1);
    root.add(mesh);
    items.push({ mesh, block, slides: captureSlides(mesh) });
  }
  return {
    object: root,
    update(time) {
      const clock = time + 0.17 * spot.id;
      for (const item of items) {
        const local = localPoint(item.block, clock);
        slide(item, clock);
        const yaw = spot.yaw;
        const wx = spot.x + local.x * Math.cos(yaw) + local.z * Math.sin(yaw);
        const wz = spot.z - local.x * Math.sin(yaw) + local.z * Math.cos(yaw);
        item.mesh.position.set(wx, groundHeight(wx, wz) + local.y, wz);
        item.mesh.rotation.set(0, yaw + (item.block.rot_y || 0), local.sway);
      }
    },
    dispose() {
      root.removeFromParent();
      root.traverse((obj) => {
        if (!obj.isMesh) return;
        obj.geometry?.dispose();
        const materials = Array.isArray(obj.material) ? obj.material : [obj.material];
        for (const material of materials) material?.dispose?.();
      });
    },
  };
}

async function piece(name) {
  const gltf = await loadCatalogGltf("kits", name);
  if (gltf) {
    const mesh = gltf.scene.clone(true);
    mesh.traverse((obj) => {
      if (!obj.isMesh) return;
      obj.geometry = obj.geometry.clone();
      obj.material = Array.isArray(obj.material)
        ? obj.material.map((material) => material.clone())
        : obj.material.clone();
    });
    return mesh;
  }
  const source = makeKit(name);
  const mesh = new THREE.Mesh(source.geometry.clone(), source.material.clone());
  return mesh;
}

function captureSlides(root) {
  const slides = [];
  root.traverse((obj) => {
    if (!obj.isMesh) return;
    const uv = obj.geometry.getAttribute("uv");
    const position = obj.geometry.getAttribute("position");
    slides.push({
      uv,
      uvBase: uv ? Float32Array.from(uv.array) : null,
      position,
      positionBase: position ? Float32Array.from(position.array) : null,
      map: obj.material?.map || null,
    });
  });
  return slides;
}

function localPoint(block, time) {
  const period = block.motion_period || 1;
  const amount = block.motion_amount || 0;
  const wave = Math.sin((Math.PI * 2 * time) / period);
  let x = block.x;
  let y = block.y;
  let z = block.z;
  let sway = 0;
  if (block.motion === "sway") sway = amount * wave;
  if (block.motion === "bob") y += amount * wave;
  if (block.motion === "hop") y += amount * Math.max(0, wave) ** 2;
  if (block.motion === "drift") {
    x += amount * Math.sin(time);
    z += amount * Math.cos(time * 0.7);
  }
  if (block.motion === "path_circle") {
    const angle = (Math.PI * 2 * time) / period;
    x += Math.cos(angle) * amount;
    z += Math.sin(angle) * amount;
  }
  return { x, y, z, sway };
}

function slide(item, time) {
  if (item.block.motion !== "uv_scroll") return;
  const shift = (item.block.motion_amount || 0) * time;
  for (const entry of item.slides) {
    if (entry.map) {
      entry.map.offset.y = shift;
      continue;
    }
    if (entry.uvBase) {
      const array = entry.uv.array;
      for (let index = 1; index < array.length; index += 2) {
        array[index] = entry.uvBase[index] + shift;
      }
      entry.uv.needsUpdate = true;
    } else if (entry.positionBase) {
      const wrapped = shift % 0.4;
      const array = entry.position.array;
      for (let index = 1; index < array.length; index += 3) {
        array[index] = entry.positionBase[index] - wrapped;
      }
      entry.position.needsUpdate = true;
    }
  }
}
