"""
Tests for kapalo-py.
"""

from functools import lru_cache

simple_html_for_matching = """

    <style>html, body {width: 100%;height: 100%;margin: 0;padding: 0;}</style>
    <style>#map {position:absole;top:0;bottom:0;right:0;left:0;}</style>
    <script src="https://cdn.jsivr.net/npm/leaflet@1.6.0/dist/leaflet.js"></script>
    <script src="https://code.jquery.com/jquery-1.12.4.min.js"></script>
    <script src="https://maxcdnootstrap/3.2.0/js/bootstrap.min.js"></script>
    <script src="https://cdnjs.me-markers/2.0.2/leaflet.awesome-markers.js"></script>
    <link rel="stylesheet" hrefdelivr.net/npm/leaflet@1.6.0/dist/leaflet.css"/>
    <link rel="stylesheet" href.com/bootstrap/3.2.0/css/bootstrap.min.css"/>
"""


@lru_cache(maxsize=None)
def test_add_local_stylesheet_params():
    """
    Params for test_add_local_stylesheet.
    """
    return [simple_html_for_matching]
