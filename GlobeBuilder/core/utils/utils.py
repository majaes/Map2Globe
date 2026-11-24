# -*- coding: utf-8 -*-


#  Copyright (C) 2020-2021 GlobeBuilder contributors.
#
#
#  This file is part of GlobeBuilder.
#
#  GlobeBuilder is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#
#  GlobeBuilder is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with GlobeBuilder.  If not, see <https://www.gnu.org/licenses/>.

import os
import shutil
import tempfile

from qgis.core import QgsApplication, QgsPrintLayout, QgsFillSymbol, QgsRuleBasedRenderer, QgsFeatureRequest, \
    QgsCoordinateTransformContext, QgsCoordinateTransform, QgsMapLayer, QgsRectangle, QgsWkbTypes

from ...definitions.settings import WGS84
from ...qgis_plugin_tools.tools.i18n import tr


def local_data_copy(source_path):
    """Return a copy of a bundled data file stored *outside* the plugin folder.

    Layers read their file for as long as they are in the project. If they read it straight from the
    plugin folder, Windows locks it and QGIS can no longer uninstall/upgrade the plugin ("Failed to
    remove directory"). The copy is refreshed whenever the bundled file changes. If the copy can't be
    made, the original path is returned so the plugin keeps working.
    """
    try:
        try:
            root = os.path.join(QgsApplication.qgisSettingsDirPath(), "GlobeBuilder_data")
        except Exception:
            root = os.path.join(tempfile.gettempdir(), "GlobeBuilder_data")
        os.makedirs(root, exist_ok=True)
        target = os.path.join(root, os.path.basename(source_path))
        src_stat = os.stat(source_path)
        if (not os.path.exists(target) or os.path.getsize(target) != src_stat.st_size
                or os.path.getmtime(target) < src_stat.st_mtime):
            shutil.copy2(source_path, target)
        return target
    except OSError:
        return source_path


def create_layout(layout_name, qgis_instance):
    """Return the existing layout named layout_name, or create a new one if none exists."""
    manager = qgis_instance.layoutManager()
    for layout in manager.printLayouts():
        if layout.name() == layout_name:
            return layout
    layout = QgsPrintLayout(qgis_instance)
    layout.initializeDefaults()
    layout.setName(layout_name)
    manager.addLayout(layout)
    return layout


def set_selection_based_style(layer, s_color, else_color):
    # noinspection PyCallByClass,PyArgumentList
    fill_for_selected = QgsFillSymbol.createSimple({'color': 'blue'})
    fill_for_selected.setColor(s_color)
    rule_s = QgsRuleBasedRenderer.Rule(fill_for_selected, label=tr(u"Selected"),
                                       filterExp="is_selected()")

    fill_for_else = fill_for_selected.clone()
    fill_for_else.setColor(else_color)
    rule_else = QgsRuleBasedRenderer.Rule(fill_for_else, label=tr(u"Not Selected"),
                                          elseRule=True)

    renderer = QgsRuleBasedRenderer(QgsRuleBasedRenderer.Rule(None))
    root_rule = renderer.rootRule()
    root_rule.appendChild(rule_s)
    root_rule.appendChild(rule_else)

    layer.setRenderer(renderer)
    return layer


def transform_to_wgs84(geom, crs, qgis_instance):
    transformer = QgsCoordinateTransform(crs, WGS84, qgis_instance)
    return transformer.transform(geom)


def get_feature_ids_that_intersect_bbox(layer, rect, crs):
    request = (QgsFeatureRequest()
               .setFilterRect(rect)
               .setDestinationCrs(crs=crs, context=QgsCoordinateTransformContext())
               .setNoAttributes().setFlags(QgsFeatureRequest.NoGeometry))
    return [f.id() for f in layer.getFeatures(request)]


def get_map_center_coordinates(iface, qgis_instance, frmt="{:.0f}"):
    center_point = iface.mapCanvas().extent().center()
    center_point = transform_to_wgs84(center_point, qgis_instance.crs(),
                                      qgis_instance)
    center = {'lon': float(frmt.format(center_point.x())), 'lat': float(frmt.format(center_point.y()))}
    return center


def find_layer_with_selection(project, active_layer=None):
    """Return the vector layer whose selection should be used: the active layer if it has one,
    otherwise the first project vector layer with selected features (else None)."""
    def has_selection(layer):
        return (layer is not None and layer.type() == QgsMapLayer.VectorLayer
                and layer.selectedFeatureCount() > 0)

    if has_selection(active_layer):
        return active_layer
    for layer in project.mapLayers().values():
        if has_selection(layer):
            return layer
    return None


def get_selection_center(layer, project, decimals=4):
    """Longitude/latitude (WGS84) of the centre of the layer's selected features, or None.

    The centre of the bounding box is used. A selection that wraps around the antimeridian
    (e.g. USA, Russia, Fiji: bounding box wider than 180 degrees) would otherwise get a centre
    on the wrong side of the world, so the largest part of the selection is used instead.
    """
    geometries = [f.geometry() for f in layer.selectedFeatures() if f.hasGeometry() and not f.geometry().isEmpty()]
    if not geometries:
        return None

    transform = None
    if layer.crs() != WGS84:
        transform = QgsCoordinateTransform(layer.crs(), WGS84, project)
    rect = QgsRectangle()
    rect.setNull()
    parts = []
    for geom in geometries:
        geom = type(geom)(geom)  # copy: never alter the layer's own geometry
        if transform is not None:
            geom.transform(transform)
        rect.combineExtentWith(geom.boundingBox())
        parts.extend(geom.asGeometryCollection())

    if rect.width() > 180 and parts:
        polygon_parts = [p for p in parts if QgsWkbTypes.geometryType(p.wkbType()) == QgsWkbTypes.PolygonGeometry]
        pool = polygon_parts or parts
        biggest = max(pool, key=lambda p: p.area() if polygon_parts else p.length())
        rect = biggest.boundingBox()

    center = rect.center()
    return {'lon': round(center.x(), decimals), 'lat': round(max(-90.0, min(90.0, center.y())), decimals)}
