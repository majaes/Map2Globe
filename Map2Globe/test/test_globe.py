# coding=utf-8


#  Copyright (C) 2026 ANABA MANGA.
#  Copyright (C) 2020-2021 GlobeBuilder contributors.
#
#
#  This file is part of Map2Globe.
#
#  Map2Globe is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#
#  Map2Globe is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Map2Globe.  If not, see <https://www.gnu.org/licenses/>.

import pytest
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsCoordinateReferenceSystem, QgsProject, QgsProcessingException, Qgis, QgsVectorLayer

from ..core.globe import Globe
from ..definitions.projections import Projections
from ..definitions.settings import (DEFAULT_ORIGIN, DEFAULT_COUNTRIES_COLOR, DEFAULT_HALO_COLOR,
                                    DEFAULT_HALO_FILL_COLOR)


def test_projection_change_with_default_origin(globe):
    """Test if projection really changes"""
    globe.set_projection(Projections.AZIMUTHAL_ORTHOGRAPHIC)
    globe.change_project_projection()
    expeted_proj = Projections.AZIMUTHAL_ORTHOGRAPHIC.value.proj_str(DEFAULT_ORIGIN).replace(' +type=crs', '')
    # toProj() never reports the +type=crs marker
    assert QgsProject.instance().crs().toProj() == expeted_proj


def test_projection_change_with_custom_origin(globe):
    """Test if projection really changes"""
    custom_origin = {'lat': 10, 'lon': 10}
    globe.set_origin(custom_origin)
    globe.change_project_projection()
    expeted_proj = Projections.AZIMUTHAL_ORTHOGRAPHIC.value.proj_str(custom_origin).replace(' +type=crs', '')
    assert QgsProject.instance().crs().toProj() == expeted_proj


def test_loading_countries(globe, qgis_iface, qgis_canvas):
    """Test loading data"""
    assert len(qgis_iface.getMockLayers()) == 0
    globe.load_data(False, True, False, QColor(Qt.GlobalColor.blue), QColor(Qt.GlobalColor.blue), '50m', 10)
    names = get_existing_layer_names(qgis_iface, qgis_canvas)
    assert "Countries" in names


@pytest.mark.skip('TODO: figure way to test processing')
def test_loading_graticules(globe, qgis_iface, qgis_canvas):
    """Test loading data"""
    assert len(qgis_iface.getMockLayers()) == 0
    globe.load_data(False, False, True, QColor(Qt.GlobalColor.blue), QColor(Qt.GlobalColor.blue), '50m', 10)
    names = get_existing_layer_names(qgis_iface, qgis_canvas)
    assert "Graticules" in names


def test_loading_s2cloudless(globe, qgis_iface, qgis_canvas):
    """Test loading data"""
    assert len(qgis_iface.getMockLayers()) == 0
    globe.load_data(True, False, False, QColor(Qt.GlobalColor.blue), QColor(Qt.GlobalColor.blue), '50m', 10)
    names = get_existing_layer_names(qgis_iface, qgis_canvas)
    assert "S2 Cloudless 2018" in names


def test_loading_s2cloudless_countries_and_graticules(globe, qgis_iface, qgis_canvas, qgis_processing):
    """Test loading data"""
    assert len(qgis_iface.getMockLayers()) == 0
    try:
        globe.load_data(True, True, True, QColor(Qt.GlobalColor.blue), QColor(Qt.GlobalColor.blue), '50m', 10)
        names = get_existing_layer_names(qgis_iface, qgis_canvas)
        expected_names = {"Graticules", "S2 Cloudless 2018", "Countries"}
        assert names == expected_names
    except QgsProcessingException:
        # In QGIS 3.10 docker image, the algorithm native:creategrid seems to be missing...
        if not Qgis.QGIS_VERSION.startswith("3.10"):
            raise


def test_background_color_changing(globe, qgis_canvas):
    """Test if background color really changes"""
    expected_b_color = QColor(Qt.GlobalColor.blue)
    globe.change_background_color(expected_b_color)
    new_background_color = qgis_canvas.canvasColor()
    assert new_background_color == expected_b_color


