import { attachControls, consume, setSeated } from "../js/controls.js";

const listeners = {};
let locked = null;
const enter = {
  hidden: false,
  addEventListener() {},
};
const canvas = {
  locks: 0,
  requestPointerLock() {
    this.locks += 1;
    locked = canvas;
    for (const listener of listeners.pointerlockchange || []) listener();
  },
};
globalThis.document = {
  querySelector(selector) {
    if (selector === "#enter") return enter;
    return null;
  },
  addEventListener(type, listener) {
    (listeners[type] ||= []).push(listener);
  },
  exitPointerLock() {
    locked = null;
    for (const listener of listeners.pointerlockchange || []) listener();
  },
  get pointerLockElement() {
    return locked;
  },
};
globalThis.KeyboardEvent = class KeyboardEvent {
  constructor(type, init = {}) {
    this.type = type;
    this.code = init.code;
    this.repeat = Boolean(init.repeat);
  }
};

attachControls(canvas);
canvas.requestPointerLock();
enter.hidden = true;

let failed = false;
function expect(condition, message) {
  if (!condition) {
    failed = true;
    process.stderr.write(`${message}\n`);
  }
}

try {
  setSeated(true);
  setSeated(false);
} catch (error) {
  expect(false, `standing threw ${error.name}: ${error.message}`);
}

expect(enter.hidden === false, "the enter control stayed hidden after standing, so the player cannot click to walk");
expect(locked === null || locked === canvas, "pointer lock was left in an unexpected state");

document.dispatchEvent?.({ type: "keydown", code: "KeyF", repeat: false });
const keydown = (listeners.keydown || [])[0];
setSeated(true);
canvas.locks = 0;
keydown(new KeyboardEvent("keydown", { code: "KeyF" }));
expect(canvas.locks === 1, "pressing F while seated did not ask for pointer lock in the key gesture");
const sample = consume();
expect(sample.sitPressed === true, "F while seated was not reported as a sit press");

if (failed) process.exit(1);
process.stdout.write("controls: standing releases the cushion\n");
