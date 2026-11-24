# -*- coding: utf-8 -*-
"""Plugin language (French / English) that can be switched while QGIS is running."""

from qgis.PyQt.QtCore import QCoreApplication

from .translations import TRANSLATIONS, DictTranslator
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.settings import get_setting, set_setting

LANGUAGES = ("fr", "en")
SETTING_KEY = "language"

_state = {"code": None, "translator": None}


def default_language(locale):
    """English by default, whatever the QGIS locale: French is only used once chosen with the FR / EN toggle."""
    return "en"


def stored_language(locale):
    """The language chosen with the FR/EN toggle, or English if none was chosen yet."""
    code = get_setting(SETTING_KEY, "", str)
    return code if code in LANGUAGES else default_language(locale)


def current_language():
    return _state["code"] or "en"


def uninstall_language():
    """Remove the plugin's translator (on plugin unload)."""
    translator = _state["translator"]
    if translator is not None:
        QCoreApplication.removeTranslator(translator)
    _state["translator"] = None


def set_language(code, remember=True):
    """Switch the plugin to `code` ("fr" or "en"); `remember` stores the choice for the next sessions."""
    if code not in LANGUAGES:
        raise ValueError("unknown language: {}".format(code))
    uninstall_language()
    if code in TRANSLATIONS:  # English is the source language: nothing to install
        # A reference is kept in _state: a garbage collected translator silently stops working
        _state["translator"] = DictTranslator(TRANSLATIONS[code])
        QCoreApplication.installTranslator(_state["translator"])
    _state["code"] = code
    if remember:
        set_setting(SETTING_KEY, code)


def all_names(msgid):
    """Every name `msgid` can have: English, the current language and all the built-in translations.

    Used to find the plugin's layers and group whatever language they were created in.
    """
    return {msgid, tr(msgid)} | {texts[msgid] for texts in TRANSLATIONS.values() if msgid in texts}


class TrAttr:
    """Class attribute whose value is translated each time it is read (so it follows the language switch)."""

    def __init__(self, msgid):
        self.msgid = msgid

    def __get__(self, obj, owner=None):
        return tr(self.msgid)
