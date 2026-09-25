(() => {
  let theme;
  try { theme = localStorage.getItem("uairotas-theme"); } catch (_) { /* Private storage can be unavailable. */ }
  if (!["light", "dark"].includes(theme)) theme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  document.documentElement.dataset.theme = theme;
})();
