# -*- coding: utf-8 -*-
import pytest
from qgis.core import QgsSettings

from ..core.utils import updates

NAME = "ANB MNG TEST"
URL = "https://example.invalid/plugins.xml"


@pytest.fixture(autouse=True)
def clean_settings():
    def clean():
        settings = QgsSettings()
        settings.remove("app/plugin_repositories/" + NAME)
        settings.remove(updates.ADDED_BY_PLUGIN_KEY + "/" + NAME)
    clean()
    yield
    clean()


def test_nothing_is_registered_by_default():
    assert not updates.is_registered(NAME)


def test_register_adds_an_enabled_repository():
    assert updates.register_repository(NAME, URL)
    settings = QgsSettings()
    assert settings.value("app/plugin_repositories/" + NAME + "/url") == URL
    assert settings.value("app/plugin_repositories/" + NAME + "/enabled", type=bool) is True
    assert updates.is_registered(NAME)


def test_an_existing_repository_is_never_overwritten_nor_removed():
    settings = QgsSettings()
    settings.setValue("app/plugin_repositories/" + NAME + "/url", "https://mine.example/plugins.xml")
    settings.setValue("app/plugin_repositories/" + NAME + "/enabled", False)
    assert not updates.register_repository(NAME, URL)
    assert settings.value("app/plugin_repositories/" + NAME + "/url") == "https://mine.example/plugins.xml"
    assert settings.value("app/plugin_repositories/" + NAME + "/enabled", type=bool) is False
    assert not updates.unregister_repository(NAME)  # the user's own entry stays
    assert updates.is_registered(NAME)


def test_unregister_removes_only_what_the_plugin_added():
    updates.register_repository(NAME, URL)
    assert updates.unregister_repository(NAME)
    assert not updates.is_registered(NAME)
    assert not updates.unregister_repository(NAME)  # nothing left to remove
