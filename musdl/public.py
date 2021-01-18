# coding: utf8
"""Public API."""

import logging
import pathlib

import bs4
import requests

from musdl import utils

from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication

_log = logging.getLogger("musdl")
_app = QApplication([])

HOST = "musescore.com"


class API:
    def __init__(self, url: str):

        if HOST not in url:
            raise ValueError("invalid url")

        self.url = url

        self._browser = QWebEngineView()
        self._browser.load(QUrl(url))

        # execute musescore-downloader through a delegate
        self._browser.loadFinished.connect(self._delegate_run_musdl)

    def _delegate_run_musdl(self, status):
        if status:
            js_script = utils.JS_PATH.read_text(encoding="utf8")
            self._browser.page().runJavaScript(js_script)
            self._browser.show()

    def terminal(self):
        while True:
            command = input("> ")
            self._browser.page().runJavaScript(command, lambda rtn: print(rtn))


if __name__ == "__main__":
    api = API("https://musescore.com/classicman/scores/4766391")
    _app.exec_()
