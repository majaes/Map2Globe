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

import json
import logging

from qgis.PyQt.QtCore import QUrl, QUrlQuery
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager
from qgis.core import Qgis, QgsMessageLog

from ...definitions.settings import NOMINATIM_URL, MAX_NAME_PARTS
from ...qgis_plugin_tools.tools.i18n import tr
from ...qgis_plugin_tools.tools.resources import plugin_name

LOGGER = logging.getLogger(plugin_name())

# Qt6 only exposes the scoped form, Qt5 only the flat one.
try:
    NO_ERROR = QNetworkReply.NetworkError.NoError
except AttributeError:  # pragma: no cover
    NO_ERROR = QNetworkReply.NoError

# Nominatim's usage policy requires an identifying User-Agent (a generic browser one can be blocked).
USER_AGENT = "GlobeBuilder-QGIS-plugin (+https://github.com/GispoCoding/GlobeBuilder)"


class Geocoder:
    """Nominatim geocoder.

    :param callback: called with a {name: [lon, lat]} dict (possibly empty) when a search succeeds
    :param error_callback: optional, called with a user readable message when a search fails
    """

    # noinspection PyUnresolvedReferences
    def __init__(self, callback, error_callback=None):
        self.network_access_manager = QNetworkAccessManager()
        self.network_access_manager.finished.connect(self.on_search_response)
        self.callback = callback
        self.error_callback = error_callback

    @staticmethod
    def build_url(query, max_results):
        # QUrlQuery takes care of encoding spaces, accents, '&' ... in the user's text
        url_query = QUrlQuery()
        url_query.addQueryItem('q', query)
        url_query.addQueryItem('limit', str(max_results))
        url_query.addQueryItem('format', 'geojson')
        url = QUrl(NOMINATIM_URL)
        url.setQuery(url_query)
        return url

    def geocode(self, query, max_results):
        url = self.build_url(query.strip(), max_results)
        QgsMessageLog.logMessage(url.toString(), "GlobeBuilder", Qgis.Info)
        geocoding_request = QNetworkRequest(url)
        # https://www.riverbankcomputing.com/pipermail/pyqt/2016-May/037514.html
        geocoding_request.setRawHeader(b"User-Agent", USER_AGENT.encode("utf-8"))
        self.network_access_manager.get(geocoding_request)

    def _fail(self, message):
        LOGGER.warning(message)
        if self.error_callback is not None:
            self.error_callback(message)

    def on_search_response(self, search_result):
        try:
            if search_result.error() != NO_ERROR:
                self._fail(tr(u"Geocoding failed: {}", search_result.errorString()))
                return

            data_string = bytes(search_result.readAll()).decode('utf-8')
            try:
                features = json.loads(data_string)['features']
            except (ValueError, KeyError):
                self._fail(tr(u"Geocoding failed: unexpected answer from the server"))
                return

            self.callback(self.parse_features(features))
        finally:
            search_result.deleteLater()

    @staticmethod
    def parse_features(features):
        result_dict = {}
        for f in features:
            name_parts = f['properties']['display_name'].split(",")
            name = "{} ({})".format(",".join(
                name_parts[0:min(MAX_NAME_PARTS, len(name_parts) - 1)]),
                name_parts[-1].strip()) if len(name_parts) > 1 else name_parts[0]
            result_dict[name] = f['geometry']['coordinates']
        return result_dict
