"""Interactive map of Ithaca, NY with ERGent's six zones (Leaflet, drawn in the browser).

The zone outlines are illustrative areas of the city, laid out on the same 3 x 2 grid
as qc.NEIGHBORS (A B C on the north side, D E F on the south side); they are not
official EMS districts. Python only says what each zone looks like (a status and a
few lines of text); the browser script www/zonemap.js draws the map, colours the
zones, shows the hover text and reports clicks.

    map_div(resolve_id("map"), click_input=resolve_id("map_click"))   # in a UI function
    await update(session, session.ns("map"), {"A": {"sev": "green", ...}})  # in an async effect
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shiny import ui  # noqa: E402

import qc  # noqa: E402

LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
WWW = Path(__file__).resolve().parent / "www"

#: Map view: downtown Ithaca, zoomed to show the whole city.
CENTER = (42.4440, -76.4990)
ZOOM = 13

#: Zone outlines as [lat, lon] rings. West edge -76.535, east edge -76.462; the Cayuga
#: Inlet (about -76.505) and Aurora Street / Cascadilla Creek (about -76.488) split west,
#: centre and east; State Street (about 42.441) splits north from south.
POLYGONS = {
    "A": [[42.4675, -76.5350], [42.4675, -76.5060], [42.4545, -76.5045], [42.4410, -76.5055],
          [42.4405, -76.5350]],
    "B": [[42.4675, -76.5060], [42.4680, -76.4890], [42.4550, -76.4895], [42.4415, -76.4880],
          [42.4410, -76.5055], [42.4545, -76.5045]],
    "C": [[42.4680, -76.4890], [42.4680, -76.4620], [42.4420, -76.4620], [42.4415, -76.4880],
          [42.4550, -76.4895]],
    "D": [[42.4405, -76.5350], [42.4410, -76.5055], [42.4300, -76.5050], [42.4180, -76.5060],
          [42.4180, -76.5350]],
    "E": [[42.4410, -76.5055], [42.4415, -76.4880], [42.4300, -76.4885], [42.4180, -76.4880],
          [42.4180, -76.5060], [42.4300, -76.5050]],
    "F": [[42.4415, -76.4880], [42.4420, -76.4620], [42.4180, -76.4620], [42.4180, -76.4880],
          [42.4300, -76.4885]],
}


def _center(ring):
    lats = [p[0] for p in ring]
    lons = [p[1] for p in ring]
    return [sum(lats) / len(lats), sum(lons) / len(lons)]


def geojson() -> dict:
    """The six zones as a GeoJSON FeatureCollection (lon/lat order, as GeoJSON requires)."""
    feats = []
    for zone, ring in POLYGONS.items():
        coords = [[lon, lat] for lat, lon in ring] + [[ring[0][1], ring[0][0]]]
        feats.append({"type": "Feature",
                      "properties": {"zone": zone, "name": qc.ZONE_NAMES[zone], "center": _center(ring)},
                      "geometry": {"type": "Polygon", "coordinates": [coords]}})
    return {"type": "FeatureCollection", "features": feats}


def head():
    """The tags the page needs once: Leaflet's stylesheet and script, and zonemap.js."""
    return ui.TagList(
        ui.tags.link(rel="stylesheet", href=LEAFLET_CSS, crossorigin=""),
        ui.tags.script(src=LEAFLET_JS, crossorigin=""),
        ui.include_js(WWW / "zonemap.js", method="inline"))


def map_div(element_id: str, click_input: str | None = None, height: str = "320px",
            tiles: str | None = None):
    """The map's container. `element_id` and `click_input` must already be namespaced
    (resolve_id in a module UI). `tiles` is "dark" or "light" (default: the CSS
    variable --map-tiles, else dark)."""
    attrs = {"data-geo": json.dumps(geojson()), "data-center": json.dumps(CENTER),
             "data-zoom": str(ZOOM)}
    if click_input:
        attrs["data-click-input"] = click_input
    if tiles:
        attrs["data-tiles"] = tiles
    return ui.div(id=element_id, class_="rw-leaflet", style=f"height:{height}", **attrs)


async def update(session, element_id: str, zones: dict) -> None:
    """Colour the zones and set their hover text.

    zones: {zone: {"sev": "green"|"amber"|"red"|"grey", "status": str, "lines": [str, ...]}}
    The zone's name is added here, from qc.ZONE_NAMES.
    """
    payload = {z: {"name": qc.ZONE_NAMES.get(z, z), **info} for z, info in zones.items()}
    await session.send_custom_message("rw-zonemap", {"id": element_id, "zones": payload})
