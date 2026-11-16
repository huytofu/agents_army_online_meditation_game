export async function loadMeta() {
  const response = await fetch("/api/world/meta");
  if (!response.ok) throw new Error("world meta failed");
  return response.json();
}

export function riverZ(meta, x) {
  const river = meta.river;
  let z = river.slope * x + river.offset;
  for (const [amplitude, frequency] of river.sines) {
    z += amplitude * Math.sin(x * frequency);
  }
  return z;
}

function inRange(value, low, high, highInclusive) {
  if (value < low) return false;
  return highInclusive ? value <= high : value < high;
}

export function rectangleBiome(meta, x, z) {
  for (const band of meta.bands) {
    if (!inRange(z, band.z_min, band.z_max, band.z_max_inclusive)) continue;
    for (const column of band.columns) {
      if (inRange(x, column.x_min, column.x_max, column.x_max_inclusive)) return column.name;
    }
  }
  return null;
}

export function biomeAt(meta, x, z) {
  const base = rectangleBiome(meta, x, z);
  if (!base) return null;
  const distance = Math.abs(z - riverZ(meta, x));
  if (base === "waterfall_gorge" && distance <= meta.river.gorge_keep) return "waterfall_gorge";
  if (distance < meta.river.corridor) return "river";
  return base;
}

export function chunkIndex(meta, value) {
  return Math.floor((value - meta.world_min) / meta.chunk_size);
}

export function paletteOf(meta, biome) {
  return meta.palettes[biome] || meta.palettes.moss_plain;
}
