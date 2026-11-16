const VIDEO_ID = /^[A-Za-z0-9_-]{11}$/;

const SEARCH_STATUS = {
  unconfigured: "Search needs a YouTube API key on the server.",
  empty: "Type a video to find.",
  failed: "Search failed. Try again.",
  none: "Nothing matched.",
};

async function defaultSearch(query) {
  const token = globalThis.localStorage?.getItem("forest_token");
  const response = await fetch("/api/youtube/search", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ token, q: query }),
  });
  if (!response.ok) return { ok: false, reason: "failed" };
  return response.json();
}

async function defaultPlaylists() {
  const response = await fetch("/playlists.json");
  if (!response.ok) throw new Error("playlists");
  return response.json();
}

export function createYoutubePanel(onVideo, options = {}) {
  const search = options.search || defaultSearch;
  const loadPlaylists = options.loadPlaylists || defaultPlaylists;
  const root = document.querySelector("#youtube");
  const field = root.querySelector("[data-video]");
  const frame = root.querySelector(".youtube-frame");
  const searchPanel = root.querySelector("[data-search]");
  const playlistPanel = root.querySelector("[data-playlists]");
  const query = root.querySelector("[data-query]");
  const searchStatus = root.querySelector("[data-search-status]");
  const results = root.querySelector("[data-results]");
  const playlistSelect = root.querySelector("[data-playlist]");
  const playlistVideos = root.querySelector("[data-playlist-videos]");
  let iframe = null;
  let playlists = null;

  function destroy() {
    iframe = null;
    frame.replaceChildren();
  }

  async function play(videoId) {
    const id = String(videoId || "").trim();
    if (!VIDEO_ID.test(id)) return;
    const saved = await onVideo(id);
    if (!saved) return;
    field.value = id;
    destroy();
    iframe = document.createElement("iframe");
    iframe.title = "YouTube video";
    iframe.width = "280";
    iframe.height = "158";
    iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
    iframe.referrerPolicy = "strict-origin-when-cross-origin";
    iframe.src = `https://www.youtube.com/embed/${id}?rel=0`;
    frame.append(iframe);
  }

  function togglePanel(panel, onOpen) {
    const willOpen = panel.hidden;
    searchPanel.hidden = true;
    playlistPanel.hidden = true;
    panel.hidden = !willOpen;
    if (willOpen && onOpen) void onOpen();
  }

  function fill(list, videos, labelFor) {
    list.replaceChildren();
    for (const video of videos) {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = labelFor(video);
      button.addEventListener("click", () => {
        void play(video.id);
      });
      item.append(button);
      list.append(item);
    }
  }

  async function runSearch() {
    const text = query.value.trim();
    results.replaceChildren();
    let body;
    try {
      body = await search(text);
    } catch {
      body = { ok: false, reason: "failed" };
    }
    if (!body?.ok) {
      const reason = body?.reason === "none" ? "none" : body?.reason;
      searchStatus.textContent = SEARCH_STATUS[reason] || SEARCH_STATUS.failed;
      return;
    }
    const found = Array.isArray(body.results) ? body.results : [];
    if (found.length === 0) {
      searchStatus.textContent = SEARCH_STATUS.none;
      return;
    }
    searchStatus.textContent = "";
    fill(results, found, (video) => `${video.title} — ${video.channel}`);
  }

  function showPlaylist(title) {
    const playlist = (playlists || []).find((item) => item.title === title) || (playlists || [])[0];
    fill(playlistVideos, playlist?.videos || [], (video) => video.title);
  }

  async function openPlaylists() {
    if (playlists) {
      showPlaylist(playlistSelect.value);
      return;
    }
    try {
      const body = await loadPlaylists();
      playlists = Array.isArray(body?.playlists) ? body.playlists : [];
    } catch {
      playlists = [];
      playlistVideos.replaceChildren();
      const note = document.createElement("li");
      note.textContent = "Playlists could not be loaded.";
      playlistVideos.append(note);
      return;
    }
    playlistSelect.replaceChildren();
    for (const playlist of playlists) {
      const option = document.createElement("option");
      option.value = playlist.title;
      option.textContent = playlist.title;
      playlistSelect.append(option);
    }
    if (playlists[0]) playlistSelect.value = playlists[0].title;
    showPlaylist(playlistSelect.value);
  }

  root.querySelector("[data-play]").addEventListener("click", () => {
    void play(field.value);
  });

  root.querySelector("[data-stop]").addEventListener("click", async () => {
    destroy();
    await onVideo(null);
  });

  root.querySelector("[data-search-toggle]").addEventListener("click", () => {
    togglePanel(searchPanel);
  });

  root.querySelector("[data-playlist-toggle]").addEventListener("click", () => {
    togglePanel(playlistPanel, openPlaylists);
  });

  root.querySelector("[data-find]").addEventListener("click", () => {
    void runSearch();
  });

  query.addEventListener("keydown", (event) => {
    if (event.code !== "Enter") return;
    event.preventDefault();
    void runSearch();
  });

  playlistSelect.addEventListener("change", () => {
    showPlaylist(playlistSelect.value);
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
