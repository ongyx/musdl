# coding: utf8
"""lol"""

import pathlib
import signal
import sys

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineScript

__version__ = "4.0.0"

_app = QApplication([])

MODULE = pathlib.Path(__file__).parent
WEBMSCORE = MODULE / "webmscore.js"


class Score:
    def __init__(self, url: str):
        self.browser = QWebEngineView()

        # inject webmscore runtime
        with WEBMSCORE.open(encoding="utf8") as f:
            runtime = QWebEngineScript()
            runtime.setName("webmscore")
            runtime.setSourceCode(f.read())

        self.browser.page().scripts().insert(runtime)

        self.browser.load(QUrl(url))

        self.browser.show()


if __name__ == "__main__":
    score = Score("https://musescore.com/classicman/scores/4766391")

    # since there is no gui (yet), catch Control-C.
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(_app.exec_())
