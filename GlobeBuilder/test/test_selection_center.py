# -*- coding: utf-8 -*-
from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer

from ..core.utils.utils import find_layer_with_selection, get_selection_center


def _layer(wkt_list, crs="EPSG:4326", name="test"):
    layer = QgsVectorLayer("MultiPolygon?crs=" + crs, name, "memory")
    features = []
    for wkt in wkt_list:
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromWkt(wkt))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    return layer


def test_no_selection(qgis_new_project):
    layer = _layer(["MultiPolygon(((10 0, 20 0, 20 10, 10 10, 10 0)))"])
    QgsProject.instance().addMapLayer(layer)
    assert get_selection_center(layer, QgsProject.instance()) is None
    assert find_layer_with_selection(QgsProject.instance()) is None


def test_center_of_selected_feature(qgis_new_project):
    layer = _layer(["MultiPolygon(((10 0, 20 0, 20 10, 10 10, 10 0)))",
                    "MultiPolygon(((-50 -40, -40 -40, -40 -30, -50 -30, -50 -40)))"])
    QgsProject.instance().addMapLayer(layer)
    layer.selectByIds([1])
    assert find_layer_with_selection(QgsProject.instance()) is layer
    assert get_selection_center(layer, QgsProject.instance()) == {'lon': 15.0, 'lat': 5.0}


def test_active_layer_is_preferred(qgis_new_project):
    a = _layer(["MultiPolygon(((0 0, 1 0, 1 1, 0 1, 0 0)))"], name="a")
    b = _layer(["MultiPolygon(((0 0, 1 0, 1 1, 0 1, 0 0)))"], name="b")
    QgsProject.instance().addMapLayers([a, b])
    a.selectAll()
    b.selectAll()
    assert find_layer_with_selection(QgsProject.instance(), b) is b


def test_projected_layer_is_converted_to_wgs84(qgis_new_project):
    # 10 degrees east of Greenwich on the equator is about 1113195 m in Web Mercator
    layer = _layer(["MultiPolygon(((1000000 -100000, 1226390 -100000, 1226390 100000, 1000000 100000, 1000000 -100000)))"],
                   crs="EPSG:3857")
    QgsProject.instance().addMapLayer(layer)
    layer.selectAll()
    center = get_selection_center(layer, QgsProject.instance())
    assert abs(center['lon'] - 10.0) < 0.01 and abs(center['lat']) < 0.01


def test_selection_wrapping_the_antimeridian_uses_largest_part(qgis_new_project):
    # Fiji-like: big part east of 170, tiny part on the other side of the antimeridian
    layer = _layer(["MultiPolygon(((170 -20, 180 -20, 180 -10, 170 -10, 170 -20)),"
                    "((-180 -20, -179 -20, -179 -19, -180 -19, -180 -20)))"])
    QgsProject.instance().addMapLayer(layer)
    layer.selectAll()
    center = get_selection_center(layer, QgsProject.instance())
    assert center == {'lon': 175.0, 'lat': -15.0}
