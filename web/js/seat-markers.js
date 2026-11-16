import * as THREE from "three";

import { seatMarkerVisible } from "./seat.js";

const FLOAT_HEIGHT = 2.05;

function sitTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 96;
  const context = canvas.getContext("2d");
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "rgba(244, 241, 234, 0.94)";
  context.beginPath();
  context.roundRect(8, 8, 240, 80, 28);
  context.fill();
  context.fillStyle = "#1d3328";
  context.font = "600 54px Palatino, Georgia, serif";
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText("Sit", 128, 50);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function makeMarker(diamondGeometry, diamondMaterial, outlineMaterial, labelMaterial) {
  const group = new THREE.Group();
  const diamond = new THREE.Mesh(diamondGeometry, diamondMaterial);
  diamond.scale.set(1, 1.45, 1);
  const outline = new THREE.Mesh(diamondGeometry, outlineMaterial);
  outline.scale.setScalar(1.12);
  diamond.add(outline);
  const label = new THREE.Sprite(labelMaterial);
  label.position.y = 0.72;
  label.scale.set(1.35, 0.5, 1);
  group.add(diamond, label);
  return { group, diamond };
}

export function createSeatMarkers(scene) {
  const diamondGeometry = new THREE.OctahedronGeometry(0.22, 0);
  const diamondMaterial = new THREE.MeshBasicMaterial({ color: 0xf4f1ea, fog: false });
  const outlineMaterial = new THREE.MeshBasicMaterial({
    color: 0x1d3328,
    side: THREE.BackSide,
    fog: false,
  });
  const labelMaterial = new THREE.SpriteMaterial({
    map: sitTexture(),
    transparent: true,
    depthWrite: false,
    fog: false,
  });
  const markers = new Map();

  return {
    update(spots, player, range, time) {
      const wanted = new Set();
      for (const spot of spots) {
        const distance = Math.hypot(spot.x - player.x, spot.z - player.z);
        if (!seatMarkerVisible(distance, range, Boolean(spot.claimed))) continue;
        wanted.add(spot.id);
        let marker = markers.get(spot.id);
        if (!marker) {
          marker = makeMarker(diamondGeometry, diamondMaterial, outlineMaterial, labelMaterial);
          markers.set(spot.id, marker);
          scene.add(marker.group);
        }
        const bob = Math.sin(time * 2.1 + spot.id) * 0.08;
        marker.group.position.set(spot.x, spot.y + FLOAT_HEIGHT + bob, spot.z);
        marker.diamond.rotation.y = time * 0.9;
      }
      for (const [id, marker] of markers) {
        if (wanted.has(id)) continue;
        scene.remove(marker.group);
        markers.delete(id);
      }
    },
  };
}
