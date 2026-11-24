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

from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsFillSymbol, QgsProject)
from qgis.gui import QgisInterface

from .halo import Halo
from ..definitions.projections import Projections
from ..definitions.settings import EARTH_RADIUS, DEFAULT_NUMBER_OF_SEGMENTS
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.resources import plugin_name

LOGGER = logging.getLogger(plugin_name())


class Oceans:
    """A filled polygon covering the whole globe, drawn below the other layers.

    It gives the globe its "water" colour without touching the QGIS canvas / project background colour.
    """
    LAYER_NAME = tr('Oceans')

    def __init__(self, iface: QgisInterface, origin, projection) -> None:
        self.iface = iface
        self.origin = origin
        self.projection = projection

    def create_layer(self, color) -> QgsVectorLayer:
        proj_string = self.projection.value.proj_str(self.origin)
        # Block signals required to prevent the pop up asking about the crs change
        self.iface.mainWindow().blockSignals(True)
        layer = QgsVectorLayer("Polygon", self.LAYER_NAME, "memory")
        crs = layer.crs()
        if not crs.createFromProj(proj_string):
            LOGGER.warning(tr(u"Could not create the globe's custom projection"))
        layer.setCrs(crs)
        self.iface.mainWindow().blockSignals(False)

        if self.projection == Projections.AZIMUTHAL_ORTHOGRAPHIC:
            # In the orthographic projection the globe is a disc of the earth's radius around the origin
            # noinspection PyArgumentList
            geom = QgsGeometry.fromPointXY(QgsPointXY(0, 0)).buffer(EARTH_RADIUS, DEFAULT_NUMBER_OF_SEGMENTS)
        else:
            geom = Halo.create_grid_halo(layer.crs())

        feature = QgsFeature()
        feature.setGeometry(geom)
        layer.startEditing()
        layer.dataProvider().addFeatures([feature])
        layer.commitChanges()

        self.set_style(layer, color)
        # noinspection PyArgumentList
        QgsProject.instance().addMapLayer(layer, False)
        return layer

    @staticmethod
    def set_style(layer, color):
        # noinspection PyArgumentList, PyCallByClass
        symbol = QgsFillSymbol.createSimple({'color': 'blue', 'outline_style': 'no'})
        symbol.setColor(color)
        layer.renderer().setSymbol(symbol)
        layer.triggerRepaint()
