# -*- coding: utf-8 -*-
from ..core.utils.geocoder import Geocoder


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
