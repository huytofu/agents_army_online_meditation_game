import * as THREE from "three";

import { createAvatar } from "./avatar.js";
import { attachControls, consume } from "./controls.js";
import { groundHeight } from "./ground.js";
import { makeKit } from "./kits/index.js";
import { fog, ground, sun } from "./kits/materials.js";

const MAX_SPEED = 3.2;
const EYE_HEIGHT = 1.55;
const THIRD_DISTANCE = 4.2;
const THIRD_HEIGHT = 1.8;
const CHEST_HEIGHT = 1.15;
const SPAWN_X = -24;
const SPAWN_Z = 0;
const PLANE_LIMIT = 48;
const WORLD_LIMIT = 196;
const WALK_CYCLE_SPEED = 0.15;

const canvas = document.querySelector("#view");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);

const scene = new THREE.Scene();
scene.background = new THREE.Color(fog);
scene.fog = new THREE.FogExp2(fog, 0.018);

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 220);

scene.add(new THREE.HemisphereLight(sun, 0x3e6b45, 0.72));
const sunLight = new THREE.DirectionalLight(sun, 1.2);
sunLight.position.set(-28, 48, 16);
scene.add(sunLight);

scene.add(buildGround());
placeGrove();

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

attachControls(canvas);
window.addEventListener("resize", resize);

const clock = new THREE.Clock();
renderer.setAnimationLoop(frame);

function buildGround() {
  const geometry = new THREE.PlaneGeometry(PLANE_LIMIT * 2, PLANE_LIMIT * 2, 64, 64);
  geometry.rotateX(-Math.PI / 2);
  const positions = geometry.attributes.position;
  for (let i = 0; i < positions.count; i += 1) {
    const vx = positions.getX(i);
    const vz = positions.getZ(i);
    positions.setY(i, groundHeight(vx, vz));
  }
  geometry.computeVertexNormals();
  return new THREE.Mesh(geometry, ground);
}

function placeGrove() {
  const props = [
    ["tree", -12, 18, 1.6, 0.4],
    ["tree", -38, 8, 1.6, 1.1],
    ["moss_mound", -30, 4, 1, 0],
    ["moss_mound", -28, 11, 0.85, 0.3],
    ["moss_mound", -18, 12, 1.15, 1],
    ["moss_mound", -14, 5, 0.9, 0.2],
    ["moss_mound", -17, -9, 1.2, 0.6],
    ["moss_mound", -27, -13, 1, 0.8],
    ["moss_mound", -35, -3, 0.8, 0.1],
    ["moss_mound", -37, 9, 1.1, 1.4],
    ["moss_mound", -12, 18, 0.95, 0.5],
    ["moss_mound", -8, 1, 1.05, 2],
    ["moss_mound", -33, 17, 1.25, 0.7],
    ["moss_mound", -21, 20, 0.88, 1.2],
    ["mushroom", -21, 4, 1, 0.4],
    ["mushroom", -27, 3, 0.9, 1.2],
    ["mushroom", -19, -4, 1.1, 2.1],
    ["mushroom", -30, -6, 1, 0.6],
    ["mushroom", -23, 9, 0.85, 1.7],
    ["mushroom", -15, -2, 1.15, 0.2],
    ["mushroom", -34, 2, 1, 2.4],
    ["mushroom", -14, 11, 0.8, 0.9],
    ["mushroom", -32, 13, 1.05, 1.5],
    ["mushroom", -26, -9, 1.2, 0.3],
    ["mushroom", -11, 8, 0.95, 2.2],
    ["mushroom", -36, -9, 1, 1.1],
    ["mushroom", -17, 17, 0.9, 0.8],
    ["mushroom", -29, 19, 1.1, 1.9],
    ["fern", -20, 2, 1, 0.2],
    ["fern", -26, 7, 1, 1],
    ["fern", -22, -5, 1, 0.5],
    ["fern", -31, 0, 1,1, 1.4],
    ["fern", -16, 8, 0.9, 0.7],
    ["fern", -35, 6, 1, 2],
    ["fern", -24, 11, 1, 0.4],
    ["fern", -12, -3, 1.05, 1.6],
    ["fern", -38, 2, 1, 0.9],
    ["fern", -18, 15, 0.95, 1.3],
    ["fern", -30, 15, 1, 0.1],
    ["fern", -33, -11, 1.1, 2.3],
  ];

  for (const [name, px, pz, scale, rot] of props) {
    const kit = makeKit(name);
    kit.scale.setScalar(scale);
    kit.position.set(px, groundHeight(px, pz), pz);
    kit.rotation.y = rot;
    scene.add(kit);
  }
}

function clampAxis(value) {
  const onPlane = Math.min(PLANE_LIMIT, Math.max(-PLANE_LIMIT, value));
  return Math.min(WORLD_LIMIT, Math.max(-WORLD_LIMIT, onPlane));
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

  avatar.object.position.set(x, y, z);
  avatar.object.rotation.y = yaw;
  placeCamera();
  renderer.render(scene, camera);
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
