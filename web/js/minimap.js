import { biomeAt, riverZ } from "./meta.js";

const SIZE = 320;
const PAD = 16;
const FACING = [
  "north",
  "northeast",
  "east",
  "southeast",
  "south",
  "southwest",
  "west",
  "northwest",
];

const LANDMARK_LABELS = {
  great_fall: "Fall",
  cathedral_heart: "Heart",
  spore_well: "Spore",
  bloom_ridge: "Ridge",
  pitcher_throne: "Throne",
  lantern_monarch: "Monarch",
  mirror_pan: "Mirror",
  heron_bend: "Heron",
  vine_gate: "Gate",
  amber_circle: "Circle",
  fern_nave: "Nave",
  sundew_jewel: "Jewel",
};

const BIOME_LABELS = {
  moss_plain: "Moss",
  cathedral_trees: "Cathedral",
  waterfall_gorge: "Gorge",
  valley_bloom: "Bloom",
  strange_fauna: "Fauna",
  carnivorous_bog: "Bog",
  lantern_orchard: "Lanterns",
  fern_sea: "Ferns",
  hanging_vines: "Vines",
  amber_herd: "Amber",
  salt_mirror: "Salt",
};

export function project(meta, x, z, size = SIZE, pad = PAD) {
  const inner = size - pad * 2;
  const scale = inner / (meta.world_max - meta.world_min);
  return [
    pad + (x - meta.world_min) * scale,
    pad + (meta.world_max - z) * scale,
  ];
}

const COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];

function facingIndex(yaw) {
  const turn = Math.PI * 2;
  const wrapped = ((yaw % turn) + turn) % turn;
  return Math.round(wrapped / (Math.PI / 4)) % 8;
}

export function facingName(yaw) {
  return FACING[facingIndex(yaw)];
}

export function compassCode(yaw) {
  return COMPASS[facingIndex(yaw)];
}

export function travelHeading(fromX, fromZ, toX, toZ) {
  return facingName(Math.atan2(toX - fromX, toZ - fromZ));
}

export function formatDistance(meters) {
  if (meters >= 1000) return `${(meters / 1000).toFixed(1)} km`;
  return `${Math.round(meters)} m`;
}

