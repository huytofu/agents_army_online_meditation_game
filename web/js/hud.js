export function setPanelOpen(button, panel, open) {
  const shown = Boolean(open);
  button.setAttribute("aria-expanded", shown ? "true" : "false");
  panel.hidden = !shown;
}

export function bindPanelToggle(button, panel) {
  button.addEventListener("click", () => {
    setPanelOpen(button, panel, button.getAttribute("aria-expanded") !== "true");
  });
}

export function bindPanelGroup(pairs) {
  for (const [button, panel] of pairs) {
    button.addEventListener("click", () => {
      const open = button.getAttribute("aria-expanded") !== "true";
      for (const [otherButton, otherPanel] of pairs) {
        setPanelOpen(otherButton, otherPanel, otherButton === button && open);
      }
    });
  }
}
