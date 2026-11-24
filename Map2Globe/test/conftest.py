"""
This class contains fixtures and common helper function to keep the test files shorter

pytest-qgis (https://pypi.org/project/pytest-qgis) contains the following helpful fixtures:

* qgis_app initializes and returns fully configured QgsApplication.
  This fixture is called automatically on the start of pytest session.
* qgis_canvas initializes and returns QgsMapCanvas
* qgis_iface returns mocked QgsInterface
* new_project makes sure that all the map layers and configurations are removed.
  This should be used with tests that add stuff to QgsProject.

"""

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
import shutil

import pytest
from qgis.core import QgsApplication

from ..core.globe import Globe
from ..definitions.projections import Projections


def ensure_user_crs_database():
    """The test profile has an empty (0 byte) user database, in which no user CRS can be registered: give it the
    schema a real QGIS profile has, by copying the template shipped with QGIS."""
    path = QgsApplication.qgisUserDatabaseFilePath()
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        template = os.path.join(QgsApplication.pkgDataPath(), "resources", "qgis.db")
        if os.path.exists(template):
            shutil.copyfile(template, path)


@pytest.fixture(scope='function')
def globe(qgis_new_project, qgis_iface) -> Globe:
    ensure_user_crs_database()
    globe = Globe(qgis_iface)
    globe.set_projection(Projections.AZIMUTHAL_ORTHOGRAPHIC)
    return globe
