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
    "Countries 50m": "Pays 50m",
    "Countries 110m": "Pays 110m",
    "Sentinel-2 cloudless": "Sentinel-2 sans nuages",
    # --- UI: centrage ---
    "Coordinates": "Coordonnées",
    "'Longitude, Latitude' in decimal degrees": "« Longitude, Latitude » en degrés décimaux",
    "Center to the current view": "Centrer sur la vue actuelle",
    "Layer": "Couche",
    "Geocoding": "Géocodage",
    "Address for the geolocation of interest:": "Adresse du lieu d'intérêt :",
    "Search": "Rechercher",
    "Maximum number of addresses to list:": "Nombre maximal d'adresses à lister :",
    # --- UI: visualisation ---
    "  Fill": "  Remplissage",
    "  Line": "  Contour",
    "Background": "Arrière-plan",
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
    "Traceback": "Détail de l'erreur",
}

TRANSLATIONS = {"fr": FR}


class DictTranslator(QTranslator):
    """QTranslator backed by a plain dict, ignoring the context."""

    def __init__(self, translations, parent=None):
        super().__init__(parent)
        self._translations = translations

    def translate(self, context, source_text, disambiguation=None, n=-1):
        # None gives Qt a null string = "no translation", so it falls back to the source text.
        # (An empty string would be taken as a valid, empty translation.)
        return self._translations.get(source_text)

    def isEmpty(self):
        return not self._translations
