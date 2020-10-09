# coding: utf-8
"""[mus]escore [d]own[l]oader, ported from TypeScript"""

import argparse
import io
import json
import logging
import os
import pathlib
import re
import sys
import tempfile
from multiprocessing.pool import ThreadPool

import bs4 as bsoup
import requests

try:
    import reportlab.graphics.renderPDF as rlab_pdf
    import reportlab.lib.pagesizes as rlab_pagesizes
    import reportlab.pdfgen.canvas as rlab_canvas
    from svglib import svglib

    _PDF = True
except ImportError:
    _PDF = False

__author__ = "Ong Yong Xin"
__version__ = "2.3.1"
__copyright__ = "(c) 2020 Ong Yong Xin"
__license__ = "MIT"

HOST = "musescore.com"
# regex for download url (base)
RE_BASEURL = re.compile(
    r"(http[s]?://musescore.com/static/musescore/scoredata/gen/[a-zA-Z0-9/]*)/score"
)
# regex for page url
RE_PAGEURL = re.compile(r"http[s]?://musescore.com/user/(\d+)/scores/(\d+)$")
RE_JSONP = re.compile(r"^jsonp\d+\((.*)\)$")

# only here for backwards compatibility
ALLOWED_FORMATS = frozenset(["mid", "mp3", "mxl", "pdf"])
# number of threads to use
THREADS = os.cpu_count() or 8

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
        id (int): The score id.
        user (int): The user id that uploaded the score.
        pages (int): The number of pages in the score. Note that pages start from 0.
        soup (bs4.BeautifulSoup): The soup of the score webpage.
        baseurl (str): The 'base' url of the score (where it can be downloaded).
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
        self.user, self.id = RE_PAGEURL.findall(
            self.soup.find("meta", property="og:url")["content"]
        )[0]

        # urls for scores are stored in a js-store class, there is only one per page
        self._class_content = str(self.soup.find_all("div", {"class": "js-store"})[0])

        # base url for score
        self.baseurl = RE_BASEURL.findall(self._class_content)[0]
        self._pages = None

    @property
    def pages(self):
        if self._pages is not None:
            return self._pages

        pages = set()
        jsonp = requests.get(f"{self.baseurl}/space.jsonp").text
        # clean up content so it can be parsed as json
        actual_json = json.loads(RE_JSONP.findall(jsonp)[0])
        for section in actual_json["space"]:
            pages.add(section["page"])

        self._pages = len(pages)
        return self._pages

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

        return f"{self.baseurl}/score.{format}"

    def _get_pdf_page(self, page):
        # this does not render the svg, it just downloads first.
        svg = self._tempdir / f"{page}.svg"

        _log.info(f"downloading page ({page}.svg)")
        svg_data = requests.get(f"{self.baseurl}/score_{page}.svg", stream=True)

        if not svg_data.ok:
            raise DownloadError(
                f"could not get score pdf page #{page}: status code {svg_data.status_code}"
            )

        with svg.open(mode="wb") as f:
            f.write(svg_data.content)

        return svg

    def _get_pdf(self, gotta_go_fast=False):
        if not _PDF:
            raise RuntimeError(
                "PDF extra not installed: install with 'pip install musdl[pdf]"
            )

        temp = tempfile.TemporaryDirectory()
        self._tempdir = pathlib.Path(temp.name)

        buffer = io.BytesIO()
        pdf = rlab_canvas.Canvas(buffer)
        width, height = rlab_pagesizes.A4

        if gotta_go_fast:
            pool = ThreadPool(THREADS)
            svgs = pool.imap(self._get_pdf_page, range(self.pages))
            pool.close()
            pool.join()

        else:
            svgs = [self._get_pdf_page(s) for s in range(self.pages)]

        _log.info(f"{self.pages} page(s) downloaded")

        for page, svg in enumerate(svgs):
            _log.info(f"rendering svg for page {page}")
            drawing = svglib.svg2rlg(str(svg))
            # scale drawing
            drawing.scale(width / drawing.width, height / drawing.height)

            _log.info(f"adding {page}.png to pdf")
            rlab_pdf.draw(drawing, pdf, 0, 0)
            pdf.showPage()

        _log.info(f"building pdf file")
        pdf.save()
        temp.cleanup()
        del self._tempdir
        return buffer.getvalue()

    def download(self, format, threaded=False):
        """Get the score's data.
        Args:
            format (str): The format to download in.
                Must be in ALLOWED_FORMATS.
            threaded (bool): Whether or not to use threads to download pages (if format was 'pdf'.)
                Defaults to False.
        Returns:
            The score's data, as bytes.
        Raises:
            DownloadError, if the score could not be downloaded.
        """

        _log.info(f"downloding score as format '{format}'")

        if format == "pdf":
            return self._get_pdf(gotta_go_fast=threaded)

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
        "-t",
        "--threaded",
        default=False,
        help="whether or not to use threads to download pdf pages, defaults to False",
        action="store_true",
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
    score_data = score.download(options.format, threaded=options.threaded)

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
