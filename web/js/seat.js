export const SEAT_EYE = 1.72;
export const SEAT_BACK = 0.85;
export const SEAT_PITCH = (-6 * Math.PI) / 180;
export const SEAT_BLEND_MS = 800;

export function seatOffset(yaw) {
  return {
    x: -Math.sin(yaw) * SEAT_BACK,
    y: SEAT_EYE,
    z: -Math.cos(yaw) * SEAT_BACK,
    pitch: SEAT_PITCH,
  };
}

export function seatBlend(elapsedMs) {
  if (elapsedMs <= 0) return 0;
  return Math.min(1, elapsedMs / SEAT_BLEND_MS);
}

export function seatMarkerVisible(distance, range, claimed) {
  return !claimed && distance > range;
}
