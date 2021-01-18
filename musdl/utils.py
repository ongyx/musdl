# coding: utf8
"""Utilities."""

import logging
import pathlib
import requests

_log = logging.getLogger("musdl")

JS_URL = (
    "https://raw.githubusercontent.com/Xmader/musescore-downloader/master/dist/main.js"
)

MODULE_PATH = pathlib.Path(__file__).parent
JS_PATH = MODULE_PATH / "musdl.js"
ETAG_PATH = MODULE_PATH / "etag"


def _download_js():
    try:
        etag = ETAG_PATH.read_text()
    except FileNotFoundError:
        etag = ""

    with requests.get(JS_URL, stream=True) as response:
        _log.info("checking for latest musescore-downloader script")
        if response.headers["ETag"] != etag:
            _log.info("new version found, downloading")
            JS_PATH.write_text(response.text, encoding="utf8")
        else:
            _log.info("already at latest version")
