const TERMS = [
  [1.6, 0.02, 0.0, 1.7],
  [1.1, 0.0, 0.017, 0.4],
  [0.45, 0.05, 0.05, 0.0],
  [0.25, 0.09, 0.03, 0.0],
];

const RIVER_SLOPE = 0.55;
const RIVER_OFFSET = 280;
const RIVER_SINES = [
  [60, 0.0018],
  [22, 0.006],
];
const RIVER_WET = 16;
const RIVER_NECK = 1.38;
const RIVER_SURFACE_LIFT = 0.02;

function waves(x, z) {
  let height = 0;
  for (const [a, kx, kz, phase] of TERMS) {
    height += a * Math.sin(kx * x + kz * z + phase);
  }
  return height;
}

function riverCenter(x) {
  let z = RIVER_SLOPE * x + RIVER_OFFSET;
  for (const [amplitude, frequency] of RIVER_SINES) {
    z += amplitude * Math.sin(x * frequency);
  }
  return z;
}

function inGorge(x, z) {
  return x >= 800 && x <= 2000 && z >= 800 && z <= 2000;
}

export function groundHeight(x, z) {
  const base = waves(x, z);
  if (x < -2000 || x > 2000 || z < -2000 || z > 2000) return base;
  const center = riverCenter(x);
  const lateral = Math.abs(z - center);
  if (lateral > RIVER_WET || inGorge(x, center)) return base;
  const profile = 0.5 * (1 + Math.cos(Math.PI * (lateral / RIVER_WET)));
  return waves(x, center) - (RIVER_NECK - RIVER_SURFACE_LIFT) * profile;
}
