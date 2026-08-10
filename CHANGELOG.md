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

##
