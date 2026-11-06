import { GLTFLoader } from "../../vendor/loaders/GLTFLoader.js";

const loader = new GLTFLoader();
const cache = new Map();
let manifestPromise;

function manifest() {
  if (!manifestPromise) {
    manifestPromise = fetch("/assets/manifest.json")
      .then(async (response) => {
        if (!response.ok) return { kits: [], landmarks: [] };
        const text = await response.text();
        const stripped = text
          .split("\n")
          .map((line) => line.replace(/\/\/.*$/, ""))
          .join("\n");
        return JSON.parse(stripped);
      })
      .catch(() => ({ kits: [], landmarks: [] }));
  }
  return manifestPromise;
}

function parse(buffer, path) {
  return new Promise((resolve, reject) => {
    loader.parse(buffer, path, resolve, reject);
  });
}

export async function loadCatalogGltf(kind, name) {
  const data = await manifest();
  const names = kind === "landmarks" ? data.landmarks : data.kits;
  if (!names.includes(name)) return null;
  return loadOptionalGltf(`/assets/${kind}/${name}.glb?v=4`);
}

function loadOptionalGltf(url) {
  if (cache.has(url)) return cache.get(url);
  const pending = fetch(url).then(async (response) => {
    if (!response.ok) return null;
    const buffer = await response.arrayBuffer();
    return parse(buffer, url.slice(0, url.lastIndexOf("/") + 1));
  }).catch(() => null);
  cache.set(url, pending);
  return pending;
}
