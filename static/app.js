(() => {
  "use strict";

  const MAX_BYTES = 15 * 1024 * 1024;
  const ALLOWED_EXT = ["pdf", "png", "jpg", "jpeg", "webp"];

  const $ = (id) => document.getElementById(id);
  const form = $("form");
  const fileInput = $("file");
  const drop = $("drop");
  const dropEmpty = $("dropEmpty");
  const dropFile = $("dropFile");
  const thumb = $("thumb");
  const fileName = $("fileName");
  const fileSize = $("fileSize");
  const fileError = $("fileError");
  const submitBtn = $("submitBtn");
  const results = $("results");
  const empty = $("empty");
  const output = $("output");

  let currentFile = null;
  let thumbUrl = null;
  let lastPayload = null;
  let loadingTimer = null;

  /* ---------------------------------------------------------------- helpers */

  // Safe DOM builder: text is always inserted as text (never HTML),
  // so model output can't inject markup.
  function h(tag, attrs, ...children) {
    const node = document.createElement(tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (v == null || v === false) continue;
        if (k === "class") node.className = v;
        else if (k === "text") node.textContent = v;
        else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
        else node.setAttribute(k, v === true ? "" : v);
      }
    }
    for (const c of children.flat()) {
      if (c == null || c === false) continue;
      node.append(c.nodeType ? c : document.createTextNode(String(c)));
    }
    return node;
  }

  const has = (v) => typeof v === "string" ? v.trim().length > 0 : v != null;
  const fmtSize = (b) => (b < 1024 * 1024 ? `${Math.max(1, Math.round(b / 1024))} KB` : `${(b / 1024 / 1024).toFixed(1)} MB`);
  const pick = (obj, ...keys) => { for (const k of keys) if (has(obj[k])) return obj[k]; return null; };

  /* ----------------------------------------------------------- status logic */

  // Returns "ok" | "warn" | "bad" | "neutral" from free-text status.
  // Checks "bad" words first because "abnormal" contains "normal".
  function statusClass(text) {
    if (!has(text)) return "neutral";
    const s = String(text).toLowerCase();
    const bad = /abnormal|high|low|elevat|raised|increas|decreas|reduc|positive|critical|deficien|excess|outside|out of range|असामान्य|अधिक|कमी|जास्त|जादा|ज्यादा|वाढ|उच्च|निम्न/;
    const warn = /uncertain|borderline|unclear|equivocal|mild|possible|marginal|अनिश्चित|सीमा|अस्पष्ट|सौम्य|संदिग्ध/;
    const ok = /normal|within|healthy|negative|unremarkable|no significant|stable|सामान्य|नॉर्मल|ठीक|सामान्य/;
    if (bad.test(s)) return "bad";
    if (warn.test(s)) return "warn";
    if (ok.test(s)) return "ok";
    return "neutral";
  }

  /* ------------------------------------------------------- result normalising */

  // Turns each of the 5 different Gemini schemas into one common list of items.
  function extractItems(data) {
    if (Array.isArray(data.list_of_parameters)) {
      return data.list_of_parameters.map((p) => {
        if ("value" in p) {
          // Blood / lab parameter
          return {
            kind: "lab",
            title: p.name,
            status: p.status,
            value: p.value,
            reference: p.refrence_range,
            explanation: p.simple_explaination,
          };
        }
        // Medicine
        return {
          kind: "medicine",
          title: p.name,
          facts: [
            ["Dosage", p.Dosage],
            ["When to take", p.when_to_take],
            ["Instructions", p.instructions],
            ["Used for", p.cures_what],
          ],
          explanation: p.simple_explaination,
        };
      });
    }
    if (Array.isArray(data.list_of_organs)) {
      return data.list_of_organs.map((o) => ({
        kind: "organ",
        title: o.Organ,
        status: o.Result,
        finding: o.Finding,
        facts: [["Measurement", o.Measurement]],
        explanation: o.Simple_explanation,
      }));
    }
    if (Array.isArray(data.findings)) {
      return data.findings.map((f) => ({
        kind: "finding",
        title: f.body_part || f.category,
        status: f.status,
        finding: f.finding,
        measurements: Array.isArray(f.measurements) ? f.measurements.filter(has) : [],
        explanation: f.simple_explanation,
      }));
    }
    return [];
  }

  function extractMeta(data) {
    const rows = [
      ["Examination", data.examination],
      ["Document type", data.document_type],
      ["Reason for test", data.clinical_indication],
      ["Purpose", data.purpose],
      ["Technique", data.technique],
    ];
    return rows.filter(([, v]) => has(v));
  }

  /* -------------------------------------------------------------- rendering */

  function factsList(rows) {
    const valid = rows.filter(([, v]) => has(v));
    if (!valid.length) return null;
    return h(
      "dl",
      { class: "facts" },
      valid.map(([k, v]) => h("div", null, h("dt", { text: k }), h("dd", { text: v })))
    );
  }

  function renderItem(item) {
    const sc = statusClass(item.status);
    const node = h("article", { class: `item s-${sc}`, "data-status": sc });

    node.append(
      h(
        "div",
        { class: "item__head" },
        h("h4", { class: "item__title", text: item.title || "Untitled" }),
        has(item.status) ? h("span", { class: `badge s-${sc}`, text: item.status }) : null
      )
    );

    if (item.kind === "lab" && has(item.value)) {
      node.append(
        h(
          "div",
          { class: "value" },
          h("span", { class: "value__num", text: item.value }),
          has(item.reference) ? h("span", { class: "value__ref", text: `Reference range: ${item.reference}` }) : null
        )
      );
    }

    if (has(item.finding)) node.append(h("p", { class: "finding", text: item.finding }));

    if (item.measurements && item.measurements.length) {
      node.append(h("div", { class: "pills" }, item.measurements.map((m) => h("span", { class: "pill", text: m }))));
    }

    const facts = item.facts ? factsList(item.facts) : null;
    if (facts) node.append(facts);

    if (has(item.explanation)) {
      node.append(h("div", { class: "simple" }, h("b", { text: "In simple words" }), h("p", { text: item.explanation })));
    }
    return node;
  }

  function callout(kind, title, text) {
    return h("section", { class: `callout callout--${kind}` }, h("h3", { text: title }), h("p", { text: text }));
  }

  function renderResult(payload) {
    lastPayload = payload;
    const data = payload.result || {};
    const items = extractItems(data);
    const meta = extractMeta(data);
    const summary = pick(data, "overall_summery", "overall_summary");
    const impression = pick(data, "impression");
    const doctorNote = pick(data, "doctor_suggestion");
    const important = Array.isArray(data.important_results) ? data.important_results.filter(has) : [];

    const frag = document.createDocumentFragment();

    // Header
    frag.append(
      h(
        "section",
        { class: "card" },
        h(
          "div",
          { class: "resulthead" },
          h(
            "div",
            null,
            h("h2", { text: payload.doc_type }),
            h(
              "div",
              { class: "chips" },
              payload.filename ? h("span", { class: "chip chip--brand", text: payload.filename }) : null,
              h("span", { class: "chip", text: payload.difficulty === "Ekdam Basic" ? "Ekdam Basic" : payload.difficulty === "Intermidiate" ? "Intermediate" : "Advanced" }),
              h("span", { class: "chip", text: payload.language })
            )
          ),
          h(
            "div",
            { class: "actions" },
            h("button", { type: "button", class: "ghost", onclick: copyResult }, "Copy"),
            h("button", { type: "button", class: "ghost", onclick: () => window.print() }, "Print / Save PDF")
          )
        ),
        meta.length ? h("div", { style: "margin-top:18px" }, factsList(meta)) : null
      )
    );

    if (has(summary)) frag.append(callout("summary", "In short", summary));

    // Items list with overview + filter
    if (items.length) {
      const counts = { ok: 0, warn: 0, bad: 0 };
      items.forEach((it) => { const c = statusClass(it.status); if (counts[c] !== undefined) counts[c]++; });
      const anyStatus = items.some((it) => has(it.status));
      const attention = counts.warn + counts.bad;

      const list = h("div", { id: "items" });
      items.forEach((it) => list.append(renderItem(it)));

      const label =
        items[0].kind === "medicine" ? "Medicines" : items[0].kind === "lab" ? "Test results" : items[0].kind === "organ" ? "Organs scanned" : "Findings";

      const counters = h("div", { class: "counts" });
      counters.append(h("span", { class: "chip", text: `${items.length} total` }));
      if (anyStatus) {
        if (counts.ok) counters.append(h("span", { class: "chip", style: "background:var(--ok-bg);color:var(--ok)", text: `${counts.ok} normal` }));
        if (counts.warn) counters.append(h("span", { class: "chip", style: "background:var(--warn-bg);color:var(--warn)", text: `${counts.warn} uncertain` }));
        if (counts.bad) counters.append(h("span", { class: "chip", style: "background:var(--bad-bg);color:var(--bad)", text: `${counts.bad} abnormal` }));
      }

      const head = h("div", { class: "overview" }, h("h3", { text: label }), counters);
      frag.append(head);

      if (anyStatus && attention > 0 && attention < items.length) {
        const btnAll = h("button", { type: "button", "aria-pressed": "true", text: "All" });
        const btnAtt = h("button", { type: "button", "aria-pressed": "false", text: "Needs attention" });
        const setFilter = (onlyAttention) => {
          btnAll.setAttribute("aria-pressed", String(!onlyAttention));
          btnAtt.setAttribute("aria-pressed", String(onlyAttention));
          list.querySelectorAll(".item").forEach((el) => {
            const s = el.getAttribute("data-status");
            el.hidden = onlyAttention && !(s === "bad" || s === "warn");
          });
        };
        btnAll.addEventListener("click", () => setFilter(false));
        btnAtt.addEventListener("click", () => setFilter(true));
        head.append(h("div", { class: "toggle", style: "width:100%;justify-content:flex-start" }, btnAll, btnAtt));
      }
      frag.append(list);
    }

    if (important.length) {
      frag.append(
        h("section", { class: "card" }, h("h3", { text: "Important results" }), h("ul", { class: "bullets" }, important.map((t) => h("li", { text: t }))))
      );
    }

    if (has(impression)) frag.append(callout("plain", "Doctor's impression (explained)", impression));
    if (has(doctorNote)) frag.append(callout("note", "Doctor's suggestion (as written in the report)", doctorNote));

    if (!items.length && !has(summary) && !important.length) {
      frag.append(h("p", { class: "none", text: "Nothing could be extracted from this file. Try a clearer scan or the original PDF." }));
    }

    output.replaceChildren(frag);
  }

  function renderError(message) {
    output.replaceChildren(h("div", { class: "error", role: "alert" }, h("strong", { text: "Couldn't analyse the report" }), message));
  }

  function renderLoading() {
    const msgs = ["Reading your report…", "Picking out the key values…", "Writing it in simple language…", "Almost there…"];
    const text = h("span", { text: msgs[0] });
    output.replaceChildren(
      h(
        "div",
        { class: "loading" },
        h("div", { class: "loading__msg" }, h("span", { class: "btn__spinner" }), h("div", null, text, h("div", { class: "loading__hint", text: "This usually takes 10–30 seconds." }))),
        h("div", { class: "sk sk--tall" }),
        h("div", { class: "sk" }),
        h("div", { class: "sk" })
      )
    );
    let i = 0;
    loadingTimer = setInterval(() => { i = Math.min(i + 1, msgs.length - 1); text.textContent = msgs[i]; }, 4500);
  }

  function stopLoadingTimer() { if (loadingTimer) { clearInterval(loadingTimer); loadingTimer = null; } }

  /* ----------------------------------------------------------- copy / export */

  function toPlainText(payload) {
    const d = payload.result || {};
    const lines = [`${payload.doc_type} — explained by MedSimpler`, ""];
    extractMeta(d).forEach(([k, v]) => lines.push(`${k}: ${v}`));
    const s = pick(d, "overall_summery", "overall_summary");
    if (has(s)) lines.push("", "IN SHORT", s);
    const items = extractItems(d);
    if (items.length) lines.push("", "DETAILS");
    items.forEach((it, i) => {
      lines.push("", `${i + 1}. ${it.title || ""}${has(it.status) ? ` [${it.status}]` : ""}`);
      if (has(it.value)) lines.push(`   Value: ${it.value}${has(it.reference) ? ` (reference: ${it.reference})` : ""}`);
      if (has(it.finding)) lines.push(`   ${it.finding}`);
      if (it.measurements && it.measurements.length) lines.push(`   Measurements: ${it.measurements.join(", ")}`);
      (it.facts || []).filter(([, v]) => has(v)).forEach(([k, v]) => lines.push(`   ${k}: ${v}`));
      if (has(it.explanation)) lines.push(`   In simple words: ${it.explanation}`);
    });
    if (Array.isArray(d.important_results) && d.important_results.length) {
      lines.push("", "IMPORTANT RESULTS");
      d.important_results.forEach((t) => lines.push(`- ${t}`));
    }
    if (has(d.impression)) lines.push("", "IMPRESSION", d.impression);
    if (has(d.doctor_suggestion)) lines.push("", "DOCTOR'S SUGGESTION (from the report)", d.doctor_suggestion);
    lines.push("", "Not medical advice. Check with your doctor.");
    return lines.join("\n");
  }

  async function copyResult(e) {
    const btn = e.currentTarget;
    if (!lastPayload) return;
    const original = btn.textContent;
    try {
      await navigator.clipboard.writeText(toPlainText(lastPayload));
      btn.textContent = "Copied ✓";
    } catch {
      btn.textContent = "Copy failed";
    }
    setTimeout(() => { btn.textContent = original; }, 1800);
  }

  /* ------------------------------------------------------------ file picking */

  function showFileError(msg) {
    if (msg) {
      fileError.textContent = msg;
      fileError.hidden = false;
      drop.classList.add("has-error");
    } else {
      fileError.hidden = true;
      drop.classList.remove("has-error");
    }
  }

  function clearFile() {
    currentFile = null;
    fileInput.value = "";
    if (thumbUrl) { URL.revokeObjectURL(thumbUrl); thumbUrl = null; }
    thumb.replaceChildren();
    dropFile.hidden = true;
    dropEmpty.hidden = false;
    drop.classList.remove("has-file");
  }

  function setFile(file) {
    showFileError("");
    if (!file) return;
    let ext = (file.name.split(".").pop() || "").toLowerCase();
    if (!ALLOWED_EXT.includes(ext)) {
      const byMime = { "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "application/pdf": "pdf" }[file.type];
      if (byMime) { file = new File([file], `${file.name || "photo"}.${byMime}`, { type: file.type }); ext = byMime; }
    }
    if (!ALLOWED_EXT.includes(ext)) { clearFile(); showFileError("Unsupported file type. Please upload a PDF, PNG, JPG or WEBP."); return; }
    if (file.size > MAX_BYTES) { clearFile(); showFileError("File is too large. Please choose a file under 15 MB."); return; }
    if (file.size === 0) { clearFile(); showFileError("That file is empty."); return; }

    currentFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = fmtSize(file.size);
    if (thumbUrl) URL.revokeObjectURL(thumbUrl);
    thumb.replaceChildren();
    if (ext === "pdf") {
      thumb.textContent = "PDF";
    } else {
      thumbUrl = URL.createObjectURL(file);
      thumb.append(h("img", { src: thumbUrl, alt: "" }));
    }
    dropEmpty.hidden = true;
    dropFile.hidden = false;
    drop.classList.add("has-file");
  }

  fileInput.addEventListener("change", () => setFile(fileInput.files[0]));
  $("removeFile").addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); clearFile(); });

  ["dragenter", "dragover"].forEach((ev) =>
    drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("is-over"); })
  );
  ["dragleave", "drop"].forEach((ev) =>
    drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("is-over"); })
  );
  drop.addEventListener("drop", (e) => {
    const files = e.dataTransfer && e.dataTransfer.files;
    if (!files || !files.length) return;
    if (files.length > 1) { showFileError("Please upload one file only."); return; }
    setFile(files[0]);
  });


  /* ------------------------------------------------------------------ camera */

  const cameraBtn = $("cameraBtn");
  const cameraInput = $("cameraInput");
  const camera = $("camera");
  const camVideo = $("camVideo");
  const camShot = $("camShot");
  const camMsg = $("camMsg");
  const camCapture = $("camCapture");
  const camRetake = $("camRetake");
  const camUse = $("camUse");
  const camCancel = $("camCancel");
  let camStream = null;
  let camBlob = null;
  let camShotUrl = null;

  const isTouchDevice = window.matchMedia("(pointer: coarse)").matches;

  function camMode(mode) {
    const review = mode === "review";
    camVideo.hidden = review;
    camShot.hidden = !review;
    camCapture.hidden = review;
    camRetake.hidden = !review;
    camUse.hidden = !review;
  }

  function stopStream() {
    if (camStream) { camStream.getTracks().forEach((t) => t.stop()); camStream = null; }
    camVideo.srcObject = null;
  }

  function closeCamera() {
    stopStream();
    if (camShotUrl) { URL.revokeObjectURL(camShotUrl); camShotUrl = null; }
    camBlob = null;
    camera.hidden = true;
    document.body.style.overflow = "";
    cameraBtn.focus();
  }

  async function openCamera() {
    camMode("live");
    camMsg.hidden = true;
    camCapture.disabled = false;
    camera.hidden = false;
    document.body.style.overflow = "hidden";
    try {
      camStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" }, width: { ideal: 2560 }, height: { ideal: 1440 } },
        audio: false,
      });
      camVideo.srcObject = camStream;
      camCapture.focus();
    } catch (err) {
      camCapture.disabled = true;
      camMsg.textContent =
        err && err.name === "NotAllowedError" ? "Camera access was blocked. Allow it in your browser settings, or upload a file instead."
        : err && err.name === "NotFoundError" ? "No camera was found on this device. Please upload a file instead."
        : "Couldn't start the camera. Please upload a file instead.";
      camMsg.hidden = false;
    }
  }

  cameraBtn.addEventListener("click", () => {
    // Phones: hand off to the native camera app (best quality + autofocus).
    // Desktops: live webcam preview (needs HTTPS or localhost, which Render provides).
    if (isTouchDevice || !(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)) cameraInput.click();
    else openCamera();
  });

  cameraInput.addEventListener("change", () => {
    if (cameraInput.files[0]) setFile(cameraInput.files[0]);
    cameraInput.value = "";
  });

  camCapture.addEventListener("click", () => {
    const w = camVideo.videoWidth, hgt = camVideo.videoHeight;
    if (!w || !hgt) return;
    const canvas = document.createElement("canvas");
    canvas.width = w; canvas.height = hgt;
    canvas.getContext("2d").drawImage(camVideo, 0, 0, w, hgt);
    canvas.toBlob((blob) => {
      if (!blob) { camMsg.textContent = "Couldn't capture the photo. Please try again."; camMsg.hidden = false; return; }
      if (camShotUrl) URL.revokeObjectURL(camShotUrl);
      camBlob = blob;
      camShotUrl = URL.createObjectURL(blob);
      camShot.src = camShotUrl;
      camMsg.hidden = true;
      camMode("review");
      camUse.focus();
    }, "image/jpeg", 0.92);
  });

  camRetake.addEventListener("click", () => { camMode("live"); camCapture.focus(); });
  camUse.addEventListener("click", () => {
    if (!camBlob) return;
    const photo = new File([camBlob], `camera-${Date.now()}.jpg`, { type: "image/jpeg" });
    closeCamera();
    setFile(photo);
  });
  camCancel.addEventListener("click", closeCamera);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !camera.hidden) closeCamera(); });
  window.addEventListener("pagehide", stopStream);

  /* ------------------------------------------------------------------ submit */

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentFile) {
      showFileError("Please upload a file first.");
      drop.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }

    const fd = new FormData();
    fd.append("file", currentFile);
    fd.append("doc_type", $("docType").value);
    fd.append("difficulty", form.elements["difficulty"].value);
    fd.append("language", form.elements["language"].value);

    submitBtn.disabled = true;
    submitBtn.classList.add("is-loading");
    submitBtn.querySelector(".btn__label").textContent = "Analysing…";
    results.setAttribute("aria-busy", "true");
    empty.hidden = true;
    renderLoading();
    if (window.matchMedia("(max-width: 920px)").matches) results.scrollIntoView({ behavior: "smooth", block: "start" });

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 120000);

    try {
      const res = await fetch("/api/analyse", { method: "POST", body: fd, signal: controller.signal });
      let body = null;
      try { body = await res.json(); } catch { /* non-JSON error page */ }
      if (!res.ok) {
        const msg = body && typeof body.detail === "string" ? body.detail : "Something went wrong. Please try again.";
        throw new Error(msg);
      }
      stopLoadingTimer();
      renderResult(body);
    } catch (err) {
      stopLoadingTimer();
      if (err.name === "AbortError") renderError("The request took too long. Please try again.");
      else if (err instanceof TypeError) renderError("Couldn't reach the server. Check your connection and try again.");
      else renderError(err.message);
    } finally {
      clearTimeout(timeout);
      submitBtn.disabled = false;
      submitBtn.classList.remove("is-loading");
      submitBtn.querySelector(".btn__label").textContent = "Analyse report";
      results.setAttribute("aria-busy", "false");
    }
  });

  // Exposed for tests only
  window.__medsimpler = { renderResult, statusClass, extractItems, toPlainText };
})();
