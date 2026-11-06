import * as THREE from "three";

import { createAvatar } from "./avatar.js";
import { createChunkWorld } from "./chunks.js";
import { attachControls, consume, onEnter, setSeated } from "./controls.js";
import { createDiorama } from "./diorama.js";
import { groundHeight } from "./ground.js";
import { biomeAt, loadMeta, paletteOf } from "./meta.js";
import { createMinimap } from "./minimap.js";
import { createYoutubePanel } from "./youtube.js";

const MAX_SPEED = 3.2;
const EYE_HEIGHT = 1.55;
const THIRD_DISTANCE = 4.2;
const THIRD_HEIGHT = 1.8;
const CHEST_HEIGHT = 1.15;
const SPAWN_X = -24;
const SPAWN_Z = 0;
const WALK_CYCLE_SPEED = 0.15;
const SIT_RANGE = 2.5;
const TARGET_ACQUIRE = (10 * Math.PI) / 180;
const TARGET_HOLD = (18 * Math.PI) / 180;
const SEAT_PITCH = (-4 * Math.PI) / 180;

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
let avatarSeated = false;
let walkLimit = 1996;
let meta = null;
let world = null;
let minimap = null;
let biome = "moss_plain";
let blend = 1;
let fromFog = new THREE.Color(0xd5e2d2);
let toFog = fromFog.clone();
let fromSun = new THREE.Color(0xffe0b0);
let toSun = fromSun.clone();
let fromDensity = 0.018;
let toDensity = 0.018;
let token = localStorage.getItem("forest_token");
let sitting = false;
let seat = null;
let target = null;
let diorama = null;
let sitBlend = 1;
let sitFrom = new THREE.Vector3();
let poseClock = 0;
let showVideo = 0;

const ring = new THREE.Mesh(
  new THREE.RingGeometry(0.55, 0.72, 28),
  new THREE.MeshBasicMaterial({ color: 0xf4f1ea, side: THREE.DoubleSide, transparent: true, opacity: 0.9 }),
);
ring.rotation.x = -Math.PI / 2;
ring.visible = false;
scene.add(ring);

const youtube = createYoutubePanel(async (videoId) => {
  if (!token) return false;
  const body = await postJson("/api/session/youtube", { token, video_id: videoId });
  return Boolean(body.ok);
});

attachControls(canvas);
onEnter(() => {
  void resumeSession();
});
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
  if (sitting && seat) {
    world.markClaimed(seat.spot_id, true);
    world.setVeil({ x, z, radius: 25, keepX: x, keepZ: z });
  }
  minimap = createMinimap(meta);
  minimap.update(x, z, yaw);
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
  const input = consume();
  if (input.sitPressed) void pressSit();
  if (!sitting && document.pointerLockElement === canvas) {
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
    poseClock += dt;
    if (token && poseClock >= 2) {
      poseClock = 0;
      void postPose();
    }
  }
  if (showVideo > 0) {
    showVideo = Math.max(0, showVideo - dt);
    if (showVideo === 0 && sitting) youtube.show();
  }
  if (meta) settleLight(dt);
  if (world) {
    world.update(x, z);
    world.animate(clock.elapsedTime);
    if (!sitting) aimRing();
  }
  if (diorama) diorama.update(performance.now() / 1000);
  avatar.object.position.set(x, y, z);
  avatar.object.rotation.y = yaw;
  if (sitting !== avatarSeated) {
    avatarSeated = sitting;
    avatar.setSeated(sitting);
  }
  if (minimap) minimap.update(x, z, yaw);
  placeCamera(dt);
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

