# -*- coding: utf-8 -*-
"""Standalone dev harness: opens the Map2Globe panel next to a real map canvas, without QGIS.

Run with the QGIS Python (no plugin install / reload needed, just re-run after each edit):

    & "C:\\Program Files\\QGIS 4.0.1\\bin\\python-qgis.bat" dev\\harness.py [--fr] [--auto out.png]

  --fr          install the French translation (as the plugin does when QGIS is in French)
  --auto FILE   click "Switch the map to a globe", save a screenshot of the window to FILE and quit
                (handy for a quick visual check, also works headless with QT_QPA_PLATFORM=offscreen)
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

parser = argparse.ArgumentParser()
parser.add_argument("--fr", action="store_true")
parser.add_argument("--auto", metavar="FILE")
parser.add_argument("--shrink", action="store_true", help="with --auto: shrink the canvas after building (like a panel opening)")
parser.add_argument("--apply-country", metavar="NAME", nargs="+", help="with --auto: after building, centre on this country and click Apply changes")
parser.add_argument("--none", action="store_true", help="with --auto: halo type None (countries only)")
parser.add_argument("--flat", nargs="?", const="outline", choices=["outline", "halo"], help="with --auto: use oceans, build the globe, then switch back to flat")
args = parser.parse_args()

from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsLayerTreeModel, QgsProject
from qgis.gui import QgsLayerTreeView, QgsMapCanvas, QgsLayerTreeMapCanvasBridge, QgsMessageBar
from qgis.PyQt.QtCore import Qt, QTimer, QCoreApplication
from qgis.PyQt.QtWidgets import QDockWidget, QMainWindow

app = QgsApplication([], True)
app.initQgis()

# Processing is needed to build the graticules (it is available inside real QGIS).
qgis_plugins = os.path.join(QgsApplication.pkgDataPath(), "python", "plugins")
sys.path.append(qgis_plugins)
import processing  # noqa: E402
from processing.core.Processing import Processing  # noqa: E402
from qgis.analysis import QgsNativeAlgorithms  # noqa: E402

Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

from Map2Globe.definitions.language import set_language
set_language("fr" if args.fr else "en", remember=False)

from Map2Globe.ui.map2globe_dockwidget import Map2GlobeDockWidget  # noqa: E402


class FakeIface:
    """Minimal QgisInterface: just what the plugin uses."""

    def __init__(self, window, canvas, bar, bridge=None):
        self._window, self._canvas, self._bar, self._bridge = window, canvas, bar, bridge

    def mapCanvas(self):
        return self._canvas

    def messageBar(self):
        return self._bar

    def mainWindow(self):
        return self._window

    def layerTreeCanvasBridge(self):
        return self._bridge


window = QMainWindow()
window.setWindowTitle("Map2Globe - dev harness")
window.resize(1400, 850)
canvas = QgsMapCanvas()
canvas.setCanvasColor(Qt.GlobalColor.white)
window.setCentralWidget(canvas)
bar = QgsMessageBar(canvas)
project = QgsProject.instance()
bridge = QgsLayerTreeMapCanvasBridge(project.layerTreeRoot(), canvas)  # keeps the canvas in sync with the project
project.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))  # what a new QGIS project starts with

# QGIS keeps the canvas CRS in sync with the project CRS; the bridge doesn't do that part.
project.crsChanged.connect(lambda: canvas.setDestinationCrs(project.crs()))

# A real Layers panel, like QGIS': shows the layer symbols and the 'temporary layer' indicator
layer_model = QgsLayerTreeModel(project.layerTreeRoot())
layer_model.setFlag(QgsLayerTreeModel.ShowLegend)
layer_view = QgsLayerTreeView()
layer_view.setModel(layer_model)
layers_dock = QDockWidget('Layers')
layers_dock.setWidget(layer_view)
window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, layers_dock)

iface = FakeIface(window, canvas, bar, bridge)
iface.layerTreeView = lambda: layer_view
dock = Map2GlobeDockWidget(iface)
window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
window.resizeDocks([dock], [540], Qt.Orientation.Horizontal)
window.show()
print("dock minimumSizeHint:", dock.minimumSizeHint().width(), "x", dock.minimumSizeHint().height())

if args.auto:
    def _auto():
        if args.apply_country:
            dock.radioButtonHFillWithHalo.setChecked(True)
        if args.none:
            dock.radioButtonHNone.setChecked(True)
        if args.flat:
            (dock.radioButtonHFillWithHalo if args.flat == "halo" else dock.radioButtonHFill).setChecked(True)
        dock.pushButtonRun.click()
        if args.flat:
            QTimer.singleShot(1500, dock.pushButtonFlatMap.click)
        if args.apply_country:
            def _apply(name):
                dock.radioButtonName.setChecked(True)
                dock.comboBoxNames.setCurrentText(name)
                dock.pushButtonApplyVisualizations.click()
            for i, name in enumerate(args.apply_country):
                QTimer.singleShot(1500 * (i + 1), lambda name=name: _apply(name))
        if args.shrink:
            QTimer.singleShot(1500, lambda: canvas.setFixedHeight(330))
        QTimer.singleShot(1500 * (len(args.apply_country) + 2) if args.apply_country else 2500 if not args.flat else 4000 if not args.shrink else 4500, _grab)

    def _grab():
        canvas.waitWhileRendering()
        app.processEvents()
        print("canvas layers:", [l.name() for l in canvas.layers()], "extent:", canvas.extent().toString(0),
              "crs:", canvas.mapSettings().destinationCrs().toProj()[:30], "size:", canvas.size().width(), canvas.size().height())
        print("crs:", project.crs().authid(), project.crs().description())
        for l in project.mapLayers().values():
            print("layer:", l.name(), l.crs().authid(), l.crs().description(), l.extent().toString(0))
        print("tree:", [(n.layer().name(), n.itemVisibilityChecked()) for n in project.layerTreeRoot().findLayers()])
        window.grab().save(args.auto)
        print("screenshot:", args.auto)
        app.quit()

    QTimer.singleShot(500, _auto)

code = app.exec()
app.exitQgis()
sys.exit(code)
