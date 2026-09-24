/* Trans Travel Safety Map — app.js
 * - Leaflet map with two choropleth layers (countries, admin divisions)
 * - Continuous colour gradient: dark red (0.0) → band centre colours → light blue (1.0)
 * - Click popup: score (2 dp), international rank, risk text, sources
 */

(async function () {
  "use strict";

  /* ---------- data files ---------- */
  const BOUNDARIES = {
    countries: "boundaries/countries.geojson",
    admin1: "boundaries/admin1.geojson",
  };
  const DATA_FILES = {
    countries: "data/countries.json",
    admin1: "data/admin1.json",
  };
  const META_FILE = "data/meta.json";

  /* ---------- gradient ---------- */
  // Anchor points from PLAN.md §5.1: piecewise-linear RGB interpolation.
  let GRADIENT_ANCHORS = [
    [0.0, [0x67, 0x00, 0x0d]],
    [0.1, [0xd7, 0x30, 0x27]],
    [0.3, [0xfc, 0x8d, 0x59]],
    [0.5, [0xfe, 0xe0, 0x8b]],
    [0.7, [0x91, 0xcf, 0x60]],
    [0.9, [0x1a, 0x98, 0x50]],
    [1.0, [0xa8, 0xdb, 0xe8]],
  ];
  const BANDS = [
    { max: 0.2, label: "Do Not Travel" },
    { max: 0.4, label: "High Risk" },
    { max: 0.6, label: "Elevated Risk" },
    { max: 0.8, label: "Reduced Risk" },
    { max: 1.01, label: "Low Risk" },
  ];

  function hex(rgba) { return `#${rgba.map(c => c.toString(16).padStart(2, "0")).join("")}`; }

  function gradientColour(score) {
    const a = GRADIENT_ANCHORS;
    if (score <= a[0][0]) return hex(a[0][1]);
    for (let i = 1; i < a.length; i++) {
      if (score <= a[i][0]) {
        const t = (score - a[i - 1][0]) / (a[i][0] - a[i - 1][0]);
        return hex(a[i - 1][1].map((c, k) => Math.round(c + t * (a[i][1][k] - c))));
      }
    }
    return hex(a[a.length - 1][1]);
  }

  function bandLabel(score) {
    for (const b of BANDS) if (score < b.max) return b.label;
    return BANDS[BANDS.length - 1].label;
  }

  function darken(rgba, f) { return rgba.map(c => Math.round(c * f)); }

  /* ---------- state ---------- */
  let meta = {};
  let countryData = {};
  let admin1Data = {};
  let mode = location.hash.replace(/^#?view=/, "") === "admin1" ? "admin1" : "countries";
  let layers = {};        // mode -> L.GeoJSON
  let dotLayers = {};     // mode -> L.LayerGroup of markers for tiny features
  const loadedBoundaries = new Set();
  const loadedData = new Set();

  /* ---------- map ---------- */
  const map = L.map("map", {
    center: [20, 0],
    zoom: 2,
    minZoom: 2,
    maxZoom: 10,
    zoomSnap: 0.5,
    zoomDelta: 0.5,
    wheelPxPerZoomLevel: 250,
    worldCopyJump: true,
    scrollWheelZoom: true,
    zoomControl: true,
    attributionControl: true,
    maxBounds: L.latLngBounds([-89, -720], [89, 720]),
    maxBoundsViscosity: 0.6,
  });

  /* ---------- loading ---------- */
  async function getJSON(url) {
    const r = await fetch(url, { cache: "force-cache" });
    if (!r.ok) throw new Error(`${url}: ${r.status}`);
    return r.json();
  }

  const loadingStatus = document.getElementById("loadingStatus");
  function setLoading(msg) {
    if (msg) { loadingStatus.hidden = false; loadingStatus.textContent = msg; }
    else loadingStatus.hidden = true;
  }

  async function ensureMeta() {
    try { meta = await getJSON(META_FILE); } catch (e) { /* fallback defaults */ }
    if (Array.isArray(meta.gradientAnchors) && meta.gradientAnchors.length >= 7) {
      GRADIENT_ANCHORS = meta.gradientAnchors.map(([s, h]) => {
        const rgba = typeof h === "string"
          ? [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]
          : h;
        return [s, rgba];
      });
    }
    drawLegendBar();
  }

  async function ensureData(modeKey) {
    if (loadedData.has(modeKey)) return;
    setLoading("Loading scores…");
    const d = await getJSON(DATA_FILES[modeKey]);
    if (modeKey === "countries") countryData = d; else admin1Data = d;
    loadedData.add(modeKey);
    setLoading(null);
  }

  /* ---------- layer construction ---------- */
  function recordFor(modeKey, props) {
    if (modeKey === "countries") {
      return countryData[props.iso3] || null;
    }
    return admin1Data[props.shapeID] || null;
  }

  function styleFeature(feature) {
    const rec = recordFor(mode, feature.properties) ||
      (mode === "admin1" && countryData[feature.properties.iso3]);
    let fill = [0x99, 0x99, 0x99]; // no data
    if (rec && typeof rec.score === "number") {
      // exact gradient colour (band centre colour comes from anchors)
      fill = GRADIENT_ANCHORS[0][1]; // placeholder replaced below
    }
    // compute gradient colour directly
    let color = "#999999";
    if (rec && typeof rec.score === "number") color = gradientColour(rec.score);
    return {
      fillColor: color,
      fillOpacity: 0.75,
      weight: 1,
      color: "rgba(0,0,0,0.5)",
    };
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function sanitizeSummary(html) {
    // allow only <p>, <em>, <strong>, <a href>, <br>
    const tpl = document.createElement("div");
    tpl.innerHTML = html;
    const ok = new Set(["P", "EM", "STRONG", "BR", "A"]);
    (function walk(node) {
      for (const child of [...node.childNodes]) {
        if (child.nodeType === 1) {
          if (!ok.has(child.tagName)) {
            child.replaceWith(document.createTextNode(child.textContent));
          } else {
            if (child.tagName === "A") {
              child.setAttribute("rel", "noopener");
              child.setAttribute("target", "_blank");
              const href = child.getAttribute("href") || "";
              if (!/^https?:/i.test(href)) child.removeAttribute("href");
            }
            walk(child);
          }
        }
      }
    })(tpl);
    return tpl.innerHTML;
  }

  function popupHTML(modeKey, feature, rec) {
    const props = feature.properties;
    const name = esc(props.name || "Unknown");
    if (!rec || typeof rec.score !== "number") {
      const parentRec = modeKey === "admin1" ? countryData[props.iso3] : null;
      const parentLine = modeKey === "admin1"
        ? (parentRec && typeof parentRec.score === "number"
            ? `<p class="popup-sub">Part of ${esc(parentRec.name)} — no separate subnational assessment; national score shown.</p>`
            : `<p class="popup-sub">${countryData[props.iso3] ? esc(countryData[props.iso3].name) : esc(props.iso3 || "")}</p>`)
        : "";
      const inherited = parentRec && typeof parentRec.score === "number"
        ? popupHTML("countries", { properties: { iso3: props.iso3, name: props.name + " (" + parentRec.name + ")" } }, parentRec)
        : `<div class="popup-name">${name}</div>${parentLine}
        <p class="muted">Not yet assessed.</p>`;
      return inherited;
    }
    const score = Math.round(rec.score * 100) / 100;
    // Colour and band come from the raw score (or the stored band, which is
    // authoritative) so a 0.5999 is not shown as "0.60 Reduced Risk".
    const colour = gradientColour(rec.score);
    const label = typeof rec.band === "string" && rec.band ? rec.band : bandLabel(rec.score);
    let sub, rank;
    if (modeKey === "countries") {
      sub = "";
      rank = typeof rec.rank === "number" && meta.totalCountries
        ? `Rank ${rec.rank} of ${meta.totalCountries} countries`
        : "";
    } else {
      const parentRec = countryData[props.iso3];
      sub = `<p class="popup-sub">${parentRec ? esc(parentRec.name) : esc(props.iso3 || "")}</p>`;
      let r = "";
      if (typeof rec.worldRank === "number" && meta.totalAdmin1)
        r += `Rank ${rec.worldRank} of ${meta.totalAdmin1} states/provinces`;
      if (typeof rec.countryRank === "number" && rec.unitsInCountry)
        r += ` · ${rec.countryRank} of ${rec.unitsInCountry} in ${parentRec ? esc(parentRec.name) : ""}`;
      rank = r;
    }
    const summary = rec.summary ? `<div class="popup-text">${sanitizeSummary(rec.summary)}</div>` : "";
    const estNote = rec.estimated
      ? `<p class="popup-estimated">Model estimate — derived from the national-level assessment rather than a dedicated division dossier.</p>`
      : "";
    const outscope = rec.outOfScopeNotes
      ? `<div class="popup-outscope"><span class="label">Not factored into the score:</span> ${sanitizeSummary(rec.outOfScopeNotes)}</div>`
      : "";
    const sources = (Array.isArray(rec.sources) && rec.sources.length)
      ? `<div class="popup-sources"><details><summary>Sources (${rec.sources.length})${rec.researchedAt ? " · researched " + esc(rec.researchedAt) : ""}</summary>
          <ul>${rec.sources.map(u => {
            const url = typeof u === "string" ? u : String((u && u.url) || "");
            const note = (typeof u === "object" && u && u.summary) ? String(u.summary) : "";
            return `<li><a href="${esc(url)}" target="_blank" rel="noopener">${esc(url.replace(/^https?:\/\//, "").slice(0, 70))}</a>${note ? `<div class="src-note">${esc(note)}</div>` : ""}</li>`;
          }).join("")}</ul>
        </details></div>`
      : rec.inherited
        ? `<div class="popup-sources">Inherits national score${rec.researchedAt ? " · researched " + esc(rec.researchedAt) : ""}.</div>`
        : "";
    return `
      <div class="popup-name">${name}</div>${sub}
      <p class="popup-score">${score.toFixed(2)}</p>
      <div class="popup-band"><i style="background:${colour}"></i>${label}</div>
      <p class="popup-rank">${rank}</p>
      ${estNote}${summary}${outscope}${sources}`;
  }

  function openPopupAt(modeKey, feature, rec, latlng) {
    const popup = L.popup({ maxWidth: 420, maxHeight: 520 })
      .setLatLng(latlng)
      .setContent(popupHTML(modeKey, feature, rec))
      .openOn(map);
    // keep the whole popup (and its close button) inside the map: shift the
    // anchor down/up when the popup would overflow the container edges
    requestAnimationFrame(() => {
      const el = popup.getElement();
      if (!el) return;
      const cr = map.getContainer().getBoundingClientRect();
      const pr = el.getBoundingClientRect();
      const pad = 6;
      let dx = 0, dy = 0;
      if (pr.top < cr.top + pad) dy = cr.top + pad - pr.top;
      else if (pr.bottom > cr.bottom - pad) dy = cr.bottom - pad - pr.bottom;
      if (pr.left < cr.left + pad) dx = cr.left + pad - pr.left;
      else if (pr.right > cr.right - pad) dx = cr.right - pad - pr.right;
      if (dx || dy) {
        const p = map.latLngToContainerPoint(popup.getLatLng());
        popup.setLatLng(map.containerPointToLatLng([p.x + dx, p.y + dy]));
      }
    });
  }

  function buildLayer(modeKey, geojson) {
    return L.geoJSON(geojson, {
      style: styleFeature,
      onEachFeature: (feature, layer) => {
        const props = feature.properties;
        layer.bindTooltip(() => {
          const rec = recordFor(modeKey, props) ||
            (modeKey === "admin1" && countryData[props.iso3]);
          const s = rec && typeof rec.score === "number" ? ` — ${rec.score.toFixed(2)} ${bandLabel(rec.score)}` : "";
          return `${props.name || "?"}${s}`;
        }, { sticky: true, className: "score-tooltip" });
        layer.on("click", () => {
          const rec = recordFor(modeKey, props);
          openPopupAt(modeKey, feature, rec, layer.getBounds().getCenter());
        });
      },
    });
  }

  /* ---------- tiny-feature dots ----------
   * A country/region that renders only a few pixels across at the current zoom
   * is invisible and un-clickable. Draw a thin-outlined dot in its risk colour
   * (at its bounding-box centre) over it instead. Recomputed on every zoom.
   * In states/provinces mode dots stay sparse: a unit gets one only if (A) its
   * country itself also renders as a dot at this zoom, or (B) it sits far from
   * the country's other regions (islands, detached territories). Otherwise
   * dense small-unit countries overwhelm the map. */
  function pxBox(f, zoom) {
    if (!f.getBounds) return null;
    const key = "_px" + zoom;
    if (f[key]) return f[key];
    const b = f.getBounds();
    const nw = map.project(b.getNorthWest(), zoom);
    const se = map.project(b.getSouthEast(), zoom);
    return (f[key] = {
      w: Math.abs(se.x - nw.x), h: Math.abs(se.y - nw.y), c: b.getCenter(),
    });
  }

  function updateDots() {
    if (!dotLayers[mode]) dotLayers[mode] = L.layerGroup();
    if (!map.hasLayer(dotLayers[mode])) dotLayers[mode].addTo(map);
    dotLayers[mode].clearLayers();
    const layer = layers[mode];
    if (!layer) return;
    const zoom = map.getZoom();
    const SMALL2 = 120;      // px²-squared-diagonal threshold (~11px diagonal: Lesotho&Tetoko yes, Sierra Leone&Liberia no)
    const ISOLATED_PX = 24;  // px to nearest same-country region centroid

    // (A) countries that themselves render as dots at this zoom
    const tinyCountries = new Set();
    if (mode === "admin1" && layers.countries) {
      layers.countries.eachLayer((cf) => {
        const s = pxBox(cf, zoom);
        if (s && s.w * s.w + s.h * s.h < SMALL2 && cf.feature)
          tinyCountries.add(cf.feature.properties.iso3);
      });
    }

    // group same-country projected centroids for the isolation test
    const boxes = new Map();
    const pxCenters = {};
    layer.eachLayer((f) => {
      if (!f.feature) return;
      const s = pxBox(f, zoom);
      if (!s) return;
      boxes.set(f, s);
      const iso = f.feature.properties.iso3;
      const p = map.project(s.c, zoom);
      (pxCenters[iso] || (pxCenters[iso] = [])).push({ x: p.x, y: p.y });
    });

    const radius = mode === "countries" ? 3 : 2.5;
    layer.eachLayer((f) => {
      const s = boxes.get(f);
      if (!s || s.w * s.w + s.h * s.h >= SMALL2) return; // not "very small"
      const props = f.feature && f.feature.properties;
      if (!props) return;
      if (mode === "admin1" && !tinyCountries.has(props.iso3)) {
        // (B) only if far from every other region of the same country
        const me = map.project(s.c, zoom);
        let isolated = false;
        const peers = pxCenters[props.iso3] || [];
        if (peers.length < 2) isolated = true;
        else {
          let min = Infinity;
          for (const p of peers) {
            const d = Math.hypot(p.x - me.x, p.y - me.y);
            if (d > 0.5 && d < min) min = d;
          }
          isolated = min > ISOLATED_PX;
        }
        if (!isolated) return;
      }
      const rec = recordFor(mode, props) ||
        (mode === "admin1" && countryData[props.iso3]);
      if (!rec || typeof rec.score !== "number") return;
      const center = s.c;
      const dot = L.circleMarker(center, {
        radius,
        fillColor: gradientColour(rec.score),
        fillOpacity: 1,
        weight: 1,
        color: "rgba(255,255,255,0.85)",
        interactive: true,
      });
      dot.bindTooltip(() => {
        const t = ` — ${rec.score.toFixed(2)} ${bandLabel(rec.score)}`;
        return `${props.name || "?"}${t}`;
      }, { sticky: true, className: "score-tooltip" });
      dot.on("click", () => openPopupAt(mode, f.feature, rec, center));
      dotLayers[mode].addLayer(dot);
    });
  }

  map.on("zoomend", updateDots);

  async function ensureBoundary(modeKey) {
    if (loadedBoundaries.has(modeKey)) return;
    setLoading(modeKey === "admin1" ? "Loading states/provinces (large file)…" : "Loading map…");
    const geo = await getJSON(BOUNDARIES[modeKey]);
    loadedBoundaries.add(modeKey);
    await ensureData(modeKey);
    if (modeKey === "countries") await ensureData("admin1"); // for parent names/inherit
    layers[modeKey] = buildLayer(modeKey, geo);
    setLoading(null);
  }

  async function setMode(nextMode) {
    if (nextMode === "admin1" && !layers[nextMode]) {
      // load in background but show countries meanwhile
      try { await ensureBoundary(nextMode); } catch (e) {
        setLoading(null);
        alert("Could not load state/province boundaries: " + e.message);
        return;
      }
    } else {
      await ensureBoundary(nextMode);
    }
    mode = nextMode;
    for (const k of Object.keys(layers)) {
      if (map.hasLayer(layers[k])) map.removeLayer(layers[k]);
    }
    layers[mode].addTo(map);
    layers[mode].setStyle(styleFeature);
    for (const k of Object.keys(dotLayers)) if (dotLayers[k]) map.removeLayer(dotLayers[k]);
    updateDots();
    document.getElementById("btnCountries").classList.toggle("active", mode === "countries");
    document.getElementById("btnAdmin1").classList.toggle("active", mode === "admin1");
    document.getElementById("btnCountries").setAttribute("aria-selected", mode === "countries");
    document.getElementById("btnAdmin1").setAttribute("aria-selected", mode === "admin1");
    history.replaceState(null, "", mode === "admin1" ? "#view=admin1" : "#view=countries");
  }

  document.getElementById("btnCountries").addEventListener("click", () => setMode("countries"));
  document.getElementById("btnAdmin1").addEventListener("click", () => setMode("admin1"));

  /* ---------- legend ---------- */
  function drawLegendBar() {
    const canvas = document.getElementById("legendBar");
    const ctx = canvas.getContext("2d");
    const w = canvas.width, h = canvas.height;
    for (let x = 0; x < w; x++) {
      ctx.fillStyle = gradientColour(x / (w - 1));
      ctx.fillRect(x, 0, 1, h);
    }
  }

  /* ---------- about dialog ---------- */
  function aboutHTML() {
    const gen = meta.generatedAt ? esc(meta.generatedAt) : "—";
    const repo = (meta.repoUrl || "").replace(/\/+$/, "");
    const methUrl = repo ? `${repo}/blob/HEAD/METHODOLOGY.md` : "METHODOLOGY.md";
    const repoLinks = repo
      ? `(see also the <a href="${repo}/blob/HEAD/research/outing-risk-taxonomy.md" target="_blank" rel="noopener">risk taxonomy</a> and <a href="${repo}/blob/HEAD/research/anchors.md" target="_blank" rel="noopener">calibration anchors</a>) `
      : "";
    return `
    <p>This map scores the risk to a <strong>transgender visitor</strong> — someone who is,
    or is discovered to be, trans — in every country and, where evidence supports it, in each
    state/province. Scores run from 0.00 (dark red, highest risk) to 1.00 (light blue, lowest risk),
    using a continuous colour gradient whose anchor colours sit at the centre of the five
    named bands (Do Not Travel, High Risk, Elevated Risk, Reduced Risk, Low Risk).</p>
    <p>What the score covers: everyday exposure of a trans visitor — presence in public,
    use of public bathrooms, documents and border crossings, police interactions,
    arrest risk including detention in a gender-mismatched facility, harassment and violence,
    access to medication. It deliberately <em>excludes</em> general travel risks (crime,
    disease, conflict) and risks specific to residents (e.g. adoption or employment law),
    except where those signal official or public hostility. General risks, where serious,
    are mentioned in a region's popup under “Not factored into the score.”</p>
    <p>Scores are derived from web research (search results and primary sources fetched and
    read per region), not model memory. Every region's popup lists its sources. Ranks are
    competition-ranked (ties share a rank). Regions are compared against calibration anchor
    countries so the scale is relative as well as absolute, and the whole map was then
    refined through thousands of blind pairwise comparisons (each region's evidence
    presented anonymously, without names or prior scores, and rated against a randomly
    drawn partner).</p>
    <p>The full methodology — the risk taxonomy, the severity ladder, the calibration
    rules, and the blind-refinement process — is documented in
    <a href="${methUrl}" target="_blank" rel="noopener">METHODOLOGY.md</a>
    ${repoLinks}in the project repository. This edition covers research through
    ${esc(meta.edition || "2026")}; the map is updated annually.</p>
    <p><strong>License:</strong> the map, its scores, and all project data files are
    dedicated to the public domain (CC0 1.0) — free of copyright restrictions.</p>
    <p><strong>Boundaries are de jure</strong> (internationally recognised legal claims, not
    lines of current control — e.g. Crimea and occupied territories are shown within
    Ukraine). Contested areas with two legal claims are rendered at the most widely
    recognised position with a caveat in the relevant popups.
    Country boundaries and first-level divisions: <a href="https://www.geoboundaries.org/" target="_blank" rel="noopener">geoBoundaries</a> gbOpen (CC BY 4.0);
    Western Sahara polygon: Natural Earth (public domain); de jure conflict patches are documented in the repository.</p>
    <p>Data generated: ${gen}. Methodology version: ${esc(meta.methodologyVersion || "1.0")}.</p>
    <p class="muted">This map is informational research, not personalised advice. Conditions change;
    verify with current official travel advisories before travelling.</p>`;
  }
  const dlg = document.getElementById("aboutDialog");
  document.getElementById("btnAbout").addEventListener("click", () => {
    document.getElementById("aboutContent").innerHTML = aboutHTML();
    dlg.showModal();
  });
  document.getElementById("aboutClose").addEventListener("click", () => dlg.close());

  /* ---------- screenshot ---------- */
  function captureScreenshot() {
    // re-render the visible choropleth + dots onto an offscreen canvas, then
    // overlay the map title in white with a thin black outline, centred.
    const size = map.getSize();
    const scale = 2;
    const canvas = document.createElement("canvas");
    canvas.width = size.x * scale;
    canvas.height = size.y * scale;
    const ctx = canvas.getContext("2d");
    ctx.scale(scale, scale);
    ctx.fillStyle = "#0b0c0f";
    ctx.fillRect(0, 0, size.x, size.y);
    const pt = (ll) => map.latLngToContainerPoint(ll);
    const layer = layers[mode];
    if (layer) layer.eachLayer((f) => {
      if (!f.getBounds) return;
      const b = f.getBounds();
      if (!map.getBounds().intersects(b)) return;
      const st = f.options || {};
      ctx.fillStyle = st.fillColor || "#999";
      ctx.globalAlpha = st.fillOpacity == null ? 0.75 : st.fillOpacity;
      ctx.strokeStyle = "rgba(0,0,0,0.5)";
      ctx.lineWidth = 1;
      const g = f.feature.geometry;
      if (!g) return;
      if (g.type === "Polygon") {
        ctx.beginPath();
        for (const r of g.coordinates) {
          if (r.length < 2) continue;
          r.forEach((c, i) => { const p = pt(L.latLng(c[1], c[0])); i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y); });
          ctx.closePath();
        }
        ctx.fill(); ctx.stroke();
      } else if (g.type === "MultiPolygon") {
        for (const poly of g.coordinates) {
          ctx.beginPath();
          for (const r of poly) {
            if (r.length < 2) continue;
            r.forEach((c, i) => { const p = pt(L.latLng(c[1], c[0])); i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y); });
            ctx.closePath();
          }
          ctx.fill(); ctx.stroke();
        }
      }
      ctx.globalAlpha = 1;
    });
    if (dotLayers[mode]) dotLayers[mode].eachLayer((d) => {
      const p = pt(d.getLatLng());
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = d.options.fillColor;
      ctx.globalAlpha = 1;
      ctx.fill();
      ctx.strokeStyle = "rgba(255,255,255,0.85)";
      ctx.lineWidth = 1;
      ctx.stroke();
    });
    ctx.setTransform(scale, 0, 0, scale, 0, 0);
    const title = document.querySelector("h1").textContent;
    ctx.font = `800 ${Math.max(11, size.x * 0.015)}px system-ui, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "rgba(0,0,0,0.9)";
    ctx.lineWidth = 2;
    ctx.fillStyle = "#fff";
    ctx.strokeText(title, size.x / 2, 10);
    ctx.fillText(title, size.x / 2, 10);
    canvas.toBlob((blob) => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "trans-travel-safety-map.png";
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 30000);
    }, "image/png");
  }
  document.getElementById("btnScreenshot").addEventListener("click", captureScreenshot);

  /* ---------- boot ---------- */
  await ensureMeta();
  try { await ensureData("countries"); } catch (e) { /* data may not exist yet */ }
  await ensureBoundary("countries");
  await setMode(mode);
  if (mode === "admin1") await setMode("admin1");
})();