function placeCamera(dt) {
  if (sitting) {
    const seatedYaw = yaw + ((1.5 * Math.PI) / 180) * Math.sin(clock.elapsedTime / 12);
    const eye = new THREE.Vector3(x, y + 1.15, z);
    const look = new THREE.Vector3(
      x + Math.sin(seatedYaw) * Math.cos(SEAT_PITCH),
      y + 1.15 + Math.sin(SEAT_PITCH),
      z + Math.cos(seatedYaw) * Math.cos(SEAT_PITCH),
    );
    avatar.object.visible = false;
    if (sitBlend < 1) {
      sitBlend = Math.min(1, sitBlend + dt / 0.8);
      camera.position.lerpVectors(sitFrom, eye, sitBlend);
      camera.lookAt(look);
      return;
    }
    camera.position.copy(eye);
    camera.lookAt(look);
    return;
  }
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

function lookAtSpot(spot) {
  const dx = spot.x - x;
  const dz = spot.z - z;
  const dist = Math.hypot(dx, dz);
  const facing = dist === 0 ? 1 : (dx * Math.sin(yaw) + dz * Math.cos(yaw)) / dist;
  return { dist, angle: Math.acos(Math.min(1, Math.max(-1, facing))) };
}

function aimRing() {
  const spots = world.spots().filter((spot) => !spot.claimed);
  if (target) {
    const still = spots.find((spot) => spot.id === target.id);
    if (!still) target = null;
    else {
      const glance = lookAtSpot(still);
      target = glance.dist <= 14 && glance.angle <= TARGET_HOLD ? still : null;
    }
  }
  if (!target) {
    let best = null;
    let bestDist = Infinity;
    for (const spot of spots) {
      const glance = lookAtSpot(spot);
      if (glance.dist <= 12 && glance.angle <= TARGET_ACQUIRE && glance.dist < bestDist) {
        best = spot;
        bestDist = glance.dist;
      }
    }
    target = best;
  }
  ring.visible = Boolean(target);
  if (target) ring.position.set(target.x, target.y + 0.08, target.z);
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) return { ok: false, reason: "missing" };
  return response.json();
}

async function postPose() {
  if (!token || sitting) return;
  await postJson("/api/pose", { token, x, y, z, yaw, pitch });
}

async function resumeSession() {
  const opened = await postJson("/api/session", { token });
  if (!opened.token) return;
  token = opened.token;
  localStorage.setItem("forest_token", token);
  avatar.setColor(opened.color);
  youtube.setDraft(opened.youtube_video_id);
  if (opened.pose?.mode === "sit" && opened.pose.spot_id) {
    await beginSit(opened.pose, true);
  }
}

async function pressSit() {
  if (sitting) {
    await standUp();
    return;
  }
  if (!token || !target || lookAtSpot(target).dist > SIT_RANGE) return;
  await postPose();
  const result = await postJson("/api/sit", { token, spot_id: target.id });
  if (!result.ok) {
    if (result.reason === "taken" && world) world.markClaimed(target.id, true);
    target = null;
    ring.visible = false;
    return;
  }
  await beginSit(result.pose, false);
}

async function beginSit(pose, resumed) {
  sitting = true;
  seat = pose;
  x = pose.x;
  y = pose.y;
  z = pose.z;
  yaw = pose.yaw;
  setSeated(true);
  ring.visible = false;
  target = null;
  if (world) {
    world.markClaimed(pose.spot_id, true);
    world.setVeil({ x, z, radius: 25, keepX: x, keepZ: z });
    world.update(x, z);
  }
  sitFrom.copy(camera.position);
  sitBlend = resumed ? 1 : 0;
  const recipe = await fetch(`/api/world/spots/${pose.spot_id}/recipe`);
  if (recipe.ok) {
    const body = await recipe.json();
    if (diorama) diorama.dispose();
    diorama = await createDiorama(
      { id: body.spot_id, x: pose.x, z: pose.z, yaw: body.yaw },
      body.blocks,
    );
    scene.add(diorama.object);
    diorama.update(performance.now() / 1000);
  }
  showVideo = 1.2;
}

async function standUp() {
  if (!token) return;
  const result = await postJson("/api/stand", { token });
  if (diorama) diorama.dispose();
  diorama = null;
  youtube.hide();
  showVideo = 0;
  sitting = false;
  if (world && seat) world.markClaimed(seat.spot_id, false);
  seat = null;
  if (world) world.setVeil(null);
  setSeated(false);
  if (result.ok) {
    x = result.pose.x;
    y = result.pose.y;
    z = result.pose.z;
  }
  y = groundHeight(x, z);
}
