import { readFileSync } from "node:fs";

import { SEAT_BACK, SEAT_EYE, seatBlend, seatMarkerVisible, seatOffset } from "../js/seat.js";

let failed = false;
function expect(condition, message) {
  if (!condition) {
    failed = true;
    process.stderr.write(`${message}\n`);
  }
}

const offset = seatOffset(0);
const back = Math.hypot(offset.x, offset.z);
expect(SEAT_EYE >= 1.68 && SEAT_EYE <= 1.9, `seated eye ${SEAT_EYE} should sit just above the old 1.5 m view`);
expect(offset.y === SEAT_EYE, "seatOffset did not use the seated eye height");
expect(back >= 0.75, `viewpoint is ${back.toFixed(2)} m from the cushion center, inside the seat`);
expect(seatBlend(0) === 0, "blend should start at 0");
expect(Math.abs(seatBlend(400) - 0.5) < 1e-9, "400 ms should be halfway through the 800 ms sit");
expect(seatBlend(1500) === 1, "a slow 1500 ms frame must finish the sit instead of advancing 50 ms");
expect(seatMarkerVisible(4, 2.5, false) === true, "a cushion farther than the sit key should show a marker");
expect(seatMarkerVisible(2.5, 2.5, false) === false, "the marker should hide at the distance where F sits");
expect(seatMarkerVisible(1, 2.5, false) === false, "the marker should hide when someone stands within 1 m");
expect(seatMarkerVisible(4, 2.5, true) === false, "a taken cushion is not seatable");
expect(seatMarkerVisible(2.6, 2.5, false) === true, "the marker should return after the player walks away");
const client = readFileSync(new URL("../js/main.js", import.meta.url), "utf8");
expect(!client.includes("createDiorama"), "sitting must not add a generated scene on the cushion");
expect(!client.includes("setVeil({"), "sitting must not hide the plants already around the cushion");

if (failed) process.exit(1);
process.stdout.write("seat: viewpoint clears the cushion and the sit finishes on the clock\n");
