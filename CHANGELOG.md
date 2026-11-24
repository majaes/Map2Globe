# CHANGELOG

### 0.2.3 - 15/01/2020

* Initial release

### 0.3.0 - 17/01/2020

* Rounder halo with default of 64 segments.
* New data sources: Sentinel-2 cloudless and Natural Earth 30 degree graticules

### 0.4.0 - 24/01/2020

* Dockable window
* Visualization customization
* Option to center based on a layer
* Bug fixes

### 0.5.0 - 11/02/2020

* Possibility to add Globe to any layout
* More accurate countries and graticules
* Improved UI and customization
* Simple tests

### 0.6.0 - 23/09/2020

* More projections (might work depending on PROJ version)
* Fixed bug with changing origin of the globe
* Fixed rendering artefacts caused by graticules by generating those via processing algorithms
* Various bug fixes
* Use pytest and CI tests
* Automatic release process with <a href="https://github.com/opengisch/qgis-plugin-ci">qgis-plugin-ci</a>

### 0.6.1 - 10/08/2026

* Fixed plugin failing to load on QGIS 4.x (Qt6-based builds): replaced direct `PyQt5` imports with the Qt-version-independent `qgis.PyQt` shim across the plugin and the vendored `qgis_plugin_tools` package

### 0.6.2 - 10/08/2026

* Fixed `AttributeError: type object 'Qt' has no attribute 'black'` on QGIS 4.x (Qt6): PyQt6 requires scoped enum access (e.g. `Qt.GlobalColor.black` instead of `Qt.black`). Fully-qualified all previously-flat `Qt.*`, `QAbstractItemView.*` enum references in `definitions/settings.py`, `plugin.py`, `test/test_globe.py` and the vendored `qgis_plugin_tools` widgets

### 0.6.3 - 10/08/2026

* Declared `qgisMaximumVersion=4.99` in metadata.txt: without it, QGIS infers a max version of `3.99` from `qgisMinimumVersion=3.2`, which marked the plugin "invalid" on QGIS 4.x even though it now loads without error

### 0.6.4 - 10/08/2026

* Added a dedicated "Globe Builder" toolbar (`iface.addToolBar`) instead of adding the plugin's icon to the generic Plugins toolbar, so it's visible as its own toggleable toolbar

### 0.6.5 - 10/08/2026

* Fixed the globe's custom orthographic projection silently failing to apply (project CRS stayed at EPSG:4326 and the map never rendered as a globe): PROJ ≥ 6 requires `+type=crs` on proj-string CRS definitions, otherwise `QgsCoordinateReferenceSystem.createFromProj()` returns an invalid CRS and `setCrs()` is a no-op. Added `+type=crs` to all projection strings in `definitions/projections.py` and added warning logs everywhere `createFromProj()`'s return value was previously ignored (`core/globe.py`, `core/halo.py`)

### 0.6.6 - 10/08/2026

* Fixed "Add the Globe to a Layout" deleting any layer the user had manually placed inside the "Globe" group: `Globe.delete_group()` unconditionally removed every child of the group before rebuilding it. It now only removes the plugin's own managed layers (Halo/Countries/Graticules/S2 Cloudless) by name, and no longer removes the group node itself, so manually added layers (e.g. a filtered/highlighted basemap) survive repeated clicks

### 0.6.7 - 10/08/2026

* Fixed Graticules color/resolution changes silently having no effect: `load_data()` only (re)created the Graticules layer if none existed yet, so once created it was never restyled again. It's now deleted and recreated on every call, same as Halo already was.
* Fixed "Add the Globe to a Layout" stacking a brand new, identically-positioned map item on top of the layout on every click instead of updating the existing one — since the old (stale-looking) item was still there covering the new one, style/color changes appeared to never apply. `Globe.add_to_layout()` now reuses the existing map item (tracked via a stable item ID) and explicitly calls `refresh()` to force a redraw, only creating/positioning a new item the first time.

### 0.6.8 - 10/08/2026

* Fixed "Create new layout (LayoutGlobe)" deleting and recreating the "LayoutGlobe" print layout from scratch every time it was picked, discarding any manual page setup. `create_layout()` now reuses the existing "LayoutGlobe" layout if one already exists (same behavior as picking it by name from the dropdown), and only creates a brand new one if none exists yet.

### 0.6.9 - 10/08/2026

