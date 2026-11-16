import { createYoutubePanel } from "../js/youtube.js";

function control() {
  const listeners = {};
  return {
    hidden: false,
    value: "",
    textContent: "",
    children: [],
    listeners,
    addEventListener(type, listener) {
      (listeners[type] ||= []).push(listener);
    },
    replaceChildren() {
      this.children = [];
    },
    append(...nodes) {
      this.children.push(...nodes);
    },
  };
}

const frame = control();
const field = control();
field.value = "dQw4w9WgXcQ";
const playButton = control();
const stopButton = control();
const searchToggle = control();
const playlistToggle = control();
const searchPanel = control();
searchPanel.hidden = true;
const query = control();
const findButton = control();
const searchStatus = control();
const results = control();
const playlistPanel = control();
playlistPanel.hidden = true;
const playlistSelect = control();
const playlistVideos = control();
const root = {
  hidden: true,
  querySelector(selector) {
    const found = {
      "[data-video]": field,
      input: field,
      ".youtube-frame": frame,
      "[data-play]": playButton,
      "[data-stop]": stopButton,
      "[data-search-toggle]": searchToggle,
      "[data-playlist-toggle]": playlistToggle,
      "[data-search]": searchPanel,
      "[data-query]": query,
      "[data-find]": findButton,
      "[data-search-status]": searchStatus,
      "[data-results]": results,
      "[data-playlists]": playlistPanel,
      "[data-playlist]": playlistSelect,
      "[data-playlist-videos]": playlistVideos,
    };
    return found[selector] || null;
  },
};
const scripts = [];
globalThis.document = {
  querySelector(selector) {
    if (selector === "#youtube") return root;
    return null;
  },
  createElement(tag) {
    const node = control();
    node.tag = tag;
    node.src = "";
    node.remove = () => {};
    if (tag === "script") scripts.push(node);
    return node;
  },
  head: { append(node) { scripts.push(node); } },
};
globalThis.window = globalThis;

let saved = null;
let queries = [];
const panel = createYoutubePanel(async (videoId) => {
  saved = videoId;
  return true;
}, {
  search: async (text) => {
    queries.push(text);
    if (text === "missing") return { ok: false, reason: "unconfigured" };
    return {
      ok: true,
      results: [{ id: "eKFTSSKCzWA", title: "Forest waterfall", channel: "johnnielawson" }],
    };
  },
  loadPlaylists: async () => ({
    playlists: [
      { title: "Quiet forest", videos: [{ id: "d0tU18Ybcvk", title: "Forest river" }] },
      { title: "Rain", videos: [{ id: "8plwv25NYRo", title: "Forest rain" }] },
    ],
  }),
});
panel.show();

let failed = false;
function expect(condition, message) {
  if (!condition) {
    failed = true;
    process.stderr.write(`${message}\n`);
  }
}

async function click(button) {
  const listener = (button.listeners.click || [])[0];
  expect(typeof listener === "function", "a player button has no click handler");
  if (typeof listener === "function") await listener();
}

try {
  await Promise.race([
    click(playButton),
    new Promise((_, reject) => setTimeout(() => reject(new Error("play timed out")), 30)),
  ]);
} catch (error) {
  process.stderr.write(`play did not finish: ${error.message}\n`);
  failed = true;
}

const iframe = () => frame.children.find((node) => node.tag === "iframe");
expect(Boolean(iframe()), "play did not create an iframe");
expect(iframe() && iframe().src.startsWith("https://www.youtube.com/embed/dQw4w9WgXcQ"), `iframe src was ${iframe() && iframe().src}`);
expect(iframe() && !iframe().src.includes("autoplay=1"), "the video must not autoplay");
expect(saved === "dQw4w9WgXcQ", "the video id was not saved");
expect(!scripts.some((node) => String(node.src).includes("iframe_api")), "play still loads the YouTube API, which evaluates strings");

await click(searchToggle);
expect(searchPanel.hidden === false, "search did not open");
query.value = "missing";
await click(findButton);
expect(queries.at(-1) === "missing", "search did not send the typed query");
expect(/api key/i.test(searchStatus.textContent), `search status was ${searchStatus.textContent}`);

query.value = "forest";
await click(findButton);
const resultButton = results.children.flatMap((item) => item.children || [item]).find((node) => node.tag === "button")
  || results.children.find((node) => node.tag === "button");
expect(Boolean(resultButton), "search did not list a video");
if (resultButton) await (resultButton.listeners.click || [])[0]?.();
expect(saved === "eKFTSSKCzWA", "the chosen search result was not saved");
expect(iframe() && iframe().src.includes("/embed/eKFTSSKCzWA"), "the chosen search result did not play");

await click(playlistToggle);
expect(playlistPanel.hidden === false, "playlists did not open");
const listed = playlistVideos.children.flatMap((item) => item.children || [item]);
const playlistButton = listed.find((node) => node.tag === "button") || playlistVideos.children.find((node) => node.tag === "button");
expect(Boolean(playlistButton), "the playlist did not list a title");
expect(playlistButton && /Forest river/.test(playlistButton.textContent), "the first playlist title was missing");
if (playlistButton) await (playlistButton.listeners.click || [])[0]?.();
expect(saved === "d0tU18Ybcvk", "the chosen playlist title was not saved");
expect(iframe() && iframe().src.includes("/embed/d0tU18Ybcvk"), "the chosen playlist title did not play");

panel.hide();
expect(frame.children.length === 0, "standing did not remove the iframe");

if (failed) process.exit(1);
process.stdout.write("youtube: embed plays without eval\n");
