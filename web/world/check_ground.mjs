import { groundHeight } from "../js/ground.js";

const points = [
  [0, 0],
  [10, -4],
  [-80, 120],
  [199, 199],
];

const heights = {};
for (const [x, z] of points) {
  heights[`${x},${z}`] = groundHeight(x, z);
}

process.stdout.write(`${JSON.stringify(heights)}\n`);
