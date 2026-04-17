async function fetchJSON(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

let map;
let markersLayer;

function createStatCard(label, value) {
  return `
    <article class="stat-card">
      <div class="stat-label">${label}</div>
      <div class="stat-value">${value}</div>
    </article>
  `;
}

function renderHotspots(hotspots) {
  if (!hotspots.length) {
    return `<div class="row"><strong>No hotspots yet</strong><p>Ingest incident data to see area-level risk.</p></div>`;
  }

  return hotspots
    .map(
      (item) => `
        <div class="row">
          <strong>${item.area_name}</strong>
          <p>${item.violations} suspected violations across ${item.incidents} incident records.</p>
          <span class="pill">Priority zone</span>
        </div>
      `
    )
    .join("");
}

function renderSourceMix(sourceMix) {
  if (!sourceMix.length) {
    return `<div class="row"><strong>No ingestion data yet</strong><p>Add camera or drone feeds to see source coverage.</p></div>`;
  }

  return sourceMix
    .map(
      (item) => `
        <div class="row">
          <strong>${item.source_type.replaceAll("_", " ")}</strong>
          <p>${item.incidents} incident records and ${item.violations} probable violations.</p>
        </div>
      `
    )
    .join("");
}

function renderIncidents(incidents) {
  if (!incidents.length) {
    return `<div class="row"><strong>No incidents yet</strong><p>Use the analyze endpoint to add live observations.</p></div>`;
  }

  return incidents
    .slice(0, 6)
    .map(
      (item) => `
        <div class="row">
          <strong>${item.source_name}</strong>
          <p>${item.area_name} • ${new Date(item.captured_at).toLocaleString()}</p>
          <p>${item.violations_detected} probable violations out of ${item.riders_detected} riders. Confidence ${Math.round(item.confidence_score * 100)}%.</p>
        </div>
      `
    )
    .join("");
}

function ensureMap() {
  if (map) {
    return;
  }

  map = L.map("hotspot-map", {
    zoomControl: true,
    scrollWheelZoom: true,
  }).setView([25.5941, 85.1376], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);
}

function renderMap(hotspots) {
  ensureMap();
  markersLayer.clearLayers();

  if (!hotspots.length) {
    return;
  }

  const bounds = [];
  hotspots.forEach((item) => {
    const marker = L.circleMarker([item.latitude, item.longitude], {
      radius: Math.max(10, item.violations * 2.5),
      color: "#88431c",
      fillColor: "#c56f32",
      fillOpacity: 0.55,
      weight: 2,
    });

    marker.bindPopup(
      `<strong>${item.area_name}</strong><br>${item.violations} probable violations across ${item.incidents} incidents.`
    );
    marker.addTo(markersLayer);
    bounds.push([item.latitude, item.longitude]);
  });

  if (bounds.length) {
    map.fitBounds(bounds, { padding: [32, 32] });
  }
}

async function postUpload(form) {
  const status = document.getElementById("upload-status");
  status.textContent = "Uploading video and sampling frames...";

  const formData = new FormData(form);
  const capturedAt = formData.get("captured_at");
  if (capturedAt) {
    formData.set("captured_at", new Date(capturedAt).toISOString());
  }

  const response = await fetch("/api/v1/analyze/video", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.status}`);
  }

  return response.json();
}

async function bootDashboard() {
  try {
    const [stats, incidents, pipeline] = await Promise.all([
      fetchJSON("/api/v1/stats"),
      fetchJSON("/api/v1/incidents"),
      fetchJSON("/api/v1/pipeline"),
    ]);

    document.getElementById("stats-grid").innerHTML = [
      createStatCard("Total incidents", stats.total_incidents),
      createStatCard("Total violations", stats.total_violations),
      createStatCard("Riders observed", stats.total_riders),
      createStatCard("Pipeline", pipeline.cv2_available ? "CV Ready" : "Form Mode"),
    ].join("");

    document.getElementById("hotspot-list").innerHTML = renderHotspots(stats.top_hotspots);
    document.getElementById("source-mix").innerHTML = renderSourceMix(stats.source_mix);
    document.getElementById("incident-list").innerHTML = renderIncidents(incidents);
    renderMap(stats.top_hotspots);

    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.querySelector('input[name="captured_at"]').value = now.toISOString().slice(0, 16);
    document.getElementById("upload-status").textContent =
      `${pipeline.detector_name} active in ${pipeline.model_mode} mode. ${pipeline.notes[0]}`;
  } catch (error) {
    document.getElementById("stats-grid").innerHTML = createStatCard("Status", "Offline");
    document.getElementById("hotspot-list").innerHTML = `<div class="row"><strong>Data unavailable</strong><p>${error.message}</p></div>`;
    document.getElementById("source-mix").innerHTML = `<div class="row"><strong>Pipeline unavailable</strong><p>The command dashboard could not load pipeline status.</p></div>`;
    document.getElementById("incident-list").innerHTML = `<div class="row"><strong>Retry later</strong><p>The API is not responding yet.</p></div>`;
  }
}

document.getElementById("upload-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const status = document.getElementById("upload-status");

  try {
    const result = await postUpload(form);
    status.textContent =
      `Analyzed ${result.frames_processed} sampled frames and created ${result.incidents_created} incident records with ${result.total_violations_detected} probable violations.`;
    await bootDashboard();
    form.reset();
  } catch (error) {
    status.textContent = error.message;
  }
});

bootDashboard();
