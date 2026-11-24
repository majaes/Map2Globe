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

from qgis.PyQt.QtCore import Qt, pyqtSignal, pyqtSlot
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QComboBox, QCompleter
from qgis.core import Qgis, QgsProject

from ..core.globe import Globe
from ..core.utils.geocoder import Geocoder
from ..core.utils.utils import (transform_to_wgs84, get_map_center_coordinates,
                                load_name_centers, local_data_copy)
from ..definitions.projections import Projections
from ..definitions.settings import (LOCAL_DATA_DIR, DEFAULT_MAX_NUMBER_OF_RESULTS, DEFAULT_USE_NE_COUNTRIES,
                                    DEFAULT_USE_NE_GRATICULES, DEFAULT_USE_S2_CLOUDLESS, DEFAULT_ORIGIN,
                                    DEFAULT_BACKGROUND_COLOR, DEFAULT_HALO_COLOR, DEFAULT_HALO_FILL_COLOR,
                                    DEFAULT_COUNTRIES_COLOR,
                                    DEFAULT_GRATICULES_COLOR)
from ..qgis_plugin_tools.tools.custom_logging import bar_msg
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.resources import load_ui, plugin_name
from ..qgis_plugin_tools.tools.settings import get_setting, set_setting
from ..qgis_plugin_tools.tools.version import proj_version

FORM_CLASS = load_ui('globe_builder_dockwidget_base.ui')
LOGGER = logging.getLogger(plugin_name())


class GlobeBuilderDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor."""
        self.is_initializing = True

        super(GlobeBuilderDockWidget, self).__init__(parent)

        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.make_panel_compact()

        self.iface = iface
        # noinspection PyArgumentList
        self.qgis_instance = QgsProject.instance()
        self.globe = Globe(iface)
        self.geocoder = Geocoder(lambda results: self.on_geocoding_finished(results),
                                 lambda message: self.show_warning(message))

        # Set default values
        self.spinBoxMaxResults.setValue(get_setting("maxNumberOfResults", DEFAULT_MAX_NUMBER_OF_RESULTS, int))
        self.checkBoxCountries.setChecked(get_setting("useNE-countries", DEFAULT_USE_NE_COUNTRIES, bool))
        self.checkBoxGraticules.setChecked(get_setting("useNE-graticules", DEFAULT_USE_NE_GRATICULES, bool))
        self.checkBoxS2cloudless.setChecked(get_setting("useS2cloudless", DEFAULT_USE_S2_CLOUDLESS, bool))

        self.lineEditLonLat.setText("{lon}, {lat}".format(**DEFAULT_ORIGIN))
        self.on_radioButtonCoordinates_toggled(self.radioButtonCoordinates.isChecked())
        self.setup_name_search()
        self.on_radioButtonName_toggled(self.radioButtonName.isChecked())
        self.on_radioButtonLayer_toggled(self.radioButtonLayer.isChecked())
        self.on_radioButtonGeocoding_toggled(self.radioButtonGeocoding.isChecked())
        self.on_radioButtonHFill_toggled(self.radioButtonHFill.isChecked())
        self.on_radioButtonHFillWithHalo_toggled(self.radioButtonHFillWithHalo.isChecked())
        self.on_radioButtonHNone_toggled(self.radioButtonHNone.isChecked())

        self.populate_comboBoxProjections()
        self.update_attributions()

        self.mColorButtonHalo.setColor(DEFAULT_HALO_COLOR)
        self.mColorButtonHFill.setColor(DEFAULT_HALO_FILL_COLOR)
        self.mColorButtonCountries.setColor(DEFAULT_COUNTRIES_COLOR)
        self.mColorButtonGraticules.setColor(DEFAULT_GRATICULES_COLOR)

        self.geolocations = {}
        self.old_coordinates = DEFAULT_ORIGIN
        self.old_projection = Projections.proj_from_id(self.comboBoxProjections.currentText())

        # connections
        # keep "Apply changes" in sync with the existence of a globe
        for signal in (self.qgis_instance.layerTreeRoot().addedChildren,
                       self.qgis_instance.layerTreeRoot().removedChildren,
                       self.qgis_instance.layerTreeRoot().visibilityChanged,
                       self.qgis_instance.cleared, self.qgis_instance.readProject):
            signal.connect(self.update_apply_button_state)
        self.comboBoxProjections.currentTextChanged.connect(self.projection_changed)

        self.update_apply_button_state()
        self.is_initializing = False

    def make_panel_compact(self):
        """Let long texts shrink/wrap so the panel needs no horizontal scrollbar."""
        for label in (self.label_2, self.label_3, self.label_4):
            label.setWordWrap(True)
        for combo in (self.comboBoxProjections, self.comboBoxCountries,
                      self.comboBoxGraticules):
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(8)

        # Sentinel-2 goes on its own row instead of widening the Countries/Graticules row.
        self.horizontalLayout_9.removeWidget(self.checkBoxS2cloudless)
        self.verticalLayout_6.addWidget(self.checkBoxS2cloudless)

        self.label_5.setWordWrap(True)
        self.label_5.setOpenExternalLinks(True)
        self.groupBox_6.setCollapsed(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    ATTRIBUTION_OSM = (
        u'This plugin uses the <a href="https://wiki.openstreetmap.org/wiki/Nominatim">OpenStreetMap Nominatim</a> '
        u'geocoding API. Please <b>use a maximum of 1 geocoding request per second</b>. '
        u'OpenStreetMap data &copy; OpenStreetMap contributors, licensed under the '
        u'<a href="https://opendatacommons.org/licenses/odbl/">ODbL</a>.')
    ATTRIBUTION_NE = (
        u'Made with Natural Earth. Free vector and raster map data from '
        u'<a href="https://www.naturalearthdata.com">naturalearthdata.com</a>.')
    ATTRIBUTION_S2 = (
        u'Sentinel-2 cloudless data from <a href="https://s2maps.eu/">s2maps.eu</a> by EOX IT Services GmbH '
        u'(contains modified Copernicus Sentinel data 2017 &amp; 2018), licensed under '
        u'<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>. '
        u'<b>Non-commercial use only</b>; for commercial use see '
        u'<a href="https://cloudless.eox.at">cloudless.eox.at</a>.')

    def update_attributions(self):
        """Show only the attributions that apply: Sentinel-2's only when that layer is enabled."""
        parts = [tr(self.ATTRIBUTION_OSM), tr(self.ATTRIBUTION_NE)]
        if self.checkBoxS2cloudless.isChecked():
            parts.append(tr(self.ATTRIBUTION_S2))
        self.label_5.setText("<p>" + "</p><p>".join(parts) + "</p>")

    def setup_name_search(self):
        """Searchable list of the NAME values of the bundled Natural Earth countries."""
        path = local_data_copy(os.path.join(LOCAL_DATA_DIR, 'ne_50m_admin_0_countries.geojson'))
        self.name_centers = load_name_centers(path, 'NAME')
        self.name_centers_lower = {name.lower(): center for name, center in self.name_centers.items()}
        names = sorted(self.name_centers)
        self.comboBoxNames.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.comboBoxNames.addItems(names)
        self.comboBoxNames.setCurrentIndex(-1)
        self.comboBoxNames.lineEdit().setPlaceholderText(tr(u"Type to search a country name"))
        completer = QCompleter(names, self.comboBoxNames)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.comboBoxNames.setCompleter(completer)

    @pyqtSlot(bool)
    def on_radioButtonName_toggled(self, is_checked):
        self.comboBoxNames.setEnabled(is_checked)

    def closeEvent(self, event):
        # noinspection PyUnresolvedReferences
        self.closingPlugin.emit()
        event.accept()

    # Without this annotation the signal is handled twice,
    # see https://stackoverflow.com/questions/14311578/event-signal-is-emmitted-twice-every-time
    @pyqtSlot(bool)
    def on_radioButtonCoordinates_toggled(self, is_checked):
        self.lineEditLonLat.setEnabled(is_checked)

    @pyqtSlot(bool)
    def on_radioButtonLayer_toggled(self, is_checked):
        self.mMapLayerComboBox.setEnabled(is_checked)

    @pyqtSlot(bool)
    def on_radioButtonGeocoding_toggled(self, is_checked):
        self.lineEditGeocoding.setEnabled(is_checked)
        self.pushButtonSearch.setEnabled(is_checked)
        self.listWidgetGeocodingResults.setEnabled(is_checked)
        self.spinBoxMaxResults.setEnabled(is_checked)


    @pyqtSlot(bool)
    def on_radioButtonHFillWithHalo_toggled(self, is_checked):
        self.mColorButtonHFill.setEnabled(is_checked or self.radioButtonHFill.isChecked())

    @pyqtSlot(bool)
    def on_radioButtonHFill_toggled(self, is_checked):
        self.mColorButtonHFill.setEnabled(is_checked or self.radioButtonHFillWithHalo.isChecked())

    @pyqtSlot(bool)
    def on_radioButtonHNone_toggled(self, is_checked):
        self.mColorButtonHalo.setEnabled(not is_checked)
        self.mColorButtonHFill.setEnabled(not is_checked and (
            self.radioButtonHFill.isChecked() or self.radioButtonHFillWithHalo.isChecked()))

    @pyqtSlot(int)
    def on_spinBoxMaxResults_valueChanged(self, value):
        set_setting("maxNumberOfResults", value)

    def on_checkBoxCountries_stateChanged(self):
        set_setting("useNE-countries", self.checkBoxCountries.isChecked())

    def on_checkBoxGraticules_stateChanged(self):
        set_setting("useNE-graticules", self.checkBoxGraticules.isChecked())

    def on_checkBoxS2cloudless_stateChanged(self):
        set_setting("useS2cloudless", self.checkBoxS2cloudless.isChecked())
        self.update_attributions()

    @pyqtSlot()
    def on_pushButtonSearch_clicked(self):
        text = self.lineEditGeocoding.text()
        if len(text.strip()):
            self.listWidgetGeocodingResults.clear()
            self.geolocations.clear()
            self.geocoder.geocode(text, self.spinBoxMaxResults.value())

    @pyqtSlot()
    def on_pushButtonApplyVisualizations_clicked(self):
        """Update the globe that already exists in the map. Never builds anything in a workspace without one."""
        if self.is_initializing:
            return
        if not Globe.exists_in_map():
            self.show_warning(tr(u"There is no globe to update yet: add the globe to the map first"))
            self.update_apply_button_state()
            return
        self.update_map_globe()
        self.update_apply_button_state()

    def update_map_globe(self):
        self.globe.suspend_auto_crs_setup()
        coordinates = self.calculate_origin_coordinates()
        if coordinates is not None and coordinates != self.old_coordinates:
            self.old_coordinates = coordinates
            self.globe.set_origin(coordinates)
        projection = Projections.proj_from_id(self.comboBoxProjections.currentText())
        self.old_projection = projection
        self.globe.set_projection(projection)
        # Load the data first and set the globe projection afterwards: QGIS resets the project CRS to the
        # one of the first layer added, which would otherwise undo the projection (flat world map).
        self.load_data_to_globe()
        self.globe.change_project_projection()
        self.globe.set_group_visibility(True)
        self.add_halo_to_globe()
        self.globe.zoom_to_globe()

    @pyqtSlot()
    def on_pushButtonRun_clicked(self):
        self.globe.suspend_auto_crs_setup()
        self.load_data_to_globe()
        self.old_coordinates = self.calculate_origin_coordinates()
        self.globe.set_origin(self.old_coordinates)
        self.old_projection = Projections.proj_from_id(self.comboBoxProjections.currentText())
        self.globe.set_projection(self.old_projection)
        self.globe.change_project_projection()
        self.globe.set_group_visibility(True)
        self.add_halo_to_globe()
        self.globe.zoom_to_globe()
        self.update_apply_button_state()

    def update_apply_button_state(self, *args):
        """"Apply changes" only makes sense when a globe already exists in the map."""
        has_globe = Globe.exists_in_map()
        self.pushButtonApplyVisualizations.setEnabled(has_globe)
        self.pushButtonApplyVisualizations.setToolTip(
            "" if has_globe else tr(u"Add the globe to the map first: there is nothing to update yet"))

    def populate_comboBoxProjections(self, *args):
        try:
            proj_v = proj_version()
        except AttributeError:
            proj_v = (0, 0)
        self.comboBoxProjections.clear()
        for projection in Projections:
            if proj_v >= projection.value.min_proj:
                self.comboBoxProjections.addItem(projection.value.name)

    def add_halo_to_globe(self):
        if self.radioButtonHNone.isChecked():
            self.globe.remove_halo()
        else:
            self.globe.add_halo(self.radioButtonHHalo.isChecked(), self.mColorButtonHalo.color(),
                                self.get_halo_fill_color(), self.radioButtonHFillWithHalo.isChecked())

    def get_halo_fill_color(self):
        return self.mColorButtonHFill.color() if (
            self.radioButtonHFill.isChecked() or self.radioButtonHFillWithHalo.isChecked()) else None

    def show_warning(self, message):
        self.iface.messageBar().pushMessage(plugin_name(), message, level=Qgis.Warning, duration=8)

    def on_geocoding_finished(self, geolocations):
        self.geolocations = geolocations.copy()
        if not self.geolocations:
            self.show_warning(tr(u"No place found for this address"))
        self.listWidgetGeocodingResults.clear()
        [self.listWidgetGeocodingResults.addItem(name) for name in self.geolocations.keys()]
        if self.listWidgetGeocodingResults.count() > 0:
            # Preselect the best match so "Apply changes" works right away
            self.listWidgetGeocodingResults.setCurrentRow(0)

    def load_data_to_globe(self):
        self.globe.load_data(self.checkBoxS2cloudless.isChecked(), self.checkBoxCountries.isChecked(),
                             self.checkBoxGraticules.isChecked(), self.mColorButtonCountries.color(),
                             self.mColorButtonGraticules.color(),
                             self.comboBoxCountries.currentText().strip(),
                             self.comboBoxGraticules.currentText().rstrip("°").strip())

    def get_geocoded_coordinates(self):
        coordinates = None
        if (len(self.geolocations) and
            self.listWidgetGeocodingResults.count() > 0 and
            self.listWidgetGeocodingResults.currentItem() is not None):
            geolocation = self.listWidgetGeocodingResults.currentItem().text()
            coordinates = self.geolocations.get(geolocation, None)
            coordinates = {'lon': coordinates[0], 'lat': coordinates[1]}

        return coordinates

    def calculate_origin_coordinates(self):
        coordinates = None
        try:
            if self.radioButtonCoordinates.isChecked():
                coordinates = tuple(map(lambda c: float(c.strip()), self.lineEditLonLat.text().split(',')))
                coordinates = {'lon': coordinates[0], 'lat': coordinates[1]}

            elif self.radioButtonGeocoding.isChecked():
                coordinates = self.get_geocoded_coordinates()
                if not coordinates:
                    raise ValueError(tr(u"Make sure to select an item from the Geolocation list"))

            elif self.radioButtonLayer.isChecked():
                layer = self.mMapLayerComboBox.currentLayer()
                if layer is None:
                    raise ValueError(tr(u"Make sure to have at least one layer in the project"))
                center_point = layer.extent().center()

                center_point = transform_to_wgs84(center_point, layer.crs(), self.qgis_instance)
                coordinates = {'lon': center_point.x(), 'lat': center_point.y()}

            elif self.radioButtonCenter.isChecked():
                coordinates = get_map_center_coordinates(self.iface, self.qgis_instance)

            elif self.radioButtonName.isChecked():
                name = self.comboBoxNames.currentText().strip().lower()
                coordinates = self.name_centers_lower.get(name)
                if coordinates is None:
                    raise ValueError(tr(u"Choose a name from the list"))

        except ValueError as e:
            LOGGER.warning(tr(u"Error occurred while parsing center of the globe"),
                           bar_msg(f"{tr(u'Traceback')}: {e}", duration=6))
        return coordinates

    def projection_changed(self, projection_id: str):
        # TODO: check if this causes problems in newer QGIS versions
        projection = Projections.proj_from_id(projection_id)
        # Centering is disabled due to rendering artifacts
        self.centeringGroupBox.setEnabled(projection == Projections.AZIMUTHAL_ORTHOGRAPHIC)
