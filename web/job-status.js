/*
 * SOPR Offline Knowledge
 * Copyright (c) 2026 Aaron Morris / A2ThreeD.
 * Shared progress panel for the offline portal.
 */
(() => {
  const start = () => {
    if (window.top !== window || document.getElementById("sopr-job-status")) return;
    const host = document.createElement("div");
    host.id = "sopr-job-status";
    const root = host.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        :host {
          position: fixed; inset: auto max(1rem, env(safe-area-inset-right)) max(1rem, env(safe-area-inset-bottom)) auto;
          width: min(31rem, calc(100vw - 2rem)); z-index: 900;
          font: 0.875rem/1.4 system-ui, sans-serif; pointer-events: none;
        }
        aside {
          box-sizing: border-box; max-height: 37vh; overflow: auto; padding: .75rem 1rem;
          background: #102238; color: #edf4fb; border: 1px solid #7999bb;
          border-radius: .65rem; box-shadow: 0 .4rem 1.4rem rgba(0,0,0,.45);
          visibility: hidden; opacity: 0; transform: translateY(110%);
          transition: transform .2s, opacity .2s, visibility .2s;
        }
        aside.open { visibility: visible; opacity: 1; transform: translateY(0); pointer-events: auto; }
        section + section { margin-top: .65rem; padding-top: .65rem; border-top: 1px solid #38516e; }
        header { display: flex; align-items: baseline; justify-content: space-between; gap: .75rem; }
        a { color: #afd5ff; }
        p { margin: .2rem 0; overflow-wrap: anywhere; }
        progress { display: block; width: 100%; height: .55rem; accent-color: #7bb7ff; margin-top: .35rem; }
        @media (prefers-reduced-motion: reduce) { aside { transition: none; } }
      </style>
      <aside aria-label="SOPR job progress"></aside>
    `;
    document.body.append(host);
    const panel = root.querySelector("aside");
    const cacheKey = "sopr-job-status-v1";
    const endpoints = ["/api/apply", "/api/maps/sync"];
    const jobs = [null, null];
    let checking = false;

    try {
      const saved = JSON.parse(sessionStorage.getItem(cacheKey));
      if (saved && Date.now() - saved.at < 20000) jobs.splice(0, jobs.length, ...saved.jobs);
    } catch (_) {}

    function displayJob(state, map) {
      if (!state) return null;
      const problem = state.status === "failed" || (state.status === "succeeded" && state.download_failed > 0);
      if (state.status !== "running" && !(problem && Date.now() - Date.parse(state.finished_at) < 45000)) return null;
      const setup = !map && state.action === "full";
      const title = map ? "Offline maps" : setup ? "SOPR installation" : "Offline content";
      if (problem) {
        const failed = Number(state.download_failed);
        return { title, detail: state.error || `Finished with ${failed} failed download${failed === 1 ? "" : "s"}.` };
      }
      const percent = map && state.total_files && state.current_index && Number.isFinite(state.current_percent)
        ? Math.floor(((state.current_index - 1) * 100 + state.current_percent) / state.total_files)
        : state.progress_percent;
      const files = (state.active_downloads || []).map((file) => file.filename);
      const count = state.downloads_active && state.download_total
        ? `${state.download_current || 0} of ${state.download_total} files processed` : "";
      const mapName = state.current_label || state.current_file;
      const detail = map ? (mapName ? `${mapName}${state.total_files ? ` · map ${state.current_index} of ${state.total_files}` : ""}` : "Preparing maps…")
        : [state.step || "Preparing…", count, files.length ? files.join(", ") : state.downloads_active ? state.current_file : ""].filter(Boolean).join(" · ");
      return { title, detail, percent };
    }

    let lastView = "";
    function render() {
      const views = jobs.map((job, index) => displayJob(job, index === 1));
      const serialized = JSON.stringify(views);
      if (lastView === serialized) return;
      lastView = serialized;
      const sections = views.map((view, index) => {
        if (!view) return null;
        const section = document.createElement("section");
        const header = document.createElement("header");
        const title = document.createElement("strong");
        title.textContent = view.title;
        const link = document.createElement("a");
        link.href = index === 1 ? "/admin/#maps" : "/admin/#content";
        link.textContent = "Details";
        const detail = document.createElement("p");
        detail.textContent = view.detail;
        header.append(title, link);
        section.append(header, detail);
        if ("percent" in view) {
          const meter = document.createElement("progress");
          meter.max = 100;
          meter.setAttribute("aria-label", view.title);
          if (Number.isFinite(view.percent)) {
            meter.value = Math.max(0, Math.min(100, view.percent));
            title.textContent += ` · ${meter.value}%`;
          }
          section.append(meter);
        }
        return section;
      }).filter(Boolean);
      if (sections.length) panel.replaceChildren(...sections);
      panel.classList.toggle("open", Boolean(sections.length));
      panel.inert = !sections.length;
    }

    async function refresh() {
      if (checking || document.hidden) return;
      checking = true;
      try {
        await Promise.allSettled(endpoints.map(async (url, index) => {
          const response = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(4500) });
          if (!response.ok) return;
          const state = await response.json();
          jobs[index] = displayJob(state, index === 1) ? { ...state, log_tail: undefined } : null;
          render();
        }));
        try { sessionStorage.setItem(cacheKey, JSON.stringify({ at: Date.now(), jobs })); } catch (_) {}
      } finally {
        checking = false;
        render();
      }
    }

    render();
    refresh();
    window.setInterval(refresh, 2500);
    window.addEventListener("pageshow", refresh);
    document.addEventListener("visibilitychange", refresh);
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, { once: true });
  else start();
})();
