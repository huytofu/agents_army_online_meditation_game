import * as THREE from "three";

export function piece(geometry, color, x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, sx = 1, sy = 1, sz = 1) {
  return { geometry, color, x, y, z, rx, ry, rz, sx, sy, sz };
}

export function mergeParts(parts) {
  const baked = parts.map((part) => {
    const geometry = part.geometry.clone();
    const color = new THREE.Color(part.color);
    const count = geometry.attributes.position.count;
    const colors = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    const matrix = new THREE.Matrix4().compose(
      new THREE.Vector3(part.x, part.y, part.z),
      new THREE.Quaternion().setFromEuler(new THREE.Euler(part.rx, part.ry, part.rz)),
      new THREE.Vector3(part.sx, part.sy, part.sz),
    );
    geometry.applyMatrix4(matrix);
    return geometry;
  });
  let vertices = 0;
  let indexes = 0;
  for (const geometry of baked) {
    vertices += geometry.attributes.position.count;
    indexes += geometry.index ? geometry.index.count : geometry.attributes.position.count;
  }
  const positions = new Float32Array(vertices * 3);
  const colors = new Float32Array(vertices * 3);
  const indices = new Uint32Array(indexes);
  let vertexBase = 0;
  let indexBase = 0;
  for (const geometry of baked) {
    const position = geometry.attributes.position;
    const color = geometry.attributes.color;
    for (let i = 0; i < position.count; i += 1) {
      positions[(vertexBase + i) * 3] = position.getX(i);
      positions[(vertexBase + i) * 3 + 1] = position.getY(i);
      positions[(vertexBase + i) * 3 + 2] = position.getZ(i);
      colors[(vertexBase + i) * 3] = color.getX(i);
      colors[(vertexBase + i) * 3 + 1] = color.getY(i);
      colors[(vertexBase + i) * 3 + 2] = color.getZ(i);
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
