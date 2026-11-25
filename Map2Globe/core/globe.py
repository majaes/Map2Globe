# -*- coding: utf-8 -*-


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

import logging
import os

from qgis.PyQt.QtCore import QTimer
from qgis.core import (QgsApplication, QgsProject, QgsCoordinateReferenceSystem, Qgis, QgsRasterLayer, QgsVectorLayer,
                       QgsMapSettings, QgsRectangle, QgsFeature, QgsGeometry, QgsPointXY, QgsFillSymbol)

from .graticules import Graticules
from .halo import Halo
from .utils.utils import crs_from_proj, local_data_copy, persist_layer
from ..definitions.language import TrAttr, all_names
from ..definitions.projections import Projections
from ..definitions.settings import (LayerConnectionType, S2CLOUDLESS_WMTS_URL, LOCAL_DATA_DIR,
                                    DEFAULT_LAYER_CONNECTION_TYPE, NATURAL_EARTH_BASE_URL,
                                    DEFAULT_ORIGIN, DEFAULT_HALO_FILL_COLOR, DEFAULT_HALO_COLOR, HaloDrawMethod,
                                    WGS84)
from ..qgis_plugin_tools.tools.custom_logging import bar_msg
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.resources import plugin_name
from ..qgis_plugin_tools.tools.settings import get_setting

LOGGER = logging.getLogger(plugin_name())


