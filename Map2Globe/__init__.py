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

import os

from .qgis_plugin_tools.infrastructure.debugging import setup_pydevd

if os.environ.get('QGIS_PLUGIN_USE_DEBUGGER') == 'pydevd':
    if os.environ.get('IN_TESTS', "0") != "1" and os.environ.get('QGIS_PLUGIN_IN_CI', "0") != "1":
        setup_pydevd()


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load Map2Globe class from file Map2Globe.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .plugin import Map2Globe
    return Map2Globe(iface)
