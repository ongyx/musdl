# coding: utf-8
"""[mus]escore [d]own[l]oader, ported from TypeScript"""

import argparse
import io
import re
import logging
import os
import pathlib
import tempfile
import sys

import bs4 as bsoup
import requests

try:
    from svglib import svglib
    import reportlab.pdfgen.canvas as rlab_canvas
    import reportlab.graphics.renderPDF as rlab_pdf
    _PDF = True
except ImportError:
    _PDF = False

__author__ = "Ong Yong Xin"
__version__ = "2.2.1"
__copyright__ = "(c) 2020 Ong Yong Xin"
__license__ = "MIT"

HOST = "musescore.com"
# regex for download url (base)
RE_BASEURL = re.compile(
    r"(http[s]?://musescore.com/static/musescore/scoredata/gen/[a-zA-Z0-9/]*)score"
)

# only here for backwards compatibility
ALLOWED_FORMATS = frozenset(["mid", "mp3", "mxl", "pdf"])

# logging stuff
_log = logging.getLogger("musdl")
logging.basicConfig()
_log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]


class DownloadError(Exception):
    pass


def _is_valid_char(char):
    return char.isalnum()


def sanitize_filename(name):
    """Sanitise a name so it can be used as a filename.

    Args:
        name (str): The name to sanitise.

    Returns:
        The sanitised name as a string.
    """

    sanitised = "".join([c if _is_valid_char(c) else "_" for c in name])

    # remove duplicate underscores
    return re.sub("_{2,}", "_", sanitised)


class Score(object):
    """A music score on Musescore.

    Args:
        url (str): The score url.

    Attributes:
        name (str): The name of the score.
        soup (bs4.BeautifulSoup): The soup of the score webpage.
        baseurl (str): The 'base' url for downloading a score.
    """

    def __init__(self, url):

        if HOST not in url:
            raise DownloadError("not a musescore url")

        try:
            _log.info(f"downloading score {url}")
            webpage = requests.get(url).content

        except requests.ConnectionError as e:
            raise DownloadError("could not get website data: " + str(e))

        _log.info("parsing score")

        self.soup = bsoup.BeautifulSoup(webpage, "html.parser")
        self.name = self.soup.find("meta", property="og:title")["content"]

        # urls for scores are stored in a js-store class, there is only one per page
        self._class_content = str(self.soup.find_all("div", {"class": "js-store"})[0])

        # base url for score
        self.baseurl = RE_BASEURL.findall(self._class_content)[0]

    def get_url(self, format):
        """Get the url for the format given.
        Note that the PDF format cannot be directly downloaded from a single url,
        use .download('pdf') instead.

        Args:
            format (str): The format. Must be in ALLOWED_FORMATS.

        Returns:
            The url, as a string, or a list of urls (if the format is 'pdf').

        Raises:
            ValueError, if the format is invalid.
        """

        if format not in ALLOWED_FORMATS:
            raise ValueError(f"format invalid: must be [{', '.join(ALLOWED_FORMATS)}]")

        return f"{self.baseurl}score.{format}"

    def _as_pdf(self):
        if not _PDF:
            raise RuntimeError("PDF extra not installed: install with 'pip install musdl[pdf]")

        temp = tempfile.TemporaryDirectory()
        tempdir = pathlib.Path(temp.name)
        
        buffer = io.BytesIO()
        pdf = rlab_canvas.Canvas(buffer)
        
        page = 0

        while True:
            svg = tempdir / f"{page}.svg"
            
            _log.info(f"downloading page ({page}.svg)")
            svg_data = requests.get(f"{self.baseurl}score_{page}.svg")

            if svg_data.status_code == 404:
                _log.info(f"{page} page(s) downloaded")
                break

            elif not svg_data.ok:
                raise DownloadError(f"could not get score pdf page #{page}: {e}")

            with svg.open(mode="wb") as f:
                f.write(svg_data.content)

            _log.info("rendering svg")
            drawing = svglib.svg2rlg(str(svg))

            _log.info(f"adding {page}.png to pdf")
            rlab_pdf.draw(drawing, pdf, 0, 0)
            pdf.showPage()

            page += 1

        _log.info(f"building pdf file")
        pdf.save()
        temp.cleanup()
        return buffer.getvalue()

    def download(self, format):
        """Get the score's data.

        Args:
            format (str): The format to download in.
                Must be in ALLOWED_FORMATS.

        Returns:
            The score's data, as bytes.

        Raises:
            DownloadError, if the score could not be downloaded.
        """

        _log.info(f"downloding score as format '{format}'")

        if format == "pdf":
            return self._as_pdf()

        try:
            score_data = requests.get(self.get_url(format))
            if not score_data.ok:
                raise requests.ConnectionError(score_data.status_code)
        except requests.ConnectionError as e:
            raise DownloadError(f"could not get score data for format '{format}': {e}")
        else:
            return score_data.content


def main(args=None):
    if args == None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(prog="musdl", description=__doc__)

    parser.add_argument(
        "-v", "--verbose", help="be more chatty", action="count", default=1
    )

    parser.add_argument(
        "-V",
        "--version",
        help="print version",
        action="version",
        version="%(prog)s v{}".format(__version__),
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=ALLOWED_FORMATS,
        default="mp3",
        help="format to download, defaults to mp3",
        action="store",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="file to output the score to, otherwise stdout",
        action="store",
    )

    parser.add_argument(
        "-O",
        "--remote-name",
        help="write output to a local file named like the remote file we get",
        action="store_true",
    )

    parser.add_argument("url", help="url of the score", action="store")
    options = parser.parse_args(args)

    _log.setLevel(_log_levels[options.verbose])

    score = Score(options.url)
    score_data = score.download(options.format)

    if options.remote_name:
        filename = f"{sanitize_filename(score.name)}.{options.format}"

    elif options.output:
        filename = options.output

    else:
        print(score_data)
        return 0

    with open(filename, mode="wb") as f:
        f.write(score_data)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
