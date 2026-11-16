const VIDEO_ID = /^[A-Za-z0-9_-]{11}$/;

export function createYoutubePanel(onVideo) {
  const root = document.querySelector("#youtube");
  const field = root.querySelector("input");
  const frame = root.querySelector(".youtube-frame");
  let iframe = null;

  function destroy() {
    iframe = null;
    frame.replaceChildren();
  }

  root.querySelector("[data-play]").addEventListener("click", async () => {
    const videoId = field.value.trim();
    if (!VIDEO_ID.test(videoId)) return;
    const saved = await onVideo(videoId);
    if (!saved) return;
    destroy();
    iframe = document.createElement("iframe");
    iframe.title = "YouTube video";
    iframe.width = "280";
    iframe.height = "158";
    iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
    iframe.referrerPolicy = "strict-origin-when-cross-origin";
    iframe.src = `https://www.youtube.com/embed/${videoId}?rel=0`;
    frame.append(iframe);
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
