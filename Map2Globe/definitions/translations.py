# -*- coding: utf-8 -*-
"""Built-in translations.

Qt's ``lrelease`` is not always available to contributors, so translations are provided as plain
Python dictionaries served through a ``QTranslator`` subclass. This works for strings coming from the
``.ui`` file as well as for ``tr()`` calls, and needs no compilation step.

The names of the layers and of the group built by the plugin are translated too (and renamed when the
language is switched, see ``definitions/language.py``).
"""

from qgis.PyQt.QtCore import QTranslator

FR = {
    # --- UI: titres et sections ---
    "Data sources (optional)": "Sources de données (facultatif)",
    "Center the Globe based on:": "Centrer le globe sur :",
    "Visualization": "Visualisation",
    "Credits": "Crédits",
    # --- UI: sources de données ---
    "Countries": "Pays",
    "Oceans": "Océans",
    "S2 Cloudless 2018": "S2 sans nuages 2018",
    "Graticules": "Graticules",
    "Sentinel-2 cloudless": "Sentinel-2 sans nuages",
    # --- UI: centrage ---
    "Coordinates": "Coordonnées",
    "'Longitude, Latitude' in decimal degrees": "« Longitude, Latitude » en degrés décimaux",
    "Current view": "Vue actuelle",
    "Country": "Pays",
    "Type to search a country name": "Tapez pour rechercher un nom de pays",
    "Choose a name from the list": "Choisissez un nom dans la liste",
    "Layer": "Couche",
    "Geocoding": "Géocodage",
    "Address for the geolocation of interest:": "Adresse du lieu d'intérêt :",
    "Search": "Rechercher",
    "Maximum number of addresses to list:": "Nombre maximal d'adresses à lister :",
    # --- UI: visualisation ---
    "Halo / outline": "Halo / contour",
    "Colors": "Couleurs",
    "Address or place name": "Adresse ou nom de lieu",
    "The map already shows a globe: use \"Apply changes\" to update it":
        "La carte montre déjà un globe : utilisez « Appliquer les modifications » pour le mettre à jour",
    "Build the globe from the settings above": "Construire le globe avec les réglages ci-dessus",
    "Natural Earth countries, bundled with the plugin (works offline)":
        "Pays Natural Earth, fournis avec le plugin (fonctionne hors ligne)",
    "Needs an Internet connection. Non-commercial use only (CC BY-NC-SA 4.0)":
        "Nécessite une connexion Internet. Usage non commercial uniquement (CC BY-NC-SA 4.0)",
    "Optional visualizations": "Visualisations facultatives",
    "Halo type": "Type de halo",
    "Halo, no oceans": "Halo, sans océans",
    "Halo, with oceans": "Halo, avec océans",
    "Outline, no oceans": "Contour, sans océans",
    "Outline, with oceans": "Contour, avec océans",
    "None": "Aucun",
    # --- UI: mise en page ---
    "Apply changes": "Appliquer les modifications",
    "Switch the map to a globe": "Passer la carte en globe",
    "Switch the map to flat": "Passer la carte à plat",
    # --- Attributions ---
    'The free vector and raster map data used come from the '
    '<a href="https://wiki.openstreetmap.org/wiki/Nominatim">OpenStreetMap Nominatim</a> geocoding API '
    'and from <a href="https://www.naturalearthdata.com">naturalearthdata.com</a>.':
        'Les données cartographiques vectorielles et raster libres utilisées sont issues de l\'API de géocodage '
        '<a href="https://wiki.openstreetmap.org/wiki/Nominatim">OpenStreetMap Nominatim</a> '
        'et de <a href="https://www.naturalearthdata.com">naturalearthdata.com</a>.',
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
    "There is no globe to update yet: switch the map to a globe first":
        "Il n’y a pas encore de globe à mettre à jour : passez d’abord la carte en globe",
    "Switch the map to a globe first: there is nothing to update yet":
        "Passez d’abord la carte en globe : il n’y a encore rien à mettre à jour",
    "Switch back to the flat map and keep the plugin's layers (the halo and the oceans are adapted to the flat map)":
        "Revenir à la carte à plat en gardant les couches du plugin (le halo et les océans sont adaptés à la carte plate)",
    "There is no globe in the map": "Il n’y a pas de globe dans la carte",
    "Traceback": "Détail de l'erreur",
}

TRANSLATIONS = {"fr": FR}

# Identifiers that go through tr() with the default context (layer names) must stay as is,
# even though the same words are translated when they come from the .ui file.
# Only the plugin's own strings are translated: those of ``tr()`` ("@default") and of the panel's .ui file.
# Other contexts (QGIS itself, other plugins) must be left alone, as a translator is application wide.
CONTEXTS = ("@default", "Map2GlobeDockWidgetBase")


class DictTranslator(QTranslator):
    """QTranslator backed by a plain dict, for the plugin's contexts only."""

    def __init__(self, translations, parent=None):
        super().__init__(parent)
        self._translations = translations

    def translate(self, context, source_text, disambiguation=None, n=-1):
        # None gives Qt a null string = "no translation", so it falls back to the source text.
        # (An empty string would be taken as a valid, empty translation.)
        if context not in CONTEXTS:
            return None
        return self._translations.get(source_text)

    def isEmpty(self):
        return not self._translations
