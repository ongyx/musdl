# coding: utf-8
#!/usr/bin/env python3
"""musdl: Pure Python score downloader for
Musescore."""

import argparse
import re
import sys

import bs4 as bsoup
import requests

__author__ = "Ong Yong Xin, JPFrancoia"
__version__ = "1.1.0"
__copyright__ = "(c) 2020 Ong Yong Xin, JPFrancoia"
__license__ = "MIT"

REGEXES = {
    "midi": r"http[s]?://musescore.com/static/musescore/scoredata/gen/[a-zA-Z0-9/]*score\.mid",
    "mp3": r"http[s]?://nocdn.musescore.com/static/musescore/scoredata/gen/[a-zA-Z0-9/]*score\.mp3",
    "mxl": r"http[s]?://nocdn.musescore.com/static/musescore/scoredata/gen/[a-zA-Z0-9/]*score\.mp3",
}

ALLOWED_FORMATS = ["mp3", "midi", "mxl"]


class DownloadError(Exception):
    pass


def download_score(format, url):
    """Download a score from Musescore,
    returning its raw byte data.
    
    Parameters
    ----------
    format : str
        The format to download. Must be
        'midi' or 'mp3'.
    url : str
        The URL of the score.
    """
    if "musescore.com" not in url:
        raise DownloadError("not a musescore url")
    elif format not in ALLOWED_FORMATS:
        raise DownloadError("format must be mid or mp3")
    else:
        re_score = REGEXES[format]

    try:
        soup = bsoup.BeautifulSoup(requests.get(url).content, "html5lib")
    except requests.ConnectionError as e:
        raise DownloadError("could not get website data: " + str(e))

    # urls for scores are stored in a js-store class, there is only one per page
    class_content = str(soup.find_all("div", {"class": "js-store"})[0])
    score_data_url = re.findall(re_score, class_content)[0]

    # The URL for the mxl file is not present in the downloaded html page and it is
    # built from the mp3 URL
    if format == "mxl":
        score_data_url = re.sub(r"\.mp3$", ".mxl", score_data_url, flags=re.IGNORECASE)

    try:
        score_data = requests.get(score_data_url)
    except requests.ConnectionError as e:
        raise DownloadError("could not get score data: " + str(e))
    else:
        return score_data.content


def main(args=None):
    if args == None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(prog="musdl", description=__doc__)

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

    parser.add_argument("url", help="url of the score", action="store")
    options = parser.parse_args(args)

    score_data = download_score(options.format, options.url)

    if options.output:
        with open(options.output, mode="wb") as f:
            f.write(score_data)

    else:
        print(score_data)


if __name__ == "__main__":
    main(sys.argv[1:])
