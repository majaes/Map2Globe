Development of the Map2Globe plugin
====================================

The code of the plugin is in the [Map2Globe](../Map2Globe) folder. Python files use **relative imports**:

```python
from ..core.globe import Globe          # Good
from Map2Globe.core.globe import Globe  # Bad
```

## Layout

* `Map2Globe/plugin.py`: the QGIS plugin class (toolbar, menu, panel).
* `Map2Globe/ui/map2globe_dockwidget.py` and `Map2Globe/resources/ui/map2globe_dockwidget_base.ui`: the panel.
* `Map2Globe/core/`: building and switching the globe (`globe.py`), halo/oceans, graticules, geocoding.
* `Map2Globe/definitions/`: settings, projections, translations and the language switch (`language.py`).
* `Map2Globe/test/`: the tests.
* `dev/`: development tools (harness, zip build).

## Tests

Install `pytest` and `pytest-qgis` for the Python of QGIS (see `requirements-dev.txt`) and run, from the repository
root, with the Python of QGIS:

```powershell
$env:QT_QPA_PLATFORM="offscreen"; & "C:\Program Files\QGIS 4.0.1\bin\python-qgis.bat" -m pytest Map2Globe/test -q
```

The plugin supports QGIS 3.44 (Qt 5) and QGIS 4 (Qt 6): run the tests with both. With QGIS 3.44 the launcher is
`python-qgis-ltr.bat`:

```powershell
$env:QT_QPA_PLATFORM="offscreen"; & "C:\Program Files\QGIS 3.44.15\bin\python-qgis-ltr.bat" -m pytest Map2Globe/test -q
```

## Trying the panel without reloading QGIS

`dev/harness.py` opens the panel next to a real map canvas and layers panel, outside QGIS:

```powershell
& "C:\Program Files\QGIS 4.0.1\bin\python-qgis.bat" dev\harness.py --fr
```

`--fr` uses the French interface (English by default), `--auto file.png` clicks "Switch the map to a globe", saves a
screenshot and quits.

## Translations

The plugin is bilingual. The translations are plain Python dictionaries in
`Map2Globe/definitions/translations.py` (no `.ts` / `.qm` files to compile): the key is the English text, the value its
translation. Add every new `tr(u"...")` text and every text of the `.ui` file there. `definitions/language.py` installs
the translator, remembers the choice made with the FR / EN toggle and renames the generated layers.

To add a language, add its dictionary to `TRANSLATIONS`, its code to `LANGUAGES` and a button in
`setup_language_buttons()` of the panel.

## Building the release zip

Always build the zip with the script, never by hand: it zips every tracked file of the plugin (a new module cannot be
forgotten) and then imports the plugin from the extracted zip as QGIS does.

```powershell
& "C:\Program Files\QGIS 4.0.1\bin\python-qgis.bat" dev\build_zip.py
```

The result is `releases/Map2Globe-<version>.zip`. The version is the one of `Map2Globe/metadata.txt`.

## Publishing on the QGIS plugin repository

1. Check `Map2Globe/metadata.txt` (version, changelog, author, e-mail, repository URLs).
2. Build the zip with `dev/build_zip.py`.
3. Upload it at https://plugins.qgis.org/plugins/add/ with an OSGeo account.