class Globe:
    GROUP_NAME = TrAttr('Globe')
    # msgids of the layers built by the plugin (their names are translated)
    LAYER_MSGIDS = (u'Halo', u'Oceans', u'Graticules', u'Countries', u'S2 Cloudless 2018')

    def __init__(self, iface, origin=DEFAULT_ORIGIN, projection=Projections.AZIMUTHAL_ORTHOGRAPHIC):
        self.iface = iface
        self.origin = origin
        self.projection = projection
        # noinspection PyArgumentList
        self.qgis_instance = QgsProject.instance()

    @property
    def group(self):
        root = self.qgis_instance.layerTreeRoot()
        group_names = all_names(u'Globe')
        groups = tuple(filter(lambda g: g.name() in group_names,
                              filter(root.isGroup, root.children())))
        if len(groups) == 1:
            return groups[0]
        else:
            return root.addGroup(Globe.GROUP_NAME)

    # Layer names the plugin itself creates and is therefore safe to delete/recreate.
    # Layers manually added to the group by the user (e.g. their own basemap) are left untouched.
    @staticmethod
    def managed_layer_names():
        """Names of the layers built by the plugin, in every language (a project can come from another one)."""
        names = set()
        for msgid in Globe.LAYER_MSGIDS:
            names |= all_names(msgid)
        return names

    @staticmethod
    def layers_named(msgid):
        """The project's layers called `msgid`, in whatever language they were named."""
        names = all_names(msgid)
        return [layer for layer in QgsProject.instance().mapLayers().values() if layer.name() in names]

    # How long QGIS' "set CRS from the first layer" step is kept off after building the globe (ms).
    # That step runs deferred, i.e. after the code building the globe has returned.
    AUTO_CRS_SETUP_SUSPENSION_MS = 1500

    def suspend_auto_crs_setup(self):
        """Stop QGIS from resetting the project CRS to the first layer's CRS while the globe is built.

        When the first layers are added to a project, QGIS' layer tree/canvas bridge deferredly sets
        the project CRS (and extent) from the first layer, i.e. EPSG:4326 for the countries. That
        silently undid the globe projection (flat world map) in a project without layers.
        """
        get_bridge = getattr(self.iface, "layerTreeCanvasBridge", None)
        bridge = get_bridge() if get_bridge is not None else None
        if bridge is None:
            return
        if bridge.autoSetupOnFirstLayer():
            bridge.setAutoSetupOnFirstLayer(False)
            self._auto_crs_setup_bridge = bridge
        else:
            bridge = getattr(self, "_auto_crs_setup_bridge", None)
            if bridge is None:
                return  # it was already off before us: not ours to switch back on
        QTimer.singleShot(Globe.AUTO_CRS_SETUP_SUSPENSION_MS, self._restore_auto_crs_setup)

    def _restore_auto_crs_setup(self):
        bridge = getattr(self, "_auto_crs_setup_bridge", None)
        if bridge is not None:
            bridge.setAutoSetupOnFirstLayer(True)
            self._auto_crs_setup_bridge = None

    @staticmethod
    def find_group():
        """The Globe group, or None. Unlike the `group` property it never creates the group."""
        root = QgsProject.instance().layerTreeRoot()
        for child in root.children():
            if root.isGroup(child) and child.name() in all_names(u'Globe'):
                return child
        return None

    @staticmethod
    def exists_in_map():
        """True if a globe built by the plugin is currently shown: its layers are visible and the project
        uses the globe's projection (after "Switch the map to flat" the layers stay but the map is flat again)."""
        if not Globe.is_globe_crs(QgsProject.instance().crs()):
            return False
        group = Globe.find_group()
        if group is None:
            return False
        managed = Globe.managed_layer_names()
        nodes = [node for node in group.findLayers()
                 if node.layer() is not None and node.layer().name() in managed]
        return bool(nodes) and group.itemVisibilityChecked() and any(n.itemVisibilityChecked() for n in nodes)

    def set_origin(self, coordinates):
        if coordinates is not None:
            self.origin = coordinates

    def set_projection(self, projection):
        self.projection = projection

    def set_group_visibility(self, is_visible):
        self.group.setItemVisibilityCheckedRecursive(is_visible)

    def load_data(self, load_s2, load_countries, load_graticules, countries_color, graticules_color,
                  counties_res, graticules_res):
        s2_cloudless_layer_name = tr(u'S2 Cloudless 2018')
        if load_s2 and not Globe.layers_named(u'S2 Cloudless 2018'):
            s2_layer = QgsRasterLayer(S2CLOUDLESS_WMTS_URL, s2_cloudless_layer_name, "wms")
            if s2_layer.isValid():
                self.insert_layer_to_group(s2_layer)
            else:
                LOGGER.warning(tr(u"Could not add Sentinel 2 Cloudless layer"), extra=bar_msg())

        ne_data = {}
        if load_countries:
            def style_countries(layer):
                layer.renderer().symbol().setColor(countries_color)

            ne_data[u'Countries'] = (
                'ne_{}_admin_0_countries.geojson'.format(counties_res), lambda l: style_countries(l))

        if len(ne_data):
            self.load_natural_earth_data(ne_data)

        gra = Graticules(graticules_res)
        if load_graticules:
            # Recreate rather than reuse so a changed color/resolution is always applied
            [self.qgis_instance.removeMapLayer(lyr.id()) for lyr in Globe.layers_named(u'Graticules')]
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

        for msgid, data in ne_data.items():
            name = tr(msgid)
            source, styling_method = data
            source_path = os.path.join(root, source)
            if connection_type == LayerConnectionType.local:
                # Don't let layers lock files inside the plugin folder (breaks upgrades on Windows)
                source_path = local_data_copy(source_path)
            # The layer may carry another language's name (older version, project from another language)
            existing = Globe.layers_named(msgid)
            layer = existing[0] if existing else None
            if layer is not None and layer.name() != name:
                layer.setName(name)

            # Reload if the layer doesn't exist yet, or its source (e.g. resolution) changed
            if layer is None or os.path.normpath(layer.source()) != os.path.normpath(source_path):
                if layer is not None:
                    self.qgis_instance.removeMapLayer(layer.id())
                layer = QgsVectorLayer(source_path, name, "ogr")
                if not layer.isValid():
                    layer = QgsVectorLayer(local_data_copy(os.path.join(LOCAL_DATA_DIR, source)), name, "ogr")
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
                self.refresh_legend(layer)

    # Project entries (saved with the project) remembering the flat map, to restore it with "Cancel the globe"
    FLAT_STATE_SCOPE = "Map2Globe"

    def remember_flat_state(self):
        """Remember the flat map (project CRS and view) before it is turned into a globe.

        Nothing is remembered while the project is already in the globe's projection, so that building the
        globe several times doesn't make us "remember" the globe itself.
        """
        crs = self.qgis_instance.crs()
        if Globe.is_globe_crs(crs):
            return
        definition = ("auth:" + crs.authid()) if crs.isValid() and crs.authid() else \
            ("proj:" + crs.toProj() if crs.isValid() else "")
        self.qgis_instance.writeEntry(Globe.FLAT_STATE_SCOPE, "flat_crs", definition)
        extent = self.iface.mapCanvas().extent()
        self.qgis_instance.writeEntry(
            Globe.FLAT_STATE_SCOPE, "flat_extent",
            "" if extent.isNull() or extent.isEmpty() else
            "{},{},{},{}".format(extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()))

    def _remembered_crs(self):
        definition = self.qgis_instance.readEntry(Globe.FLAT_STATE_SCOPE, "flat_crs", "")[0]
        crs = QgsCoordinateReferenceSystem()
        if definition.startswith("auth:"):
            crs = QgsCoordinateReferenceSystem(definition[len("auth:"):])
        elif definition.startswith("proj:"):
            crs.createFromProj(definition[len("proj:"):])
        return crs if crs.isValid() else WGS84

    def _remembered_extent(self):
        text = self.qgis_instance.readEntry(Globe.FLAT_STATE_SCOPE, "flat_extent", "")[0]
        try:
            x_min, y_min, x_max, y_max = (float(v) for v in text.split(","))
        except ValueError:
            return None
        rect = QgsRectangle(x_min, y_min, x_max, y_max)
        return None if rect.isEmpty() else rect

    @staticmethod
    def _is_flat_layer(layer):
        """The flat versions of the Halo and Oceans layers are in WGS84, the globe's ones in the globe's CRS."""
        return layer.crs().authid() == "EPSG:4326"

    def _world_rectangle(self):
        """The whole world as a polygon in WGS84, with a vertex every 2 degrees so that it follows the curves of
        the projection the flat map may use. Mercator-like projections can't show the poles."""
        max_lat = 90 if self.qgis_instance.crs().isGeographic() else 85
        coords = ([(x, -max_lat) for x in range(-180, 181, 2)] + [(180, y) for y in range(-max_lat, max_lat + 1, 2)]
                  + [(x, max_lat) for x in range(180, -181, -2)] + [(-180, y) for y in range(max_lat, -max_lat - 1, -2)])
        return QgsGeometry.fromPolygonXY([[QgsPointXY(x, y) for x, y in coords]])

    def _flat_layer_from(self, disc, file_stem, msgid):
        """A WGS84 layer called `msgid`, holding the whole world, to take the place of the globe's `disc` layer."""
        layer = QgsVectorLayer("Polygon?crs=EPSG:4326", tr(msgid), "memory")
        feature = QgsFeature()
        feature.setGeometry(self._world_rectangle())
        layer.dataProvider().addFeatures([feature])
        layer = persist_layer(layer, file_stem, tr(msgid))
        return layer

    def flatten_globe_layers(self):
        """Replace the Oceans and Halo discs by their flat map version, covering the whole world.

        The discs are only right in the globe's projection; elsewhere they are deformed shapes (a triangle,
        a part of the world, a white veil...). The flat layers keep the colours of the discs: the oceans are
        a filled rectangle drawn under the other layers, the halo is the outline (with its glow) of the map.
        """
        group = Globe.find_group()
        if group is None:
            return
        for msgid, stem in ((u'Oceans', 'oceans_flat'), (u'Halo', 'halo_flat')):
            names = all_names(msgid)
            for node in list(group.findLayers()):
                disc = node.layer()
                if disc is None or disc.name() not in names or Globe._is_flat_layer(disc):
                    continue
                index = group.children().index(node)
                try:
                    symbol = disc.renderer().symbol()
                    color = symbol.color()
                    symbol_layer = symbol.symbolLayer(0)
                    stroke = symbol_layer.strokeColor() if hasattr(symbol_layer, "strokeColor") else color
                    effect = symbol_layer.paintEffect() if hasattr(symbol_layer, "paintEffect") else None
                    use_effects = effect is not None and effect.enabled()
                except Exception:  # unusual renderer: sensible defaults
                    LOGGER.debug("Could not read the style of the %s layer", msgid, exc_info=True)
                    color, stroke, use_effects = DEFAULT_HALO_FILL_COLOR, DEFAULT_HALO_COLOR, False
                layer = self._flat_layer_from(disc, stem, msgid)
                if msgid == u'Oceans':
                    flat_symbol = QgsFillSymbol.createSimple({'color': color.name(), 'outline_style': 'no'})
                    flat_symbol.setColor(color)
                    layer.renderer().setSymbol(flat_symbol)
                    index = len(group.children())  # under everything else
                else:
                    Halo.set_halo_styles(layer, HaloDrawMethod.buffered_point, stroke, use_effects, None)
                self.qgis_instance.removeMapLayer(disc.id())
                self.qgis_instance.addMapLayer(layer, False)
                group.insertLayer(min(index, len(group.children())), layer)

    def adapt_to_flat_map(self):
        """Make the plugin's layers fit a flat map: halo and oceans covering the whole world."""
        self.flatten_globe_layers()

    def show_flat_map(self):
        """Switch from the globe back to the flat map, keeping the plugin's layers.

        The project gets its flat projection and view back. The Halo and Oceans discs are built for the globe's
        projection and look wrong on a flat map, so they are replaced by a halo and oceans covering the whole
        world; the other layers (countries, graticules...) stay as they are. Building the globe again
        rebuilds the halo and the oceans.
        """
        self.qgis_instance.setCrs(self._remembered_crs())
        self.adapt_to_flat_map()
        canvas = self.iface.mapCanvas()
        rect = self._remembered_extent()
        if rect is not None:
            canvas.setExtent(rect)
        else:
            canvas.zoomToFullExtent()
        canvas.refresh()
        for key in ("flat_crs", "flat_extent"):
            self.qgis_instance.removeEntry(Globe.FLAT_STATE_SCOPE, key)

    def retranslate_layers(self):
        """Rename the group and the layers built by the plugin to the current language."""
        group = Globe.find_group()
        if group is None:
            return
        group.setName(Globe.GROUP_NAME)
        for node in group.findLayers():
            layer = node.layer()
            if layer is None:
                continue
            for msgid in Globe.LAYER_MSGIDS:
                if layer.name() in all_names(msgid):
                    if layer.name() != tr(msgid):
                        layer.setName(tr(msgid))
                    break

    def refresh_legend(self, layer):
        """Update the layer's symbol in the Layers panel.

        The panel keeps the symbol QGIS gave the layer when it was added (a random colour); changing the
        renderer's colour afterwards doesn't update it, hence the countries icon not matching the map.
        """
        get_view = getattr(self.iface, "layerTreeView", None)
        view = get_view() if get_view is not None else None
        if view is not None:
            view.refreshLayerSymbology(layer.id())

    def insert_layer_to_group(self, layer, index=0):
        self.qgis_instance.addMapLayer(layer, False)
        self.group.insertLayer(index, layer)

    def change_project_projection(self):
        # Change to wgs84 to activate the changes in origin
        self.qgis_instance.setCrs(WGS84)
        proj_string = self.projection.value.proj_str(self.origin)
        crs = crs_from_proj(proj_string)
        if crs is None:
            LOGGER.warning(tr(u"Could not create the globe's custom projection"), extra=bar_msg())
            return
        self.qgis_instance.setCrs(self.named_crs(crs))

    # Prefix of the name given to the globe's projection (shown by QGIS instead of "unknown CRS")
    GLOBE_CRS_NAME_PREFIX = "Map2Globe - "

    def named_crs(self, crs):
        """Return the globe's projection as a named QGIS user CRS ("Map2Globe - <projection>").

        QGIS shows a custom projection without code as "unknown CRS". One user CRS is kept per projection
        and replaced when the origin changes (no pile-up of entries). If this QGIS can't register
        user CRSs, the unnamed CRS is returned.
        """
        try:
            registry = QgsApplication.coordinateReferenceSystemRegistry()
            name = Globe.GLOBE_CRS_NAME_PREFIX + self.projection.value.name
            # Replace the entry instead of updating it in place: QGIS keeps objects (layers, canvas, caches) that
            # still hold the old definition of an updated entry, which draws the halo and the oceans as a sliver
            # when the centre changes. A new entry has a new identifier, so nothing stale can be reused.
            # (The new entry is added before the old one is removed: QGIS would otherwise hand out the same
            # identifier again.)
            old_ids = [d.id for d in registry.userCrsList() if d.name == name]
            user_id = registry.addUserCrs(crs, name)
            for old_id in old_ids:
                registry.removeUserCrs(old_id)
            if user_id >= 0:
                named = QgsCoordinateReferenceSystem("USER:{}".format(user_id))
                if named.isValid():
                    return named
        except Exception:  # older QGIS versions: keep the unnamed CRS
            LOGGER.debug("Could not register the globe's CRS as a named user CRS", exc_info=True)
        return crs

    @staticmethod
    def is_globe_crs(crs):
        """True for the globe's projection (named, or an unnamed custom CRS created by an older version)."""
        return crs.isValid() and (crs.description().startswith(Globe.GLOBE_CRS_NAME_PREFIX) or crs.authid() == "")

    def zoom_to_globe(self):
        """Fit the canvas to the whole globe.

        Changing the project CRS keeps the canvas extent numerically unchanged, so degree values
        (e.g. -180..180) end up interpreted as metres in the globe CRS: a tiny sliver around the
        projection centre, i.e. an apparently empty map. Refit the view after every (re)build.
        """
        layers = [node.layer() for node in self.group.findLayers() if node.layer() is not None]
        if not layers:
            return
        ms = QgsMapSettings()
        ms.setLayers(layers)
        ms.setDestinationCrs(self.qgis_instance.crs())
        rect = QgsRectangle(ms.fullExtent())
        if rect.isEmpty():
            return
        rect.scale(1.05)
        canvas = self.iface.mapCanvas()
        canvas.setExtent(rect)
        canvas.refresh()

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
    def remove_halo(self):
        for msgid in (u'Halo', u'Oceans'):
            [self.qgis_instance.removeMapLayer(lyr.id()) for lyr in Globe.layers_named(msgid)]

    def add_halo(self, use_effects, stroke_color, fill_color=None, halo_with_fill=False):
        halo = Halo(self.iface, self.origin, self.projection)

        if halo_with_fill:
            self.add_halo(True, stroke_color)
        else:
            self.remove_halo()

        layer, index = halo.create_halo_layer(use_effects, stroke_color, fill_color)
        # The disc must use exactly the project's globe CRS. QGIS can hand back an older definition of the named
        # user CRS (it is updated in place when the centre changes), which draws the disc as a sliver.
        project_crs = self.qgis_instance.crs()
        if Globe.is_globe_crs(project_crs):
            layer.setCrs(project_crs)
        self.insert_layer_to_group(layer, index)
