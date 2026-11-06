const VIDEO_ID = /^[A-Za-z0-9_-]{11}$/;
let apiPromise;

function loadApi() {
  if (window.YT?.Player) return Promise.resolve(window.YT);
  if (!apiPromise) {
    apiPromise = new Promise((resolve) => {
      const previous = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => {
        if (typeof previous === "function") previous();
        resolve(window.YT);
      };
      const script = document.createElement("script");
      script.src = "https://www.youtube.com/iframe_api";
      document.head.append(script);
    });
  }
  return apiPromise;
}

export function createYoutubePanel(onVideo) {
  const root = document.querySelector("#youtube");
  const field = root.querySelector("input");
  const frame = root.querySelector(".youtube-frame");
  let player = null;

  function mountSlot() {
    frame.replaceChildren();
    const slot = document.createElement("div");
    slot.id = "youtube-player";
    frame.append(slot);
    return slot;
  }

  function destroy() {
    if (player && typeof player.destroy === "function") player.destroy();
    player = null;
    mountSlot();
  }

  root.querySelector("[data-play]").addEventListener("click", async () => {
    const videoId = field.value.trim();
    if (!VIDEO_ID.test(videoId)) return;
    const saved = await onVideo(videoId);
    if (!saved) return;
    const YT = await loadApi();
    destroy();
    player = new YT.Player(mountSlot(), {
      videoId,
      width: "280",
      height: "158",
      playerVars: { autoplay: 0, rel: 0 },
    });
  });

  root.querySelector("[data-stop]").addEventListener("click", async () => {
    destroy();
    await onVideo(null);
  });

  return {
    setDraft(videoId) {
      field.value = videoId || "";
    },
    show() {
      root.hidden = false;
    },
    hide() {
      root.hidden = true;
      destroy();
    },
  };
}
