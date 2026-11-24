# -*- coding: utf-8 -*-
import pytest
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsProject

from ..core.globe import Globe
from ..core.graticules import Graticules
from ..core.halo import Halo
from ..definitions import language
from ..definitions.language import all_names, current_language, default_language, set_language
from ..definitions.projections import Projections
from ..definitions.translations import DictTranslator, FR
from ..qgis_plugin_tools.tools.i18n import tr


@pytest.fixture(autouse=True)
def english_afterwards():
    """The language is global to the QGIS application: always leave the tests in English."""
    yield
    set_language("en", remember=False)


def test_default_language_is_english_whatever_the_qgis_locale():
    for locale in ("fr_FR", "fr", "en_GB", "de_DE", ""):
        assert default_language(locale) == "en"


def test_switching_language_changes_tr():
    set_language("fr", remember=False)
    assert current_language() == "fr"
    assert tr(u"Countries") == "Pays" and tr(u"Oceans") == "Océans"
    set_language("en", remember=False)
    assert current_language() == "en"
    assert tr(u"Countries") == "Countries" and tr(u"Oceans") == "Oceans"


def test_unknown_language_is_refused():
    with pytest.raises(ValueError):
        set_language("xx", remember=False)


def test_the_choice_is_remembered_between_sessions():
    set_language("fr")
    assert language.stored_language("en_GB") == "fr"  # the toggle wins
    set_language("en")
    assert language.stored_language("fr_FR") == "en"
    language.set_setting(language.SETTING_KEY, "")
    assert language.stored_language("fr_FR") == "en"  # nothing chosen yet: English


def test_only_the_plugin_strings_are_translated():
    translator = DictTranslator(FR)
    assert translator.translate("@default", "Layer") == "Couche"
    assert translator.translate("Map2GlobeDockWidgetBase", "Layer") == "Couche"
    # QGIS itself and other plugins keep their own strings
    assert translator.translate("QgisApp", "Layer") is None
    assert translator.translate("SomeOtherPlugin", "Search") is None


def test_layer_and_projection_names_follow_the_language():
    assert Halo.LAYER_NAME == "Halo" and Halo.OCEANS_LAYER_NAME == "Oceans" and Graticules.LAYER_NAME == "Graticules"
    assert Projections.AZIMUTHAL_ORTHOGRAPHIC.value.name == "Azimuthal Orthographic"
    set_language("fr", remember=False)
    assert Halo.OCEANS_LAYER_NAME == "Océans"
    assert Projections.AZIMUTHAL_ORTHOGRAPHIC.value.name == "Azimutale orthographique"
    # the combo box text is turned back into the projection whatever the language
    assert Projections.proj_from_id("Azimutale orthographique") is Projections.AZIMUTHAL_ORTHOGRAPHIC
    set_language("en", remember=False)
    assert Projections.proj_from_id("Azimuthal Orthographic") is Projections.AZIMUTHAL_ORTHOGRAPHIC


def test_all_names_covers_every_language():
    assert all_names(u"Oceans") == {"Oceans", "Océans"}
    assert all_names(u"Countries") == {"Countries", "Pays"}


def test_layers_already_built_are_renamed_when_the_language_changes(globe):
    globe.load_data(False, True, False, QColor("#ffe9a8"), QColor("#ffffff"), "110m", 10)
    globe.add_halo(False, QColor("#ffffff"), QColor("#a6cee3"), halo_with_fill=True)
    names = lambda: sorted(node.layer().name() for node in globe.group.findLayers())
    assert names() == ["Countries", "Halo", "Oceans"]

    set_language("fr", remember=False)
    globe.retranslate_layers()
    assert names() == ["Halo", "Océans", "Pays"]
    assert Globe.find_group() is not None

    set_language("en", remember=False)
    globe.retranslate_layers()
    assert names() == ["Countries", "Halo", "Oceans"]


def test_a_layer_in_another_language_is_reused_not_duplicated(globe):
    set_language("fr", remember=False)
    globe.load_data(False, True, False, QColor("#ffe9a8"), QColor("#ffffff"), "110m", 10)
    assert [l.name() for l in QgsProject.instance().mapLayers().values()] == ["Pays"]
    set_language("en", remember=False)  # no rename on purpose: the project comes from a French session
    globe.load_data(False, True, False, QColor("#ff0000"), QColor("#ffffff"), "110m", 10)
    layers = list(QgsProject.instance().mapLayers().values())
    assert len(layers) == 1 and layers[0].name() == "Countries"  # renamed, not duplicated
    assert layers[0].renderer().symbol().color() == QColor("#ff0000")


def test_removing_the_halo_works_in_any_language(globe):
    globe.add_halo(False, QColor("#ffffff"), QColor("#a6cee3"), halo_with_fill=True)
    set_language("fr", remember=False)  # layers are still named in English
    globe.remove_halo()
    assert not QgsProject.instance().mapLayers()
