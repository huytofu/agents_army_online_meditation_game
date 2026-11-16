import { createYoutubePanel } from "../js/youtube.js";

const frame = {
  children: [],
  replaceChildren() {
    this.children = [];
  },
  append(node) {
    this.children.push(node);
  },
};
const field = { value: "dQw4w9WgXcQ" };
const root = {
  hidden: true,
  querySelector(selector) {
    if (selector === "input") return field;
    if (selector === ".youtube-frame") return frame;
    if (selector === "[data-play]") return playButton;
    if (selector === "[data-stop]") return stopButton;
    return null;
  },
};
const playButton = { listeners: {}, addEventListener(type, listener) { this.listeners[type] = listener; } };
const stopButton = { listeners: {}, addEventListener(type, listener) { this.listeners[type] = listener; } };
const scripts = [];
globalThis.document = {
  querySelector(selector) {
    if (selector === "#youtube") return root;
    return null;
  },
  createElement(tag) {
    const node = { tag, src: "", remove() {} };
    if (tag === "script") scripts.push(node);
    return node;
  },
  head: { append(node) { scripts.push(node); } },
};
globalThis.window = globalThis;

let saved = null;
const panel = createYoutubePanel(async (videoId) => {
  saved = videoId;
  return true;
});
panel.show();
try {
  await Promise.race([
    playButton.listeners.click(),
    new Promise((_, reject) => setTimeout(() => reject(new Error("play timed out")), 30)),
  ]);
} catch (error) {
  process.stderr.write(`play did not finish: ${error.message}\n`);
}

let failed = false;
function expect(condition, message) {
  if (!condition) {
    failed = true;
    process.stderr.write(`${message}\n`);
  }
}

const iframe = frame.children.find((node) => node.tag === "iframe");
expect(Boolean(iframe), "play did not create an iframe");
expect(iframe && iframe.src.startsWith("https://www.youtube.com/embed/dQw4w9WgXcQ"), `iframe src was ${iframe && iframe.src}`);
expect(iframe && !iframe.src.includes("autoplay=1"), "the video must not autoplay");
expect(saved === "dQw4w9WgXcQ", "the video id was not saved");
expect(!scripts.some((node) => String(node.src).includes("iframe_api")), "play still loads the YouTube API, which evaluates strings");

panel.hide();
expect(frame.children.length === 0, "standing did not remove the iframe");

if (failed) process.exit(1);
process.stdout.write("youtube: embed plays without eval\n");