def test_adding_halo(globe, qgis_iface, qgis_canvas):
    globe.add_halo(True, QColor(Qt.GlobalColor.blue))
    names = get_existing_layer_names(qgis_iface, qgis_canvas)
    assert "Halo" in names


def test_halo_without_fill_stays_a_halo(globe, qgis_iface, qgis_canvas):
    globe.add_halo(False, QColor('#ffffff'))
    names = get_existing_layer_names(qgis_iface, qgis_canvas)
    assert "Halo" in names and "Oceans" not in names


def test_filled_halo_layer_is_the_oceans_layer(globe, qgis_iface, qgis_canvas):
    globe.add_halo(False, QColor('#ffffff'), QColor('#a6cee3'))
    names = get_existing_layer_names(qgis_iface, qgis_canvas)
    assert "Oceans" in names and "Halo" not in names
    layers = [node.layer() for node in globe.group.findLayers()]
    # at the very bottom, with the requested fill colour
    assert layers[-1].name() == "Oceans"
    assert layers[-1].renderer().symbol().color() == QColor('#a6cee3')
    assert layers[-1].featureCount() == 1


def test_halo_with_fill_gives_a_halo_on_top_and_oceans_at_the_bottom(globe):
    globe.add_halo(False, QColor('#ffffff'), QColor('#a6cee3'), halo_with_fill=True)
    names = [node.layer().name() for node in globe.group.findLayers()]
    assert names == ["Halo", "Oceans"]


def test_oceans_are_replaced_not_duplicated(globe):
    globe.add_halo(False, QColor('#ffffff'), QColor(Qt.GlobalColor.red))
    globe.add_halo(False, QColor('#ffffff'), QColor(Qt.GlobalColor.green))
    layers = QgsProject.instance().mapLayersByName("Oceans")
    assert len(layers) == 1
    assert layers[0].renderer().symbol().color() == QColor(Qt.GlobalColor.green)


def test_remove_halo_removes_halo_and_oceans(globe):
    globe.add_halo(False, QColor('#ffffff'), QColor('#a6cee3'), halo_with_fill=True)
    globe.remove_halo()
    assert not QgsProject.instance().mapLayersByName("Halo")
    assert not QgsProject.instance().mapLayersByName("Oceans")


def test_no_globe_in_an_empty_project(globe):
    assert Globe.find_group() is None
    assert not Globe.exists_in_map()
    # the check must not create the group as a side effect
    assert Globe.find_group() is None


def test_globe_exists_in_map_only_while_visible(globe):
    globe.add_halo(False, QColor('#ffffff'), QColor('#a6cee3'))
    globe.change_project_projection()
    assert Globe.exists_in_map()
    globe.set_group_visibility(False)
    assert not Globe.exists_in_map()
    globe.set_group_visibility(True)
    assert Globe.exists_in_map()


def test_foreign_layers_in_the_group_are_not_a_globe(globe):
    layer = QgsVectorLayer("Polygon", "my own layer", "memory")
    QgsProject.instance().addMapLayer(layer, False)
    globe.group.insertLayer(0, layer)
    assert not Globe.exists_in_map()


def test_flat_map_keeps_the_plugin_layers_and_hides_the_globe_shaped_ones(globe):
    globe.load_data(False, True, False, QColor(Qt.GlobalColor.blue), QColor(Qt.GlobalColor.blue), '110m', 10)
    globe.add_halo(False, QColor('#ffffff'), QColor('#a6cee3'), halo_with_fill=True)
    globe.change_project_projection()
    assert Globe.exists_in_map()
    globe.show_flat_map()
    nodes = {node.layer().name(): node for node in globe.group.findLayers()}
    assert set(nodes) == {"Countries", "Halo", "Oceans"}  # nothing deleted
    assert nodes["Countries"].itemVisibilityChecked()
    # the halo and the oceans are those of a flat map: visible, in WGS84, covering the whole world
    assert nodes["Halo"].itemVisibilityChecked() and nodes["Halo"].layer().crs().authid() == "EPSG:4326"
    # the oceans are now those of a flat map: visible, in WGS84, covering the whole world
    assert nodes["Oceans"].itemVisibilityChecked() and nodes["Oceans"].layer().crs().authid() == "EPSG:4326"
    assert nodes["Oceans"].layer().extent().width() == 360
    assert not Globe.exists_in_map()  # the map is flat again: "Apply changes" must be disabled


