// ERGent: the interactive Ithaca zone map (Leaflet). Python sends each zone's status
// with session.send_custom_message("rw-zonemap", {id, zones}); this script draws the
// map once per container, colours the zones, sets the hover text, and reports clicks
// to Shiny (data-click-input) so a supervisor can pick a zone on the map.
(function () {
  "use strict";
  var maps = {};
  var waiting = {};
  var FALLBACK = { green: "#4fcf8e", amber: "#f0b43c", red: "#f26b61", grey: "#6b7688" };

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim().replace(/["']/g, "");
  }
  function colour(sev) { return cssVar("--map-" + sev) || FALLBACK[sev] || FALLBACK.grey; }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function init(el) {
    if (maps[el.id]) return maps[el.id];
    if (!window.L) return null;
    var geo = JSON.parse(el.dataset.geo);
    var center = JSON.parse(el.dataset.center || "[42.444,-76.499]");
    var map = L.map(el, { scrollWheelZoom: false, zoomSnap: 0.25 }).setView(center, Number(el.dataset.zoom || 13));
    // Esri's grey canvas tiles (no key needed): a base layer plus a street-name layer.
    var theme = el.dataset.tiles || cssVar("--map-tiles") || "dark";
    var shade = theme === "light" ? "Light" : "Dark";
    var esri = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_" + shade + "_Gray_";
    L.tileLayer(esri + "Base/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 16, attribution: "Tiles &copy; Esri &middot; &copy; OpenStreetMap contributors"
    }).addTo(map);
    map.createPane("rwLabels");
    map.getPane("rwLabels").style.zIndex = 450;            // street names above the zones
    map.getPane("rwLabels").style.pointerEvents = "none";
    L.tileLayer(esri + "Reference/MapServer/tile/{z}/{y}/{x}", { maxZoom: 16, pane: "rwLabels" }).addTo(map);
    var layers = {};
    var line = cssVar("--map-line") || "#c3cddc";
    L.geoJSON(geo, {
      style: function () { return { color: line, weight: 1.25, opacity: 0.9, fillColor: FALLBACK.grey, fillOpacity: 0.3 }; },
      onEachFeature: function (f, layer) {
        var z = f.properties.zone;
        layers[z] = layer;
        layer.bindTooltip("<b>Zone " + z + " &middot; " + esc(f.properties.name) + "</b>", { sticky: true, className: "rw-map-tip" });
        layer.on("mouseover", function () { layer.setStyle({ weight: 2.5, opacity: 1 }); });
        layer.on("mouseout", function () { layer.setStyle({ weight: 1.25, opacity: 0.9 }); });
        layer.on("click", function () {
          var id = el.dataset.clickInput;
          if (id && window.Shiny && Shiny.setInputValue) Shiny.setInputValue(id, z, { priority: "event" });
        });
      }
    }).addTo(map);
    geo.features.forEach(function (f) {
      L.marker(f.properties.center, {
        interactive: false,
        icon: L.divIcon({ className: "rw-zone-label", html: f.properties.zone, iconSize: [24, 24] })
      }).addTo(map);
    });
    var bounds = L.geoJSON(geo).getBounds();
    map.fitBounds(bounds, { padding: [8, 8] });
    if (window.ResizeObserver) {
      new ResizeObserver(function () { map.invalidateSize(); if (el.offsetWidth) map.fitBounds(bounds, { padding: [8, 8] }); }).observe(el);
    }
    maps[el.id] = { map: map, layers: layers };
    return maps[el.id];
  }

  function apply(entry, zones) {
    Object.keys(zones).forEach(function (z) {
      var layer = entry.layers[z];
      if (!layer) return;
      var info = zones[z];
      layer.setStyle({ fillColor: colour(info.sev), fillOpacity: info.sev === "grey" ? 0.18 : 0.42 });
      var lines = (info.lines || []).map(esc).join("<br>");
      layer.setTooltipContent("<b>Zone " + z + " &middot; " + esc(info.name) + "</b><br>" +
        esc(info.status || "") + (lines ? "<br>" + lines : ""));
    });
  }

  function handle(msg) {
    var el = document.getElementById(msg.id);
    var entry = el ? init(el) : null;
    if (!entry) { waiting[msg.id] = msg; return; }
    apply(entry, msg.zones);
  }

  // Retry messages that arrived before Leaflet or the container was ready.
  setInterval(function () {
    Object.keys(waiting).forEach(function (id) {
      var msg = waiting[id];
      delete waiting[id];
      handle(msg);
    });
  }, 500);

  function register() {
    if (window.Shiny && Shiny.addCustomMessageHandler) {
      Shiny.addCustomMessageHandler("rw-zonemap", handle);
    } else {
      setTimeout(register, 50);
    }
  }
  register();
})();
