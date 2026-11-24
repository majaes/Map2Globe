# -*- coding: utf-8 -*-
"""Built-in translations.

Qt's ``lrelease`` is not always available to contributors, so translations are provided as plain
Python dictionaries served through a ``QTranslator`` subclass. This works for strings coming from the
``.ui`` file as well as for ``tr()`` calls, and needs no compilation step.

Strings used as layer/group names (``Globe``, ``Countries``, ``Halo``, ``Graticules``,
``S2 Cloudless 2018``) are intentionally *not* translated: they are used as identifiers to find the
plugin's own layers in the project.
"""

from qgis.PyQt.QtCore import QTranslator

FR = {
    # --- UI: titres et sections ---
    "Data sources (optional)": "Sources de données (facultatif)",
    "Center the Globe based on:": "Centrer le globe sur :",
    "Visualization": "Visualisation",
    "Layout": "Mise en page",
    # --- UI: sources de données ---
    "Countries": "Pays",
    "Graticules": "Graticules",
    "Sentinel-2 cloudless": "Sentinel-2 sans nuages",
    # --- UI: centrage ---
    "Coordinates": "Coordonnées",
    "'Longitude, Latitude' in decimal degrees": "« Longitude, Latitude » en degrés décimaux",
    "Center to the current view": "Centrer sur la vue actuelle",
    "Country (NAME field)": "Pays (champ NAME)",
    "Type to search a country name": "Tapez pour rechercher un nom de pays",
    "Choose a name from the list": "Choisissez un nom dans la liste",
    "Layer": "Couche",
    "Geocoding": "Géocodage",
    "Address for the geolocation of interest:": "Adresse du lieu d'intérêt :",
    "Search": "Rechercher",
    "Maximum number of addresses to list:": "Nombre maximal d'adresses à lister :",
    # --- UI: visualisation ---
    "  Line": "  Contour",
    "  Oceans": "  Océans",
    "  Countries": "  Pays",
    "Optional visualizations": "Visualisations facultatives",
    "Halo type": "Type de halo",
    "Halo, no fill": "Halo, sans remplissage",
    "Halo, fill": "Halo, avec remplissage",
    "Outline, no fill": "Contour, sans remplissage",
    "Outline, fill": "Contour, avec remplissage",
    "None": "Aucun",
    # --- UI: mise en page ---
    "Map composer:": "Composeur de cartes :",
    "Color for Countries intersecting the current view": "Couleur des pays croisant la vue actuelle",
    "Globe size in mm": "Taille du globe en mm",
    "Apply changes": "Appliquer les modifications",
    "Add the Globe to a Map": "Ajouter le globe à la carte",
    "Add the Globe to a Layout": "Ajouter le globe à une mise en page",
    # --- Attributions ---
    'This plugin uses the <a href="https://wiki.openstreetmap.org/wiki/Nominatim">OpenStreetMap Nominatim</a> '
    'geocoding API. Please <b>use a maximum of 1 geocoding request per second</b>. '
    'OpenStreetMap data &copy; OpenStreetMap contributors, licensed under the '
    '<a href="https://opendatacommons.org/licenses/odbl/">ODbL</a>.':
        'Ce plugin utilise l’API de géocodage <a href="https://wiki.openstreetmap.org/wiki/Nominatim">'
        'OpenStreetMap Nominatim</a>. Merci de <b>ne pas dépasser 1 requête de géocodage par seconde</b>. '
        'Données OpenStreetMap &copy; les contributeurs d’OpenStreetMap, sous licence '
        '<a href="https://opendatacommons.org/licenses/odbl/">ODbL</a>.',
    'Made with Natural Earth. Free vector and raster map data from '
    '<a href="https://www.naturalearthdata.com">naturalearthdata.com</a>.':
        'Réalisé avec Natural Earth. Données cartographiques vectorielles et raster libres de '
        '<a href="https://www.naturalearthdata.com">naturalearthdata.com</a>.',
    'Sentinel-2 cloudless data from <a href="https://s2maps.eu/">s2maps.eu</a> by EOX IT Services GmbH '
    '(contains modified Copernicus Sentinel data 2017 &amp; 2018), licensed under '
    '<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>. '
    '<b>Non-commercial use only</b>; for commercial use see '
    '<a href="https://cloudless.eox.at">cloudless.eox.at</a>.':
        'Données Sentinel-2 cloudless de <a href="https://s2maps.eu/">s2maps.eu</a>, par EOX IT Services GmbH '
        '(contient des données Copernicus Sentinel modifiées 2017 et 2018), sous licence '
        '<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>. '
        '<b>Usage non commercial uniquement</b> ; pour un usage commercial, voir '
        '<a href="https://cloudless.eox.at">cloudless.eox.at</a>.',
    # --- Projections ---
    "Azimuthal Orthographic": "Azimutale orthographique",
    "Hammer & Eckert-Greifendorff": "Hammer et Eckert-Greifendorff",
    # --- Menus et messages ---
    "Build Globe view": "Construire la vue globe",
    "Create new layout (LayoutGlobe)": "Créer une nouvelle mise en page (LayoutGlobe)",
    "Selected": "Sélectionné",
    "Not Selected": "Non sélectionné",
    "Could not add Sentinel 2 Cloudless layer": "Impossible d'ajouter la couche Sentinel-2 sans nuages",
    "Could not add graticules": "Impossible d'ajouter les graticules",
    "Could not load Natural Earth layer '{}'": "Impossible de charger la couche Natural Earth « {} »",
    "Could not create the globe's custom projection": "Impossible de créer la projection personnalisée du globe",
    "Could not create the globe's custom projection for the halo":
        "Impossible de créer la projection personnalisée du globe pour le halo",
    "Make sure to select an item from the Geolocation list":
        "Veuillez sélectionner un élément dans la liste de géolocalisation",
    "Make sure to have at least one layer in the project": "Le projet doit contenir au moins une couche",
    "Error occurred while parsing center of the globe": "Erreur lors de la lecture du centre du globe",
    "Geocoding failed: {}": "Échec du géocodage : {}",
    "Geocoding failed: unexpected answer from the server": "Échec du géocodage : réponse inattendue du serveur",
    "No place found for this address": "Aucun lieu trouvé pour cette adresse",
    "There is no globe to update yet: add the globe to a map or to a layout first":
        "Il n’y a pas encore de globe à mettre à jour : ajoutez d’abord le globe à la carte ou à une mise en page",
    "Add the globe to a map or to a layout first: there is nothing to update yet":
        "Ajoutez d’abord le globe à la carte ou à une mise en page : il n’y a encore rien à mettre à jour",
    "Traceback": "Détail de l'erreur",
}

TRANSLATIONS = {"fr": FR}

# Identifiers that go through tr() with the default context (layer names) must stay as is,
# even though the same words are translated when they come from the .ui file.
IDENTIFIER_CONTEXT = "@default"
IDENTIFIERS = {"Countries", "Graticules", "Halo", "Oceans", "Globe", "S2 Cloudless 2018"}


class DictTranslator(QTranslator):
    """QTranslator backed by a plain dict, ignoring the context."""

    def __init__(self, translations, parent=None):
        super().__init__(parent)
        self._translations = translations

    def translate(self, context, source_text, disambiguation=None, n=-1):
        # None gives Qt a null string = "no translation", so it falls back to the source text.
        # (An empty string would be taken as a valid, empty translation.)
        if context == IDENTIFIER_CONTEXT and source_text in IDENTIFIERS:
            return None
        return self._translations.get(source_text)

    def isEmpty(self):
        return not self._translations
