# Changelog

## 1.0.0 - 2026-11-24

First release of **Map2Globe**, an original plugin by ANABA MANGA, made first of all for **location and situation maps**. It was inspired by the GlobeBuilder plugin by Gispo Ltd. (GPL), rebuilt
and extended for QGIS 3.44 LTR and QGIS 4.

* **Switch the map to a globe** (azimuthal orthographic projection) and **switch it back to flat** with one click. The
  plugin's layers are kept, the globe-shaped *Halo* and *Oceans* layers are hidden on the flat map. The projection and
  view the map had before the globe are restored.
* **Layers**: countries (Natural Earth 50m / 110m, bundled so it works offline), graticules, oceans, halo and optional
  Sentinel-2 cloudless imagery. They are saved as files (not temporary layers), their legend colours match the map and
  the Pays/Countries layer is renamed to the language in use.
* **Centre the globe** on the current view, a country (searchable list), a layer, coordinates or an address
  (OpenStreetMap Nominatim geocoding, limited to one request per second).
* **Apply changes** updates the existing globe; it is only enabled while the map shows a globe.
* The globe's projection is named *Map2Globe - <projection>* instead of "unknown CRS" (one entry, updated in place).
* **French / English** interface with a FR / EN toggle, remembered between sessions; the generated layers follow the
  language.
* Credits panel with the data licences (Natural Earth, OpenStreetMap Nominatim, Sentinel-2 cloudless CC BY-NC-SA 4.0).
* Works on **QGIS 3.44 LTR (Qt 5)** and **QGIS 4.x (Qt 6)**; tested on QGIS 3.44.15 and QGIS 4.0.1.
