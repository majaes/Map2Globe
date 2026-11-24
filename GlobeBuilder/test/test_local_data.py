# -*- coding: utf-8 -*-
import os

from ..core.utils.utils import local_data_copy
from ..definitions.settings import LOCAL_DATA_DIR


def test_local_data_copy_is_outside_plugin_folder_and_identical():
    source = os.path.join(LOCAL_DATA_DIR, 'ne_110m_admin_0_countries.geojson')
    copy = local_data_copy(source)
    assert os.path.normpath(copy) != os.path.normpath(source)
    assert not os.path.normpath(copy).startswith(os.path.normpath(LOCAL_DATA_DIR))
    assert os.path.getsize(copy) == os.path.getsize(source)
    # second call reuses the copy
    assert local_data_copy(source) == copy


def test_local_data_copy_falls_back_to_original_when_source_missing(tmp_path):
    missing = str(tmp_path / 'does_not_exist.geojson')
    assert local_data_copy(missing) == missing
