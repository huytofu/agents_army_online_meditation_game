const FIRST_PITCH = [-50, 70];
const THIRD_PITCH = [-35, 55];
const LOOK_SPEED = 0.002;

const held = new Set();
let yaw = 0;
let pitch = 0;
let view = "third";
let viewEdge = false;

function pitchLimits() {
  const [minDeg, maxDeg] = view === "first" ? FIRST_PITCH : THIRD_PITCH;
  return [(minDeg * Math.PI) / 180, (maxDeg * Math.PI) / 180];
}

function clampPitch() {
  const [minPitch, maxPitch] = pitchLimits();
  pitch = Math.min(maxPitch, Math.max(minPitch, pitch));
}

export function attachControls(canvas) {
  const enter = document.querySelector("#enter");

  enter.addEventListener("click", () => {
    canvas.requestPointerLock();
  });

  document.addEventListener("pointerlockchange", () => {
    enter.hidden = document.pointerLockElement === canvas;
  });

  document.addEventListener("mousemove", (event) => {
    if (document.pointerLockElement !== canvas) return;
    yaw += event.movementX * LOOK_SPEED;
    pitch -= event.movementY * LOOK_SPEED;
    clampPitch();
  });

  document.addEventListener("keydown", (event) => {
    if (event.code === "KeyV") {
      if (document.pointerLockElement === canvas && !event.repeat) viewEdge = true;
      return;
    }
    held.add(event.code);
  });

  document.addEventListener("keyup", (event) => {
    held.delete(event.code);
  });
}

function axis(negative, positive) {
  return (held.has(positive) ? 1 : 0) - (held.has(negative) ? 1 : 0);
}

export function consume() {
  if (viewEdge) {
    view = view === "first" ? "third" : "first";
    viewEdge = false;
    clampPitch();
  }

  let moveX = axis("KeyA", "KeyD") + axis("ArrowLeft", "ArrowRight");
  let moveZ = axis("KeyW", "KeyS") + axis("ArrowUp", "ArrowDown");
  moveX = Math.min(1, Math.max(-1, moveX));
  moveZ = Math.min(1, Math.max(-1, moveZ));
  const length = Math.hypot(moveX, moveZ);
  if (length > 1) {
    moveX /= length;
    moveZ /= length;
  }
  return { moveX, moveZ, yaw, pitch, view };
}
