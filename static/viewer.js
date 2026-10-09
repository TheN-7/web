// Client-side rendering of Word, PowerPoint and Excel files in the viewer page.
(function () {
  const root = document.getElementById("doc-viewer");
  if (!root) return;
  const kind = root.dataset.kind;
  const url = root.dataset.src;
  const status = document.getElementById("doc-status");

  function fail(err) {
    console.error(err);
    status.querySelector(".spinner")?.remove();
    status.querySelector(".status-text").textContent = "This file couldn't be previewed. Please download it instead.";
    status.classList.add("error");
  }

  function renderDocx(buf) {
    root.classList.add("doc-docx");
    return docx.renderAsync(buf, root, null, {
      inWrapper: true,
      ignoreLastRenderedPageBreak: false,
      experimental: true,
    });
  }

  function renderPptx(buf) {
    root.classList.add("doc-pptx");
    const width = Math.min((root.clientWidth || 992) - 32, 1100);
    return pptxPreview.init(root, { width: width, height: Math.round(width * 9 / 16), mode: "list" }).preview(buf);
  }

  function renderSheet(buf) {
    root.classList.add("doc-sheet");
    const wb = XLSX.read(buf, { type: "array", cellDates: true });
    const tabs = document.createElement("div");
    tabs.className = "sheet-tabs";
    const body = document.createElement("div");
    body.className = "sheet-body";
    root.append(tabs, body);

    function show(name, btn) {
      // sheet_to_html escapes cell contents.
      body.innerHTML = XLSX.utils.sheet_to_html(wb.Sheets[name], { header: "", footer: "" });
      tabs.querySelectorAll("button").forEach((b) => b.classList.toggle("active", b === btn));
    }
    wb.SheetNames.forEach((name, i) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = name;
      btn.onclick = () => show(name, btn);
      tabs.append(btn);
      if (i === 0) show(name, btn);
    });
    if (wb.SheetNames.length < 2) tabs.hidden = true;
  }

  const renderers = { docx: renderDocx, pptx: renderPptx, sheet: renderSheet };

  fetch(url, { credentials: "same-origin" })
    .then((r) => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.arrayBuffer();
    })
    .then((buf) => renderers[kind](buf))
    .then(() => status.remove())
    .catch(fail);
})();
