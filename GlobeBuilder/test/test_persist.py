# -*- coding: utf-8 -*-
import os

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsCoordinateReferenceSystem, QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer

from ..core.globe import Globe
from ..core.utils.utils import data_dir, persist_layer
from ..definitions.projections import Projections
from ..definitions.translations import TRANSLATIONS, DictTranslator
from ..qgis_plugin_tools.tools.i18n import tr

ORTHO = "+proj=ortho +lat_0=42.5 +lon_0=0.5 +x_0=0 +y_0=0 +a=6370997 +b=6370997 +units=m +no_defs +type=crs"


def _memory_layer(crs_string=ORTHO):
    layer = QgsVectorLayer("Polygon", "tmp", "memory")
    crs = QgsCoordinateReferenceSystem()
    assert crs.createFromProj(crs_string)
    layer.setCrs(crs)
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromPointXY(__import__("qgis.core", fromlist=["x"]).QgsPointXY(0, 0)).buffer(1000, 16))
    layer.dataProvider().addFeatures([feature])
    return layer


def test_persisted_layer_is_a_file_layer_with_the_same_content(qgis_new_project):
    layer = _memory_layer()
    assert layer.isTemporary()
    saved = persist_layer(layer, "pytest_layer", "Some name")
    assert saved.isValid()
    assert saved.dataProvider().name() == "ogr"
    assert not saved.isTemporary()
    assert saved.name() == "Some name"
    assert saved.featureCount() == 1
    assert os.path.dirname(saved.source().split("|")[0]) == os.path.normpath(data_dir()) or \
        os.path.normpath(os.path.dirname(saved.source().split("|")[0])) == os.path.normpath(data_dir())


def test_custom_globe_crs_survives_the_roundtrip(qgis_new_project):
    saved = persist_layer(_memory_layer(), "pytest_crs", "crs")
    assert "+proj=ortho" in saved.crs().toProj()
    assert abs(saved.extent().width() - 2000) < 1


def test_persist_falls_back_to_the_original_layer_on_error(qgis_new_project):
    layer = QgsVectorLayer("Polygon", "broken", "memory")
    layer.setDataSource("nowhere", "broken", "ogr")  # invalid layer: can't be written
    assert persist_layer(layer, "pytest_broken") is layer


def test_halo_oceans_and_graticules_are_not_temporary(globe):
    globe.add_halo(False, QColor('#ffffff'), QColor('#a6cee3'), halo_with_fill=True)
    for node in globe.group.findLayers():
        assert not node.layer().isTemporary(), node.layer().name()
        assert node.layer().dataProvider().name() == "ogr"
    assert [n.layer().name() for n in globe.group.findLayers()] == ["Halo", "Oceans"]


def test_rebuilding_replaces_the_layer_and_keeps_it_persistent(globe):
    for color in ('#ff0000', '#00ff00', '#0000ff'):
        globe.add_halo(False, QColor('#ffffff'), QColor(color))
    layers = QgsProject.instance().mapLayersByName("Oceans")
    assert len(layers) == 1 and not layers[0].isTemporary()
    assert layers[0].renderer().symbol().color() == QColor('#0000ff')


def test_countries_layer_is_called_pays_in_french():
    translator = DictTranslator(TRANSLATIONS["fr"])
    QCoreApplication.installTranslator(translator)
    try:
        assert tr(u'Countries') == "Pays"
        assert tr(u'Halo') == "Halo" and tr(u'Oceans') == "Oceans"  # layer names stay as they are
        names = Globe.managed_layer_names()
        assert "Pays" in names and "Countries" in names  # old projects keep working
    finally:
        QCoreApplication.removeTranslator(translator)


def test_refresh_legend_without_a_layer_tree_view_is_harmless(globe):
    layer = QgsVectorLayer("Polygon", "x", "memory")
    globe.refresh_legend(layer)  # the mocked iface has no layerTreeView(): must not raise
