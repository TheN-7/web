// Small UI enhancements; every page works without them.
document.addEventListener("DOMContentLoaded", () => {
  // Show / hide password.
  document.querySelectorAll("[data-reveal]").forEach((btn) => {
    const input = btn.parentElement.querySelector("input");
    btn.addEventListener("click", () => {
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.classList.toggle("on", show);
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
      input.focus();
    });
  });

  // Confirm destructive actions.
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  // Live search over a list of .file-row elements.
  document.querySelectorAll("input[data-filter]").forEach((input) => {
    const list = document.querySelector(input.dataset.filter);
    if (!list) return;
    const rows = list.querySelectorAll(".file-row");
    const none = list.querySelector(".no-match");
    input.addEventListener("input", () => {
      const q = input.value.trim().toLowerCase();
      let shown = 0;
      rows.forEach((row) => {
        const hit = row.dataset.name.includes(q);
        row.hidden = !hit;
        if (hit) shown++;
      });
      if (none) none.hidden = shown > 0;
    });
  });

  // Drag-and-drop upload zone.
  document.querySelectorAll("[data-dropzone]").forEach((zone) => {
    const input = zone.querySelector("input[type=file]");
    const label = zone.querySelector(".dz-files");
    const original = label.textContent;
    const update = () => {
      const names = Array.from(input.files).map((f) => f.name);
      label.textContent = names.length
        ? names.length + " selected: " + names.slice(0, 3).join(", ") + (names.length > 3 ? "…" : "")
        : original;
      zone.classList.toggle("has-files", names.length > 0);
    };
    input.addEventListener("change", update);
    ["dragenter", "dragover"].forEach((ev) =>
      zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.add("drag"); })
    );
    ["dragleave", "drop"].forEach((ev) =>
      zone.addEventListener(ev, () => zone.classList.remove("drag"))
    );
    zone.addEventListener("drop", (e) => {
      e.preventDefault();
      if (e.dataTransfer.files.length) {
        input.files = e.dataTransfer.files;
        update();
      }
    });
  });

  // Buttons show a busy state while their form submits (uploads can take a while).
  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (e.defaultPrevented) return;
      const btn = form.querySelector("button:not([type=button])");
      if (btn) setTimeout(() => btn.classList.add("busy"), 0);
    });
  });

  // Toasts fade out after a few seconds.
  document.querySelectorAll(".toast").forEach((t, i) => {
    setTimeout(() => t.classList.add("leaving"), 4500 + i * 300);
    t.addEventListener("animationend", (e) => { if (e.animationName === "toast-out") t.remove(); });
  });
});
