# -*- coding: utf-8 -*-
import time

from qgis.PyQt.QtCore import QEventLoop, QTimer

from ..core.utils.geocoder import Geocoder, MIN_REQUEST_INTERVAL_MS


def test_build_url_uses_search_endpoint_with_encoded_query():
    url = Geocoder.build_url("café & thé", 3)
    text = bytes(url.toEncoded()).decode()  # what is actually sent on the wire
    assert url.path() == "/search"  # the old "/search/<query>" form now answers 404
    assert " " not in text
    assert "format=geojson" in text and "limit=3" in text
    assert "caf%C3%A9" in text and "%26" in text  # accent and '&' encoded


def test_parse_features():
    features = [{
        'properties': {'display_name': 'Yaoundé, Mfoundi, Région du Centre, Cameroun'},
        'geometry': {'coordinates': [11.52, 3.86]},
    }]
    assert Geocoder.parse_features(features) == {'Yaoundé, Mfoundi, Région du Centre (Cameroun)': [11.52, 3.86]}


def test_parse_features_single_part_name():
    features = [{'properties': {'display_name': 'Atlantis'}, 'geometry': {'coordinates': [0, 0]}}]
    assert Geocoder.parse_features(features) == {'Atlantis': [0, 0]}


def test_no_delay_for_the_first_request():
    assert Geocoder(lambda results: None).delay_before_next_request(time.monotonic()) == 0


def test_delay_to_respect_one_request_per_second():
    geocoder = Geocoder(lambda results: None)
    geocoder._last_request_time = 100.0
    assert 790 <= geocoder.delay_before_next_request(100.2) <= 810
    assert geocoder.delay_before_next_request(100.0 + MIN_REQUEST_INTERVAL_MS / 1000 + 0.5) == 0


def test_rapid_searches_are_spaced_by_one_second_and_only_the_latest_is_sent():
    geocoder = Geocoder(lambda results: None)
    sent = []
    geocoder._do_request = lambda query, max_results: sent.append((query, time.monotonic()))
    geocoder.geocode("a", 5)  # goes out at once
    geocoder.geocode("b", 5)  # replaced by "c" while waiting
    geocoder.geocode("c", 5)
    assert [query for query, _ in sent] == ["a"]
    loop = QEventLoop()
    QTimer.singleShot(1500, loop.quit)
    loop.exec()
    assert [query for query, _ in sent] == ["a", "c"]
    assert sent[1][1] - sent[0][1] >= MIN_REQUEST_INTERVAL_MS / 1000 - 0.02
