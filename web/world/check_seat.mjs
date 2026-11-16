import { SEAT_BACK, SEAT_EYE, seatBlend, seatOffset } from "../js/seat.js";

let failed = false;
function expect(condition, message) {
  if (!condition) {
    failed = true;
    process.stderr.write(`${message}\n`);
  }
}

const offset = seatOffset(0);
const back = Math.hypot(offset.x, offset.z);
expect(SEAT_EYE >= 1.45, `seated eye ${SEAT_EYE} is still down at the cushion`);
expect(offset.y === SEAT_EYE, "seatOffset did not use the seated eye height");
expect(back >= 0.75, `viewpoint is ${back.toFixed(2)} m from the cushion center, inside the seat`);
expect(seatBlend(0) === 0, "blend should start at 0");
expect(Math.abs(seatBlend(400) - 0.5) < 1e-9, "400 ms should be halfway through the 800 ms sit");
expect(seatBlend(1500) === 1, "a slow 1500 ms frame must finish the sit instead of advancing 50 ms");

if (failed) process.exit(1);
process.stdout.write("seat: viewpoint clears the cushion and the sit finishes on the clock\n");