def test_oceans_disc_becomes_world_oceans_when_the_map_is_flat_by_any_means(globe):
    globe.add_halo(False, QColor("#ffffff"), QColor("#a6cee3"), halo_with_fill=True)
    globe.change_project_projection()
    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    globe.adapt_to_flat_map()
    nodes = {node.layer().name(): node for node in globe.group.findLayers()}
    assert nodes["Halo"].layer().extent().width() == 360 and nodes["Halo"].itemVisibilityChecked()
    assert nodes["Oceans"].layer().extent().width() == 360 and nodes["Oceans"].itemVisibilityChecked()
    globe.adapt_to_flat_map()  # idempotent: no second Oceans layer
    assert len(Globe.layers_named("Oceans")) == 1 and len(Globe.layers_named("Halo")) == 1


def test_flat_map_keeps_layers_added_by_the_user(globe):
    own = QgsVectorLayer("Polygon", "my own layer", "memory")
    QgsProject.instance().addMapLayer(own, False)
    globe.group.insertLayer(0, own)
    globe.add_halo(False, QColor('#ffffff'), QColor('#a6cee3'))
    globe.change_project_projection()
    globe.show_flat_map()
    assert "my own layer" in [node.layer().name() for node in globe.group.findLayers()]


def test_flat_map_restores_the_flat_projection(globe):
    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
    globe.remember_flat_state()
    globe.add_halo(False, QColor('#ffffff'), QColor('#a6cee3'))
    globe.change_project_projection()
    assert Globe.is_globe_crs(QgsProject.instance().crs())
    globe.remember_flat_state()  # building again must not "remember" the globe CRS
    globe.show_flat_map()
    assert QgsProject.instance().crs().authid() == "EPSG:3857"
    assert not QgsProject.instance().readEntry("Map2Globe", "flat_crs", "")[1]


def test_flat_map_without_remembered_state_falls_back_to_wgs84(globe):
    globe.add_halo(False, QColor('#ffffff'), QColor('#a6cee3'))
    globe.change_project_projection()
    globe.show_flat_map()
    assert QgsProject.instance().crs().authid() == "EPSG:4326"


def test_globe_crs_is_named_and_a_single_entry_is_reused(globe):
    names = []
    ids = []
    for origin in ({'lat': 3.0, 'lon': 11.0}, {'lat': 42.5, 'lon': 0.5}, {'lat': -17.0, 'lon': 178.0}):
        globe.set_origin(origin)
        globe.change_project_projection()
        crs = QgsProject.instance().crs()
        names.append(crs.description())
        ids.append(crs.authid())
        assert "lat_0={}".format(origin['lat']) in crs.toProj()  # the entry follows the origin
    assert all(name == "Map2Globe - Azimuthal Orthographic" for name in names)
    assert len(set(ids)) == 1 and ids[0].startswith("USER:")
    assert Globe.is_globe_crs(QgsProject.instance().crs())
    assert not Globe.is_globe_crs(QgsCoordinateReferenceSystem("EPSG:4326"))


def test_adding_oceans_keeps_the_canvas_color(globe, qgis_canvas):
    before = qgis_canvas.canvasColor()
    globe.add_halo(False, QColor('#ffffff'), QColor('#a6cee3'))
    assert qgis_canvas.canvasColor() == before


def test_default_colors():
    assert DEFAULT_COUNTRIES_COLOR.name() == '#ffe9a8'
    assert DEFAULT_HALO_COLOR.name() == '#ffffff'
    assert DEFAULT_HALO_FILL_COLOR.name() == '#a6cee3'


def test_group(globe):
    group = globe.group
    children = QgsProject.instance().layerTreeRoot().children()
    assert group in children


def get_existing_layer_names(qgis_iface, qgis_canvas):
    return {layer.name() for layer in qgis_iface.getMockLayers() + qgis_canvas.layers()}
