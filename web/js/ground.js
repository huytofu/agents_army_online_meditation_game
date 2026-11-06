const TERMS = [
  [1.6, 0.02, 0.0, 1.7],
  [1.1, 0.0, 0.017, 0.4],
  [0.45, 0.05, 0.05, 0.0],
  [0.25, 0.09, 0.03, 0.0],
];

export function groundHeight(x, z) {
  let height = 0;
  for (const [a, kx, kz, phase] of TERMS) {
    height += a * Math.sin(kx * x + kz * z + phase);
  }
  return height;
}
