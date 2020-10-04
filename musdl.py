# coding: utf-8
"""musdl: Pure Python score downloader for
Musescore."""

import argparse
import re
import logging
import os
import pathlib
import tempfile
import subprocess
import sys

import bs4 as bsoup
import fpdf
import requests

__author__ = "Ong Yong Xin"
__version__ = "2.1.0"
__copyright__ = "(c) 2020 Ong Yong Xin"
__license__ = "MIT"

HOST = "musescore.com"
# regex for download url (base)
RE_BASEURL = re.compile(r"(http[s]?://musescore.com/static/musescore/scoredata/gen/[a-zA-Z0-9/]*)score")

# only here for backwards compatibility
ALLOWED_FORMATS = frozenset(["mid", "mp3", "mxl", "pdf"])
PDF_RES = [2100, 2970]

# logging stuff
_log = logging.getLogger("musdl")
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
    
    sanitised = "".join([
        c if _is_valid_char(c) else "_"
        for c in name
    ])
    
    # remove duplicate underscores
    return re.sub("_{2,}", "_", sanitised)


def _find_inkscape():
    args = ["which", "inkscape"]
        
    if os.name == "nt":
        args[0] = "where"
    
    try:
        return subprocess.check_output(args).strip()
    except subprocess.CalledProcessError:
        return None


def _convert_svg_to_png(svg_path, png_path, wh):
    
    width, height = wh
    inkscape_path = _find_inkscape()
    
    if inkscape_path is None:
        raise RuntimeError("inkscape not found: please install first")
    
    args = [
        inkscape_path,
        "--without-gui",
        "-f", svg_path,
        "--export-area-page",
        "-w", str(width),
        "-h", str(height),
        f"--export-png={png_path}"
    ]
    
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError("failed to run inkscape: exited with non-zero status code")


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
    
    def _as_pdf(self, pdf_scale):
        # pdf is made of a few images
        pdf = fpdf.FPDF()
        
        tempdir = tempfile.TemporaryDirectory()
        temp = pathlib.Path(tempdir.name)
        page = 0
        
        while True:
            svg = temp / f"{page}.svg"
            png = temp / f"{page}.png"
            
            _log.info(f"downloading page ({page}.svg)")
            svg_data = requests.get(f"{self.baseurl}score_{page}.svg")
            
            if svg_data.status_code == 404:
                _log.info(f"{page} page(s) downloaded")
                break
            
            elif not svg_data.ok:
                raise DownloadError(f"could not get score pdf page #{page}: {e}")
            
            with open(svg, "wb") as f:
                f.write(svg_data.content)
            
            _log.info(f"converting {page}.svg to png")
            _convert_svg_to_png(svg, png, pdf_scale)
            
            _log.info(f"adding {page}.png to pdf")
            pdf.add_page()
            pdf.image(str(png), x=0, y=0, w=210, h=297)
            
            page += 1
        
        _log.info(f"building pdf file")
        data = pdf.output(dest='S').encode('latin-1')
        tempdir.cleanup()
        return data
                
    def download(self, format, pdf_scale=PDF_RES):
        """Get the score's data.
        
        Args:
            format (str): The format to download in.
                Must be in ALLOWED_FORMATS.
            pdf_scale (list): If the format is 'pdf', how high the resolution of the pdf should be.
                Defaults to PDF_RES.
        
        Returns:
            The score's data, as bytes.
        
        Raises:
            DownloadError, if the score could not be downloaded.
        """
        
        _log.info(f"downloding score as format '{format}'")
        
        if format == "pdf":
            return self._as_pdf(PDF_RES)
        
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
        "-v",
        "--verbose",
        help="be more chatty",
        action="count",
        default=1
    )

    parser.add_argument(
        "-V",
        "--version",
        help="print version",
        action="version",
        version="%(prog)s v{}".format(__version__)
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=ALLOWED_FORMATS,
        default="mp3",
        help="format to download, defaults to mp3",
        action="store"
    )
    
    parser.add_argument(
        "-s",
        "--scale",
        default=5,
        help=f"scale to render PDF at (1x resolution: width={PDF_RES[0]}, height={PDF_RES[1]}), defaults to 5",
        action="store",
        type=int
    )

    parser.add_argument(
        "-o",
        "--output",
        help="file to output the score to, otherwise stdout",
        action="store"
    )
    
    parser.add_argument(
        "-O",
        "--remote-name",
        help='write output to a local file named like the remote file we get',
        action='store_true'
    )

    parser.add_argument("url", help="url of the score", action="store")
    options = parser.parse_args(args)

    _log.setLevel(
        _log_levels[options.verbose]
    )

    score = Score(options.url)
    
    scale = [r * options.scale for r in PDF_RES]
    score_data = score.download(options.format, pdf_scale=scale)
    
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
