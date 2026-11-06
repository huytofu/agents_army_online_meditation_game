import * as THREE from "three";

import { createAvatar } from "./avatar.js";
import { createChunkWorld } from "./chunks.js";
import { attachControls, consume } from "./controls.js";
import { groundHeight } from "./ground.js";
import { biomeAt, loadMeta, paletteOf } from "./meta.js";

const MAX_SPEED = 3.2;
const EYE_HEIGHT = 1.55;
const THIRD_DISTANCE = 4.2;
const THIRD_HEIGHT = 1.8;
const CHEST_HEIGHT = 1.15;
const SPAWN_X = -24;
const SPAWN_Z = 0;
const WALK_CYCLE_SPEED = 0.15;

const canvas = document.querySelector("#view");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xd5e2d2);
scene.fog = new THREE.FogExp2(0xd5e2d2, 0.018);

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 600);
scene.add(new THREE.HemisphereLight(0xffe0b0, 0x3e6b45, 0.72));
const sunLight = new THREE.DirectionalLight(0xffe0b0, 1.2);
sunLight.position.set(-28, 48, 16);
scene.add(sunLight);

const avatar = createAvatar();
avatar.setSeated(false);
scene.add(avatar.object);

let x = SPAWN_X;
let z = SPAWN_Z;
let y = groundHeight(x, z);
let yaw = 0;
let pitch = 0;
let view = "third";
let walkPhase = 0;
let walkLimit = 1996;
let meta = null;
let world = null;
let biome = "moss_plain";
let blend = 1;
let fromFog = new THREE.Color(0xd5e2d2);
let toFog = fromFog.clone();
let fromSun = new THREE.Color(0xffe0b0);
let toSun = fromSun.clone();
let fromDensity = 0.018;
let toDensity = 0.018;

attachControls(canvas);
window.addEventListener("resize", resize);
loadMeta().then((payload) => {
  meta = payload;
  walkLimit = payload.walk_limit;
  world = createChunkWorld(scene, meta);
  const first = biomeAt(meta, x, z) || "moss_plain";
  const colors = paletteOf(meta, first);
  fromFog = new THREE.Color(colors.fog);
  toFog = fromFog.clone();
  fromSun = new THREE.Color(colors.sun);
  toSun = fromSun.clone();
  fromDensity = colors.fog_density;
  toDensity = colors.fog_density;
  biome = first;
  scene.fog.color.copy(fromFog);
  scene.background.copy(fromFog);
  scene.fog.density = fromDensity;
  world.update(x, z);
});

const clock = new THREE.Clock();
renderer.setAnimationLoop(frame);

function clampAxis(value) {
  return Math.min(walkLimit, Math.max(-walkLimit, value));
}

function resize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function frame() {
  const dt = Math.min(clock.getDelta(), 0.05);
  if (document.pointerLockElement === canvas) {
    const input = consume();
    yaw = input.yaw;
    pitch = input.pitch;
    view = input.view;
    const forwardX = Math.sin(yaw);
    const forwardZ = Math.cos(yaw);
    const rightX = Math.cos(yaw);
    const rightZ = -Math.sin(yaw);
    const velocityX = (rightX * input.moveX + forwardX * input.moveZ) * MAX_SPEED;
    const velocityZ = (rightZ * input.moveX + forwardZ * input.moveZ) * MAX_SPEED;
    x = clampAxis(x + velocityX * dt);
    z = clampAxis(z + velocityZ * dt);
    y = groundHeight(x, z);
    const speed = Math.hypot(velocityX, velocityZ);
    if (speed > WALK_CYCLE_SPEED) {
      walkPhase += dt * 9;
      avatar.setWalkPhase(walkPhase);
    } else {
      avatar.setWalkPhase(0);
    }
  }
  if (meta) settleLight(dt);
  if (world) {
    world.update(x, z);
    world.animate(clock.elapsedTime);
  }
  avatar.object.position.set(x, y, z);
  avatar.object.rotation.y = yaw;
  placeCamera();
  renderer.render(scene, camera);
}

function settleLight(dt) {
  const next = biomeAt(meta, x, z) || biome;
  if (next !== biome) {
    fromFog.copy(scene.fog.color);
    fromSun.copy(sunLight.color);
    fromDensity = scene.fog.density;
    const colors = paletteOf(meta, next);
    toFog = new THREE.Color(colors.fog);
    toSun = new THREE.Color(colors.sun);
    toDensity = colors.fog_density;
    if (colors.clear) scene.background = new THREE.Color(colors.clear);
    blend = 0;
    biome = next;
  }
  if (blend < 1) {
    blend = Math.min(1, blend + dt / 1.2);
    scene.fog.color.copy(fromFog).lerp(toFog, blend);
    sunLight.color.copy(fromSun).lerp(toSun, blend);
    if (!paletteOf(meta, biome).clear) scene.background.copy(scene.fog.color);
  }
  const baseDensity = fromDensity + (toDensity - fromDensity) * blend;
  const border = [12, -12].some((offset) => {
    return biomeAt(meta, x + offset, z) !== biome || biomeAt(meta, x, z + offset) !== biome;
  });
  scene.fog.density = baseDensity + (border ? 0.01 : 0);
}

function placeCamera() {
  if (view === "first") {
    avatar.object.visible = false;
    camera.position.set(x, y + EYE_HEIGHT, z);
    camera.lookAt(
      x + Math.sin(yaw) * Math.cos(pitch),
      y + EYE_HEIGHT + Math.sin(pitch),
      z + Math.cos(yaw) * Math.cos(pitch),
    );
    return;
  }
  avatar.object.visible = true;
  camera.position.set(
    x - Math.sin(yaw) * THIRD_DISTANCE,
    y + THIRD_HEIGHT,
    z - Math.cos(yaw) * THIRD_DISTANCE,
  );
  camera.lookAt(
    x + Math.sin(yaw) * Math.cos(pitch),
    y + CHEST_HEIGHT + Math.sin(pitch),
    z + Math.cos(yaw) * Math.cos(pitch),
  );
}
