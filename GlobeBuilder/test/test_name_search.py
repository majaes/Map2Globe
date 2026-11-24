# -*- coding: utf-8 -*-
import os

from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer

from ..core.utils.utils import get_geometries_center, load_name_centers
from ..definitions.settings import LOCAL_DATA_DIR

COUNTRIES_110M = os.path.join(LOCAL_DATA_DIR, 'ne_110m_admin_0_countries.geojson')


def _layer(wkt_list, crs="EPSG:4326"):
    layer = QgsVectorLayer("MultiPolygon?crs=" + crs, "test", "memory")
    features = []
    for wkt in wkt_list:
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromWkt(wkt))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    return layer


def test_center_of_bounding_box(qgis_new_project):
    layer = _layer(["MultiPolygon(((10 0, 20 0, 20 10, 10 10, 10 0)))"])
    geoms = [f.geometry() for f in layer.getFeatures()]
    assert get_geometries_center(geoms, layer.crs(), QgsProject.instance()) == {'lon': 15.0, 'lat': 5.0}


def test_nothing_to_center():
    assert get_geometries_center([], None, None) is None


def test_projected_geometries_are_converted_to_wgs84(qgis_new_project):
    # 10 degrees east on the equator is about 1113195 m in Web Mercator
    layer = _layer(["MultiPolygon(((1000000 -100000, 1226390 -100000, 1226390 100000, 1000000 100000, 1000000 -100000)))"],
                   crs="EPSG:3857")
    geoms = [f.geometry() for f in layer.getFeatures()]
    center = get_geometries_center(geoms, layer.crs(), QgsProject.instance())
    assert abs(center['lon'] - 10.0) < 0.01 and abs(center['lat']) < 0.01


def test_geometry_wrapping_the_antimeridian_uses_largest_part(qgis_new_project):
    # Fiji-like: big part east of 170, tiny part on the other side of the antimeridian
    layer = _layer(["MultiPolygon(((170 -20, 180 -20, 180 -10, 170 -10, 170 -20)),"
                    "((-180 -20, -179 -20, -179 -19, -180 -19, -180 -20)))"])
    geoms = [f.geometry() for f in layer.getFeatures()]
    assert get_geometries_center(geoms, layer.crs(), QgsProject.instance()) == {'lon': 175.0, 'lat': -15.0}


def test_original_geometry_is_not_modified(qgis_new_project):
    layer = _layer(["MultiPolygon(((1000000 0, 1100000 0, 1100000 100000, 1000000 100000, 1000000 0)))"],
                   crs="EPSG:3857")
    geom = next(layer.getFeatures()).geometry()
    before = geom.asWkt()
    get_geometries_center([geom], layer.crs(), QgsProject.instance())
    assert geom.asWkt() == before


def test_load_name_centers_from_bundled_countries(qgis_new_project):
    centers = load_name_centers(COUNTRIES_110M, 'NAME')
    assert len(centers) > 150
    assert 'Cameroon' in centers
    assert 8 < centers['Cameroon']['lon'] < 16 and 1 < centers['Cameroon']['lat'] < 13


def test_load_name_centers_unknown_field_or_file(qgis_new_project):
    assert load_name_centers(COUNTRIES_110M, 'NO_SUCH_FIELD') == {}
    assert load_name_centers(os.path.join(LOCAL_DATA_DIR, 'missing.geojson')) == {}