function title(name) {
  return name
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function inkColor(hex) {
  const red = Number.parseInt(hex.slice(1, 3), 16);
  const green = Number.parseInt(hex.slice(3, 5), 16);
  const blue = Number.parseInt(hex.slice(5, 7), 16);
  return red * 0.299 + green * 0.587 + blue * 0.114 > 150 ? "#1d3328" : "#f4f1ea";
}

function drawPlate(ink, meta) {
  const span = meta.world_max - meta.world_min;
  const inner = SIZE - PAD * 2;
  const metersToPixels = inner / span;
  const regionLabels = [];
  ink.clearRect(0, 0, SIZE, SIZE);
  ink.fillStyle = "#24352c";
  ink.fillRect(0, 0, SIZE, SIZE);

  for (const band of meta.bands) {
    for (const column of band.columns) {
      const [left, bottom] = project(meta, column.x_min, band.z_min);
      const [right, top] = project(meta, column.x_max, band.z_max);
      const x = Math.min(left, right);
      const y = Math.min(top, bottom);
      const width = Math.abs(right - left);
      const height = Math.abs(bottom - top);
      const color = meta.palettes[column.name]?.map || "#6f8f62";
      ink.fillStyle = color;
      ink.fillRect(x, y, width, height);
      regionLabels.push({
        name: column.name,
        color,
        x: x + width / 2,
        y: y + height / 2,
        width,
        height,
      });
    }
  }

  ink.save();
  ink.beginPath();
  ink.rect(PAD, PAD, inner, inner);
  ink.clip();
  ink.strokeStyle = meta.palettes.river?.map || "#7eb8c4";
  ink.lineWidth = Math.max(3, meta.river.corridor * 2 * metersToPixels);
  ink.lineJoin = "round";
  ink.lineCap = "round";
  ink.beginPath();
  const step = 40;
  for (let x = meta.world_min; x <= meta.world_max; x += step) {
    const [px, py] = project(meta, x, riverZ(meta, x));
    if (x === meta.world_min) ink.moveTo(px, py);
    else ink.lineTo(px, py);
  }
  ink.stroke();
  ink.restore();

  const gatherings = meta.seat_fields || [];
  for (const field of gatherings) {
    const [px, py] = project(meta, field.x, field.z);
    const radius = Math.max(6, field.radius * metersToPixels);
    ink.beginPath();
    ink.arc(px, py, radius, 0, Math.PI * 2);
    ink.strokeStyle = "rgba(244, 241, 234, 0.95)";
    ink.lineWidth = 1.5;
    ink.stroke();
  }

  const landmarkPoints = meta.landmarks.map((landmark) => project(meta, landmark.x, landmark.z));
  ink.font = "12px Palatino, Georgia, serif";
  ink.textAlign = "center";
  ink.textBaseline = "middle";
  for (const label of regionLabels) {
    const covered = landmarkPoints.some(([px, py]) => Math.hypot(px - label.x, py - label.y) < 12);
    const text = BIOME_LABELS[label.name] || title(label.name);
    if (covered || ink.measureText(text).width >= label.width - 8 || label.height <= 16) continue;
    ink.fillStyle = inkColor(label.color);
    ink.fillText(text, label.x, label.y);
  }

  ink.strokeStyle = "rgba(29, 51, 40, 0.55)";
  ink.lineWidth = 2;
  ink.strokeRect(PAD, PAD, inner, inner);
  ink.fillStyle = "#f4f1ea";
  ink.font = "12px Palatino, Georgia, serif";
  ink.textAlign = "center";
  ink.textBaseline = "middle";
  ink.fillText("N", SIZE / 2, PAD / 2);

  ink.font = "11px Palatino, Georgia, serif";
  ink.textAlign = "left";
  ink.textBaseline = "top";
  const labels = [
    ...gatherings.map((field) => {
      const [px, py] = project(meta, field.x, field.z);
      const text = BIOME_LABELS[field.name] || title(field.name);
      const width = ink.measureText(text).width + 8;
      const height = 14;
      return { px, py, text, w: width, h: height, x: px - width / 2, y: py - height - 8, kind: "field" };
    }),
    ...meta.landmarks.map((landmark) => {
      const [px, py] = project(meta, landmark.x, landmark.z);
      const text = LANDMARK_LABELS[landmark.name] || title(landmark.name);
      const width = ink.measureText(text).width + 8;
      const height = 14;
      return { px, py, text, w: width, h: height, x: px - width / 2, y: py - height - 7, kind: "landmark" };
    }),
  ];
  separateLabels(labels);
  for (const label of labels) {
    ink.strokeStyle = "rgba(246, 231, 168, 0.9)";
    ink.lineWidth = 1;
    ink.beginPath();
    ink.moveTo(label.px, label.py);
    ink.lineTo(label.x + label.w / 2, label.y + label.h / 2);
    ink.stroke();
    if (label.kind === "field") {
      ink.fillStyle = "#f4f1ea";
      ink.beginPath();
      ink.arc(label.px, label.py, 3.2, 0, Math.PI * 2);
      ink.fill();
    } else {
      ink.fillStyle = "#1d3328";
      ink.beginPath();
      ink.arc(label.px, label.py, 4.5, 0, Math.PI * 2);
      ink.fill();
      ink.fillStyle = "#f6e7a8";
      ink.beginPath();
      ink.arc(label.px, label.py, 2.6, 0, Math.PI * 2);
      ink.fill();
    }
    ink.fillStyle = "rgba(29, 51, 40, 0.88)";
    ink.fillRect(label.x, label.y, label.w, label.h);
    ink.fillStyle = "#f4f1ea";
    ink.fillText(label.text, label.x + 4, label.y + 1);
  }
}

function separateLabels(labels) {
  for (let pass = 0; pass < 40; pass += 1) {
    let moved = false;
    for (let i = 0; i < labels.length; i += 1) {
      for (let j = i + 1; j < labels.length; j += 1) {
        const a = labels[i];
        const b = labels[j];
        const overlapX = (a.w + b.w) / 2 + 3 - Math.abs(a.x + a.w / 2 - (b.x + b.w / 2));
        const overlapY = (a.h + b.h) / 2 + 2 - Math.abs(a.y + a.h / 2 - (b.y + b.h / 2));
        if (overlapX <= 0 || overlapY <= 0) continue;
        const gapX = a.x + a.w / 2 - (b.x + b.w / 2);
        const gapY = a.y + a.h / 2 - (b.y + b.h / 2);
        if (overlapX < overlapY) {
          const push = overlapX / 2 + 0.4;
          const sign = gapX < 0 ? -1 : 1;
          a.x += sign * push;
          b.x -= sign * push;
        } else {
          const push = overlapY / 2 + 0.4;
          const sign = gapY < 0 ? -1 : 1;
          a.y += sign * push;
          b.y -= sign * push;
        }
        moved = true;
      }
    }
    if (!moved) break;
  }
  for (const label of labels) {
    label.x = Math.min(SIZE - PAD - label.w, Math.max(PAD, label.x));
    label.y = Math.min(SIZE - PAD - label.h, Math.max(PAD, label.y));
  }
}

function drawYou(view, meta, x, z, yaw) {
  const [px, py] = project(meta, x, z);
  view.save();
  view.translate(px, py);
  view.rotate(yaw);
  view.beginPath();
  view.moveTo(0, -8);
  view.lineTo(5, 6);
  view.lineTo(0, 2.5);
  view.lineTo(-5, 6);
  view.closePath();
  view.fillStyle = "#fffef8";
  view.strokeStyle = "#1d3328";
  view.lineWidth = 2;
  view.fill();
  view.stroke();
  view.restore();
}

export function createMinimap(meta) {
  const canvas = document.querySelector("#minimap-view");
  const key = document.querySelector("#minimap-key");
  const here = document.createElement("strong");
  const place = document.createElement("span");
  const gatherings = document.createElement("ul");
  const list = document.createElement("ul");
  const fieldRows = [...(meta.seat_fields || [])].map((field) => {
    const item = document.createElement("li");
    gatherings.append(item);
    return { field, item };
  });
  const rows = [...meta.landmarks]
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((landmark) => {
      const item = document.createElement("li");
      list.append(item);
      return { landmark, item };
    });
  key.replaceChildren(here, place, gatherings, list);

  const plate = document.createElement("canvas");
  plate.width = SIZE;
  plate.height = SIZE;
  drawPlate(plate.getContext("2d"), meta);

  const view = canvas.getContext("2d");
  const scale = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = SIZE * scale;
  canvas.height = SIZE * scale;

  return {
    update(x, z, yaw) {
      view.setTransform(scale, 0, 0, scale, 0, 0);
      view.clearRect(0, 0, SIZE, SIZE);
      view.drawImage(plate, 0, 0);
      drawYou(view, meta, x, z, yaw);
      const biome = biomeAt(meta, x, z);
      here.textContent = `${Math.round(x)} m, ${Math.round(z)} m`;
      place.textContent = `${title(biome || "forest")} · facing ${facingName(yaw)}`;
      for (const row of fieldRows) {
        const meters = Math.hypot(row.field.x - x, row.field.z - z);
        const label = BIOME_LABELS[row.field.name] || title(row.field.name);
        if (meters < 50) {
          row.item.textContent = `${label} · around you`;
          continue;
        }
        const heading = compassCode(Math.atan2(row.field.x - x, row.field.z - z));
        row.item.textContent = `${label} · ${heading} · ${formatDistance(meters)}`;
      }
      for (const row of rows) {
        const meters = Math.hypot(row.landmark.x - x, row.landmark.z - z);
        const heading = compassCode(Math.atan2(row.landmark.x - x, row.landmark.z - z));
        row.item.textContent = `${title(row.landmark.name)} · ${heading} · ${formatDistance(meters)}`;
      }
    },
  };
}
