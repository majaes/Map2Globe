# -*- coding: utf-8 -*-


#  Copyright (C) 2020-2021 GlobeBuilder contributors.
#  Copyright (C) 2026 ANABA MANGA.
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

import os
import shutil
import tempfile
import uuid

from qgis.core import (QgsApplication, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsGeometry, QgsProject, QgsRectangle,
                       QgsVectorFileWriter, QgsVectorLayer, QgsWkbTypes)

from ...definitions.settings import WGS84


def crs_from_proj(proj_string):
    """CRS for a PROJ string, or None if it is invalid.

    Depending on the QGIS/PROJ setup `createFromProj()` can wrongly identify a custom projection as a standard
    CRS (e.g. an object with authid EPSG:4326 but the orthographic definition, which then behaves as WGS 84
    once assigned to a layer). In that case the CRS is rebuilt from its WKT, which keeps the real definition.
    """
    crs = QgsCoordinateReferenceSystem()
    if not crs.createFromProj(proj_string):
        return None
    if crs.authid():
        clean = QgsCoordinateReferenceSystem()
        if clean.createFromWkt(crs.toWkt()) and clean.isValid() and not clean.authid():
            return clean
    return crs


def data_dir():
    """Folder (in the QGIS profile, outside the plugin folder) where the plugin keeps the data files of its layers."""
    try:
        root = os.path.join(QgsApplication.qgisSettingsDirPath(), "Map2Globe_data")
    except Exception:
        root = os.path.join(tempfile.gettempdir(), "Map2Globe_data")
    os.makedirs(root, exist_ok=True)
    return root


def _no_error(error):
    try:
        return error == QgsVectorFileWriter.NoError
    except AttributeError:  # Qt6 / QGIS 4 scoped enum
        return error == QgsVectorFileWriter.WriterError.NoError


def persist_layer(layer, file_stem, name=None):
    """Save a temporary (memory) vector layer as a GeoPackage in the plugin data folder, like the countries.

    Returns the layer loaded back from that file, so it is no longer a "temporary scratch layer" and survives
    saving/reopening the QGIS project. If anything goes wrong the original layer is returned unchanged.
    The file is replaced by the next build; if it is still locked (Windows) a new file name is used.
    """
    name = name or layer.name()
    try:
        path = os.path.join(data_dir(), file_stem + ".gpkg")
        try:
            for suffix in ("", "-wal", "-shm"):
                if os.path.exists(path + suffix):
                    os.remove(path + suffix)
        except OSError:
            path = os.path.join(data_dir(), "{}_{}.gpkg".format(file_stem, uuid.uuid4().hex[:8]))

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = file_stem
        options.fileEncoding = "UTF-8"
        result = QgsVectorFileWriter.writeAsVectorFormatV3(layer, path, QgsProject.instance().transformContext(),
                                                           options)
        if not _no_error(result[0]):
            return layer
        saved = QgsVectorLayer("{}|layername={}".format(path, file_stem), name, "ogr")
        if not saved.isValid():
            return layer
        # The CRS read back from the file can differ from the one that was written (e.g. matched to another
        # registered user CRS): the geometries were written in the original one, so enforce it.
        if saved.crs() != layer.crs():
            saved.setCrs(layer.crs())
        return saved
    except Exception:  # never let a saving problem prevent the globe from being built
        return layer


def local_data_copy(source_path):
    """Return a copy of a bundled data file stored *outside* the plugin folder.

    Layers read their file for as long as they are in the project. If they read it straight from the
    plugin folder, Windows locks it and QGIS can no longer uninstall/upgrade the plugin ("Failed to
    remove directory"). The copy is refreshed whenever the bundled file changes. If the copy can't be
    made, the original path is returned so the plugin keeps working.
    """
    try:
        root = data_dir()
        target = os.path.join(root, os.path.basename(source_path))
        src_stat = os.stat(source_path)
        if (not os.path.exists(target) or os.path.getsize(target) != src_stat.st_size
                or os.path.getmtime(target) < src_stat.st_mtime):
            shutil.copy2(source_path, target)
        return target
    except OSError:
        return source_path


def transform_to_wgs84(geom, crs, qgis_instance):
    transformer = QgsCoordinateTransform(crs, WGS84, qgis_instance)
    return transformer.transform(geom)


def get_map_center_coordinates(iface, qgis_instance, frmt="{:.0f}"):
    center_point = iface.mapCanvas().extent().center()
    center_point = transform_to_wgs84(center_point, qgis_instance.crs(),
                                      qgis_instance)
    center = {'lon': float(frmt.format(center_point.x())), 'lat': float(frmt.format(center_point.y()))}
    return center


def get_geometries_center(geometries, crs, project, decimals=4):
    """Longitude/latitude (WGS84) of the centre of some geometries given in `crs`, or None.

    The centre of the bounding box is used. Geometries that wrap around the antimeridian
    (e.g. USA, Russia, Fiji: bounding box wider than 180 degrees) would otherwise get a centre
    on the wrong side of the world, so the largest part is used instead.
    """
    geometries = [g for g in geometries if g is not None and not g.isEmpty()]
    if not geometries:
        return None

    transform = QgsCoordinateTransform(crs, WGS84, project) if crs != WGS84 else None
    rect = QgsRectangle()
    rect.setNull()
    parts = []
    for geom in geometries:
        geom = QgsGeometry(geom)  # copy: never alter the layer's own geometry
        if transform is not None:
            geom.transform(transform)
        rect.combineExtentWith(geom.boundingBox())
        parts.extend(geom.asGeometryCollection())

    if rect.width() > 180 and parts:
        polygons = [p for p in parts if QgsWkbTypes.geometryType(p.wkbType()) == QgsWkbTypes.PolygonGeometry]
        biggest = max(polygons, key=lambda p: p.area()) if polygons else max(parts, key=lambda p: p.length())
        rect = biggest.boundingBox()

    center = rect.center()
    return {'lon': round(center.x(), decimals), 'lat': round(max(-90.0, min(90.0, center.y())), decimals)}


def load_name_centers(path, field='NAME'):
    """{name: {'lon':.., 'lat':..}} for every feature of the vector file `path`, from its `field` column.

    The layer is only used temporarily (never added to the project) and released at once, so the
    file isn't kept open.
    """
    layer = QgsVectorLayer(path, "names", "ogr")
    if not layer.isValid() or layer.fields().indexFromName(field) < 0:
        return {}
    centers = {}
    for feature in layer.getFeatures():
        name = feature[field]
        center = get_geometries_center([feature.geometry()], layer.crs(), QgsProject.instance())
        if name and center is not None:
            centers[str(name)] = center
    del layer
    return centers
