import { readFileSync } from "node:fs";

import { bindPanelGroup, bindPanelToggle, setPanelOpen } from "../js/hud.js";

function control() {
  const listeners = {};
  const attrs = {};
  return {
    hidden: false,
    setAttribute(name, value) {
      attrs[name] = String(value);
    },
    getAttribute(name) {
      return Object.hasOwn(attrs, name) ? attrs[name] : null;
    },
    addEventListener(type, listener) {
      (listeners[type] ||= []).push(listener);
    },
    click() {
      for (const listener of listeners.click || []) listener();
    },
  };
}

let failed = false;
function expect(condition, message) {
  if (!condition) {
    failed = true;
    process.stderr.write(`${message}\n`);
  }
}

const button = control();
const panel = control();
setPanelOpen(button, panel, false);
expect(panel.hidden === true, "closing the panel left it visible");
expect(button.getAttribute("aria-expanded") === "false", "a closed panel still announced itself as open");
setPanelOpen(button, panel, true);
expect(panel.hidden === false, "opening the panel left it hidden");
expect(button.getAttribute("aria-expanded") === "true", "an open panel announced itself as closed");

const toggle = control();
const body = control();
toggle.setAttribute("aria-expanded", "true");
bindPanelToggle(toggle, body);
toggle.click();
expect(body.hidden === true, "the icon click did not collapse the panel");
toggle.click();
expect(body.hidden === false, "the icon click did not open the panel again");

const mapButton = control();
const mapPanel = control();
const keysButton = control();
const keysPanel = control();
mapButton.setAttribute("aria-expanded", "true");
mapPanel.hidden = false;
keysButton.setAttribute("aria-expanded", "false");
keysPanel.hidden = true;
bindPanelGroup([
  [mapButton, mapPanel],
  [keysButton, keysPanel],
]);
keysButton.click();
expect(keysPanel.hidden === false, "the keyboard icon did not open its card");
expect(mapPanel.hidden === true, "opening the keyboard card left the map covering it");
expect(mapButton.getAttribute("aria-expanded") === "false", "the map icon stayed highlighted after the keyboard card opened");
keysButton.click();
expect(keysPanel.hidden === true, "the keyboard icon did not close its card");

const css = readFileSync(new URL("../css/forest.css", import.meta.url), "utf8");
expect(/#minimap-body\[hidden\][\s\S]{0,40}display:\s*none/.test(css), "the map panel's own layout rule must not keep it visible when collapsed");

const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
expect(html.includes('id="minimap-toggle"'), "the map and distances need a corner icon");
expect(html.includes('id="minimap-body"'), "the map and distance list should collapse together");
expect(html.includes('id="keys-toggle"'), "the keyboard help needs its own icon");
const keys = html.slice(html.indexOf('id="keys-body"'), html.indexOf("</section>", html.indexOf('id="keys"')));
for (const key of ["W", "A", "S", "D", "F"]) {
  expect(keys.includes(`>${key}<`), `the keyboard card is missing the ${key} key`);
}
expect(/sit/i.test(keys), "the keyboard card should say that F sits");

if (failed) process.exit(1);
process.stdout.write("hud: map and keys collapse from the corner icons\n");
