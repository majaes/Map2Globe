# -*- coding: utf-8 -*-


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

"""Optional updates through the author's plugin repository (anbmng.com).

Nothing here runs unless the user ticks the box in the Credits panel. Ticking it adds the repository to the QGIS
plugin manager (Plugins > Manage and Install Plugins > Settings): QGIS itself then reports new versions. The plugin
sends no request of its own. A repository the user already had is never overwritten, and unticking only removes
the repository if the plugin was the one that added it.
"""

from qgis.core import QgsSettings

REPOSITORY_NAME = "ANB MNG"
REPOSITORY_URL = "https://anbmng.com/plugins.xml"
# Remembers that the plugin (not the user) added the repository
ADDED_BY_PLUGIN_KEY = "Map2Globe/updateRepositoryAddedByPlugin"


def _group(name):
    return "app/plugin_repositories/{}".format(name)


def is_registered(name=REPOSITORY_NAME):
    return QgsSettings().contains(_group(name) + "/url")


def register_repository(name=REPOSITORY_NAME, url=REPOSITORY_URL):
    """Add the repository to QGIS. Returns True if it was added, False if one with that name already existed."""
    settings = QgsSettings()
    if settings.contains(_group(name) + "/url"):
        return False
    settings.setValue(_group(name) + "/url", url)
    settings.setValue(_group(name) + "/enabled", True)
    settings.setValue(_group(name) + "/authcfg", "")
    settings.setValue(ADDED_BY_PLUGIN_KEY + "/" + name, True)
    return True


def unregister_repository(name=REPOSITORY_NAME):
    """Remove the repository, only if the plugin added it. Returns True if it was removed."""
    settings = QgsSettings()
    if not settings.value(ADDED_BY_PLUGIN_KEY + "/" + name, False, type=bool):
        return False
    settings.remove(_group(name))
    settings.remove(ADDED_BY_PLUGIN_KEY + "/" + name)
    return True
