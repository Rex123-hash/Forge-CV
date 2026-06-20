// Minimal: show a loading state on submit. No emojis, no frameworks.
document.querySelector("form")?.addEventListener("submit", (e) => {
  const btn = e.target.querySelector("button[type=submit]");
  if (btn) { btn.disabled = true; btn.textContent = "Generating..."; }
});