* Fixed changing the "Countries" resolution (e.g. 50m → 110m) having no effect once the layer already existed: `load_natural_earth_data()` matched layers by name only and reused whatever was already loaded regardless of the requested source file. It now compares the existing layer's source against the requested one and reloads it whenever they differ. Also fixed a related latent bug where a failed remote load was never detected (`QgsVectorLayer(...)` never returns `None`, even when invalid) so the local-data fallback never actually ran; now checked via `layer.isValid()`.

### 0.7.0 - 10/08/2026

* Added a "None" option to "Halo type" so the globe can be built without any halo layer at all. Selecting it removes any existing Halo layer instead of creating one, and disables the now-irrelevant halo color pickers.

### 0.7.1 - 10/08/2026

* Unified the two separate "background" color pickers into one: the "Background" swatch now also sets the print layout map item's background (representing water/ocean behind the countries), instead of the easy-to-miss, separately-defaulted "Globe Layout background" field (removed). Also explicitly enabled the layout map item's background (`setBackgroundEnabled(True)`), which was previously only ever set with a color but never turned on.

### 0.7.2 - 10/08/2026

* Fixed "Color for Countries intersecting the current view" using a stale/inconsistent map extent: it was read from `iface.mapCanvas().extent()` *after* the project CRS had already been switched to the globe's custom orthographic projection, and the canvas isn't guaranteed to have recalculated its extent in the new CRS by that point — potentially selecting all, none, or the wrong countries. The view extent and CRS are now captured once, before any projection switch, and threaded through to the selection instead of being re-read late.

### 0.7.3 - 10/08/2026

* Fixed "Add the Globe to a Layout" showing a tiny, flat-looking crop instead of the full globe: the `QgsMapSettings` used to compute the map item's initial extent (`ms.fullExtent()`) never had its destination CRS set to the globe's orthographic projection, so the extent was computed in degrees (a geographic default) instead of metres, then applied as if it *were* in metres — zooming the map item in on a sliver right at the projection's centre. Added the missing `ms.setDestinationCrs(crs)` before computing the extent.

### 0.7.4 - 24/11/2026

* Added a built-in French translation (`definitions/translations.py`), loaded automatically when QGIS runs in French. It's a plain Python dictionary served through a `QTranslator`, so no `lrelease` compilation is needed. The translator is also now kept alive (it used to be garbage collected). Layer/group names stay untranslated because the plugin uses them as identifiers.
* Fixed the empty/flat map after "Apply changes": the globe projection was only applied when the projection differed from its initial value, so the project could stay in EPSG:4326. It is now always re-applied.
* Added `Globe.zoom_to_globe()`: the canvas is refitted to the whole globe after "Apply changes" / "Add the Globe to a Map", since a CRS switch leaves the old extent (degrees) interpreted as metres.
* Minor cleanups: missing `@pyqtSlot`, a no-op assignment, and an unparsable origin no longer overrides the previous one.
* Panel UI: the three action buttons are now stacked vertically, which lowers the panel's minimum width from ~1100 px to ~450 px (it used to squash the map canvas). The Countries/Graticules checkboxes now have visible labels, and their resolution drop-downs only show the value (`50m`, `10°`).
* Added `dev/harness.py`: runs the panel next to a real map canvas outside QGIS (`--fr` for French, `--auto file.png` for a screenshot), so changes can be tried without reloading the plugin in QGIS.
* Removed the panel's horizontal scrollbar at normal widths: long labels now wrap, drop-downs can shrink, the Sentinel-2 checkbox moved to its own row, the "Color for Countries intersecting the current view" text wraps, and the Visualization columns are stacked. The panel's minimum content width went from ~825 px to ~460 px (measured with a wide font).
* Attributions: the section is now collapsed by default, the text is shorter and built in code (so it is translated, including in French), the Sentinel-2 cloudless notice (CC BY-NC-SA, non-commercial) only shows when that layer is enabled, and the broken Natural Earth link and the "vectior" typo are fixed (also in `metadata.txt`).
* Fixed the address search (geocoding) failing: Nominatim now answers 404 on the old `/search/<query>` URL, so requests use `/search?q=...` with a properly encoded query. Also fixed the Qt6 `QNetworkReply.NoError` check, which raised silently inside the slot, added an identifying User-Agent (required by Nominatim's policy), and made failures/empty results visible in the message bar. The first result is preselected so "Apply changes" works right after a search. Added unit tests for the URL building and result parsing.
