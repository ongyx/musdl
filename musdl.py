# coding: utf-8
"""musdl: Pure Python score downloader for
Musescore."""

import argparse
import re
import sys

import bs4 as bsoup
import requests

__author__ = "Ong Yong Xin, JPFrancoia"
__version__ = "2.0.2"
__copyright__ = "(c) 2020 Ong Yong Xin, JPFrancoia"
__license__ = "MIT"

HOST = "musescore.com"
REGEXES = {
    "mid": re.compile(r"http[s]?://musescore.com/static/musescore/scoredata/gen/[a-zA-Z0-9/]*score\.mid"),
    "mp3": re.compile(r"http[s]?://nocdn.musescore.com/static/musescore/scoredata/gen/[a-zA-Z0-9/]*score\.mp3"),
    "mxl": re.compile(r"http[s]?://nocdn.musescore.com/static/musescore/scoredata/gen/[a-zA-Z0-9/]*score\.mp3"),
}

# only here for backwards compatibility
ALLOWED_FORMATS = frozenset(REGEXES.keys())


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


class Score(object):
    """A music score on Musescore.
    
    Args:
        url (str): The score url.
    
    Attributes:
        soup (bs4.BeautifulSoup): The soup of the score webpage.
        urls (dict): A map of score formats to their urls.
    """
    
    def __init__(self, url):
        self.urls = {}
        
        if HOST not in url:
            raise DownloadError("not a musescore url")
        
        try:
            webpage = requests.get(url).content
            
        except requests.ConnectionError as e:
            raise DownloadError("could not get website data: " + str(e))
        
        self.soup = bsoup.BeautifulSoup(webpage, "html5lib")
        self.name = self.soup.find("meta", property="og:title")["content"]
        
        # urls for scores are stored in a js-store class, there is only one per page
        self._class_content = str(self.soup.find_all("div", {"class": "js-store"})[0])
    
    def get_url(self, format):
        """Get the url for the format given.
        
        Args:
            format (str): The format. Must be in ALLOWED_FORMATS.
        
        Returns:
            The url, as a string.
        
        Raises:
            ValueError, if the format is invalid.
        """
        
        if format in self.urls:
            return self.urls[format]
        
        regex = REGEXES.get(format)
        if regex is None:
            raise ValueError(f"format invalid: must be [{', '.join(ALLOWED_FORMATS)}]")
        
        url = regex.findall(self._class_content)[0]
        if format == "mxl":
            # The URL for the mxl file is not present in the downloaded html page and it is
            # built from the mp3 URL
            url = re.sub(r"\.mp3$", ".mxl", url, flags=re.IGNORECASE)
        
        self.urls[format] = url
        return url
    
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
        
        try:
            score_data = requests.get(self.get_url(format))
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
    
    parser.add_argument(
        "-O",
        "--remote-name",
        help='write output to a local file named like the remote file we get',
        action='store_true'
    )

    parser.add_argument("url", help="url of the score", action="store")
    options = parser.parse_args(args)

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
