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

import logging
import os

from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsProject, QgsCoordinateReferenceSystem, Qgis, QgsRasterLayer, QgsVectorLayer,
                       QgsMapThemeCollection, QgsLayoutItemMap,
                       QgsMapSettings, QgsRectangle, QgsLayoutPoint, QgsUnitTypes, QgsLayoutSize)

from .graticules import Graticules
from .halo import Halo
from .utils.utils import set_selection_based_style, get_feature_ids_that_intersect_bbox
from ..definitions.projections import Projections
from ..definitions.settings import (LayerConnectionType, S2CLOUDLESS_WMTS_URL, LOCAL_DATA_DIR,
                                    DEFAULT_LAYER_CONNECTION_TYPE, NATURAL_EARTH_BASE_URL,
                                    DEFAULT_ORIGIN,
                                    WGS84)
from ..qgis_plugin_tools.tools.custom_logging import bar_msg
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.resources import plugin_name
from ..qgis_plugin_tools.tools.settings import get_setting

LOGGER = logging.getLogger(plugin_name())


class Globe:
    THEME_NAME = tr('Globe')
    GROUP_NAME = tr('Globe')

    def __init__(self, iface, origin=DEFAULT_ORIGIN, projection=Projections.AZIMUTHAL_ORTHOGRAPHIC):
        self.iface = iface
        self.origin = origin
        self.projection = projection
        # noinspection PyArgumentList
        self.qgis_instance = QgsProject.instance()

    @property
    def group(self):
        root = self.qgis_instance.layerTreeRoot()
        groups = tuple(filter(lambda g: g.name() == Globe.GROUP_NAME,
                              filter(root.isGroup, root.children())))
        if len(groups) == 1:
            return groups[0]
        else:
            return root.addGroup(Globe.GROUP_NAME)

    # Layer names the plugin itself creates and is therefore safe to delete/recreate.
    # Layers manually added to the group by the user (e.g. their own basemap) are left untouched.
    MANAGED_LAYER_NAMES = {Halo.LAYER_NAME, Graticules.LAYER_NAME, tr(u'Countries'), tr(u'S2 Cloudless 2018')}

    def delete_group(self):
        group = self.group
        if group is not None:
            for child in list(group.children()):
                dump = child.dump()
                layer_id = dump.split("=")[-1].strip()
                layer = self.qgis_instance.mapLayer(layer_id)
                if layer is not None and layer.name() in Globe.MANAGED_LAYER_NAMES:
                    self.qgis_instance.removeMapLayer(layer_id)

    def set_origin(self, coordinates):
        if coordinates is not None:
            self.origin = coordinates

    def set_projection(self, projection):
        self.projection = projection

    def set_group_visibility(self, is_visible):
        self.group.setItemVisibilityCheckedRecursive(is_visible)

    def load_data(self, load_s2, load_countries, load_graticules, countries_color, graticules_color,
                  intersecting_countries_color, counties_res, graticules_res):
        existing_layer_names = self.get_existing_layer_names()
        s2_cloudless_layer_name = tr(u'S2 Cloudless 2018')
        if load_s2 and s2_cloudless_layer_name not in existing_layer_names:
            s2_layer = QgsRasterLayer(S2CLOUDLESS_WMTS_URL, s2_cloudless_layer_name, "wms")
            if s2_layer.isValid():
                self.insert_layer_to_group(s2_layer)
            else:
                LOGGER.warning(tr(u"Could not add Sentinel 2 Cloudless layer"), extra=bar_msg())

        ne_data = {}
        if load_countries:
            def style_countries(layer):
                if intersecting_countries_color is None:
                    layer.renderer().symbol().setColor(countries_color)
                else:
                    set_selection_based_style(layer, intersecting_countries_color, countries_color)
                    ids = get_feature_ids_that_intersect_bbox(layer, self.iface.mapCanvas().extent(),
                                                              self.qgis_instance.crs())
                    layer.select(ids)

            ne_data[tr(u'Countries')] = (
                'ne_{}_admin_0_countries.geojson'.format(counties_res), lambda l: style_countries(l))

        if len(ne_data):
            self.load_natural_earth_data(ne_data)

        gra = Graticules(graticules_res)
        if load_graticules:
            # Recreate rather than reuse so a changed color/resolution is always applied
            [self.qgis_instance.removeMapLayer(lyr.id()) for lyr in
             self.qgis_instance.mapLayersByName(gra.LAYER_NAME)]
            graticule_layer = gra.create_graticules(graticules_color)
            if graticule_layer.isValid():
                self.insert_layer_to_group(graticule_layer)
            else:
                LOGGER.warning(tr('Could not add graticules'), extra=bar_msg())

        self.iface.mapCanvas().refresh()

    def load_natural_earth_data(self, ne_data):
        connection_type = LayerConnectionType(
            get_setting("layerConnectionType", DEFAULT_LAYER_CONNECTION_TYPE.value, int))

        if connection_type == LayerConnectionType.local:
            root = LOCAL_DATA_DIR
        else:
            root = NATURAL_EARTH_BASE_URL

        for name, data in ne_data.items():
            source, styling_method = data
            source_path = os.path.join(root, source)
            existing = self.qgis_instance.mapLayersByName(name)
            layer = existing[0] if existing else None

            # Reload if the layer doesn't exist yet, or its source (e.g. resolution) changed
            if layer is None or os.path.normpath(layer.source()) != os.path.normpath(source_path):
                if layer is not None:
                    self.qgis_instance.removeMapLayer(layer.id())
                layer = QgsVectorLayer(source_path, name, "ogr")
                if not layer.isValid():
                    layer = QgsVectorLayer(os.path.join(LOCAL_DATA_DIR, source), name, "ogr")
                if not layer.isValid():
                    self.iface.messageBar().pushMessage(
                        tr(u"Could not load Natural Earth layer '{}'", name),
                        level=Qgis.Warning, duration=3)
                    layer = None
                else:
                    layer.setName(name)
                    self.insert_layer_to_group(layer)

            if styling_method is not None and layer is not None:
                styling_method(layer)
                layer.triggerRepaint()

    def insert_layer_to_group(self, layer, index=0):
        self.qgis_instance.addMapLayer(layer, False)
        self.group.insertLayer(index, layer)

    def change_project_projection(self):
        # Change to wgs84 to activate the changes in origin
        self.qgis_instance.setCrs(WGS84)
        proj_string = self.projection.value.proj_str(self.origin)
        crs = QgsCoordinateReferenceSystem()
        if not crs.createFromProj(proj_string):
            LOGGER.warning(tr(u"Could not create the globe's custom projection"), extra=bar_msg())
            return
        self.qgis_instance.setCrs(crs)

    def change_temporarily_to_globe_projection(self):
        crs = self.qgis_instance.crs()
        self.change_project_projection()
        self.qgis_instance.setCrs(crs)

    def change_background_color(self, new_background_color):
        # Write it to the project (will still need to be saved!)
        self.qgis_instance.writeEntry("Gui", "/CanvasColorRedPart", new_background_color.red())
        self.qgis_instance.writeEntry("Gui", "/CanvasColorGreenPart", new_background_color.green())
        self.qgis_instance.writeEntry("Gui", "/CanvasColorBluePart", new_background_color.blue())

        # And apply for the current session
        self.iface.mapCanvas().setCanvasColor(new_background_color)
        self.iface.mapCanvas().refresh()

    # noinspection PyArgumentList
    @staticmethod
    def get_existing_layer_names():
        return [layer.name() for layer in QgsProject.instance().mapLayers().values()]

    # noinspection PyArgumentList
    def add_halo(self, use_effects, stroke_color, fill_color=None, halo_with_fill=False):
        halo = Halo(self.iface, self.origin, self.projection)

        if halo_with_fill:
            self.add_halo(True, stroke_color)
        else:
            [self.qgis_instance.removeMapLayer(lyr.id()) for lyr in
             self.qgis_instance.mapLayersByName(halo.LAYER_NAME)]

        layer, index = halo.create_halo_layer(use_effects, stroke_color, fill_color)
        self.insert_layer_to_group(layer, index)

    def refresh_theme(self):
        theme_collection = self.qgis_instance.mapThemeCollection()
        layers = [layer.layer() for layer in self.group.findLayers()]
        if Globe.THEME_NAME in theme_collection.mapThemes():
            theme_collection.removeMapTheme(Globe.THEME_NAME)
        if len(layers):
            map_theme_record = QgsMapThemeCollection.MapThemeRecord()
            map_theme_record.setLayerRecords([QgsMapThemeCollection.MapThemeLayerRecord(layer) for layer in layers])
            theme_collection.insert(Globe.THEME_NAME, map_theme_record)

    LAYOUT_MAP_ITEM_ID = 'GlobeBuilderMap'

    def add_to_layout(self, layout, background_color=QColor(255, 255, 255, 0), size=80):
        """
        Inspired by https://opensourceoptions.com/blog/pyqgis-create-and-print-a-map-layout-with-python/
        """
        layers = [layer.layer() for layer in self.group.findLayers()]
        # Reuse the existing map item if this layout already has one, instead of stacking a
        # new one on top of it on every click (which made style/color changes look like they
        # weren't applied, since the old, unchanged item was still there covering the new one).
        map = layout.itemById(Globe.LAYOUT_MAP_ITEM_ID)
        is_new_item = map is None
        if is_new_item:
            map = QgsLayoutItemMap(layout)
            map.setId(Globe.LAYOUT_MAP_ITEM_ID)
            map.setRect(20, 20, 20, 20)
        # set the map extent
        ms = QgsMapSettings()
        ms.setLayers(layers)  # set layers to be mapped
        crs = QgsCoordinateReferenceSystem()
        if not crs.createFromProj(self.projection.value.proj_str(self.origin)):
            LOGGER.warning(tr(u"Could not create the globe's custom projection"), extra=bar_msg())
        map.setCrs(crs)
        map.setFollowVisibilityPreset(True)
        map.setFollowVisibilityPresetName(Globe.THEME_NAME)
        rect = QgsRectangle(ms.fullExtent())

        ms.setExtent(rect)
        map.setExtent(rect)
        map.setBackgroundColor(background_color)
        if is_new_item:
            layout.addLayoutItem(map)
            map.attemptMove(QgsLayoutPoint(5, 20, QgsUnitTypes.LayoutMillimeters))
            map.attemptResize(QgsLayoutSize(size, size, QgsUnitTypes.LayoutMillimeters))
        map.refresh()
