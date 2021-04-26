# config: utf8
"""[mus]escore [d]own[l]oader, ported from TypeScript"""

import io
import logging
import pathlib
import re
import subprocess
import tempfile
import zipfile
from datetime import datetime
from typing import Any, Dict, Union
from urllib.parse import urlparse

import bs4
import requests

__author__ = "Ong Yong Xin"
__version__ = "3.1.2"
__copyright__ = "(c) 2020 Ong Yong Xin"
__license__ = "MIT"

_log = logging.getLogger("musdl")

IPNS_KEY = "QmSdXtvzC8v8iTTZuj5cVmiugnzbR1QATYRcGix4bBsioP"
IPNS_RS_URL = f"https://ipfs.io/api/v0/dag/resolve?arg=/ipns/{IPNS_KEY}"
RADIX = 20
INDEX_RADIX = 128

# set for fast lookup
EXPORT_FORMATS = frozenset(["pdf", "mscz", "mxl", "mid", "mp3", "flac", "ogg"])


def _soup_from_str(content):
    # stop beautifulsoup complaining about parsers
    return bs4.BeautifulSoup(content, "html.parser")


def _sanitize(filename):
    return re.sub(
        "_{2,}", "_", "".join([c if c.isalnum() else "_" for c in filename])
    ).strip("_")


class Score:
    """A score stored on disk (as a .mscz file).

    Args:
        score_data: The score data as bytes.
            It must be in the mscz format.

    Attributes:
        meta (dict): A map of metadata tags to their values.
            Currently, the following tags are used:

            arranger
            composer
            copyright
            lyricist
            movementNumber
            movementTitle
            poet
            workNumber
            workTitle (str): Self-explainatory.

            creationDate (datetime.datetime): When the score was created.

            platform (str): Which OS the score was created on (i.e Microsoft Windows).

            source (str): The URL of the score (if it was hosted online).

        scorexml (bs4.BeautifulSoup): The parsed score (from XML).
    """

    def __init__(self, score_data: bytes) -> None:
        self._buffer = io.BytesIO(score_data)

        with zipfile.ZipFile(self._buffer) as zf:

            container = _soup_from_str(zf.read("META-INF/container.xml"))
            # The 'correct' way to find the .mscx file
            mscx_path = container.rootfiles.rootfile["full-path"]

            self.scorexml = _soup_from_str(zf.read(mscx_path))

        self.meta: Dict[str, Any] = {}

        for tag in self.scorexml.find_all("metatag"):
            key = tag["name"]
            value = tag.text
            if key == "creationDate":
                value = datetime.strptime(value, "%Y-%m-%d")

            self.meta[key] = value

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()

    def as_mscz(self) -> bytes:
        """
        Get the raw mscz file.

        Returns:
            The .mscz file, as raw bytes.
        """

        return self._buffer.getvalue()

    def close(self):
        self.scorexml.decompose()

    def export(self, fmt: str, path: Union[str, pathlib.Path]) -> pathlib.Path:
        """Export this score to another format and save it.
        The format must be one of ['pdf', 'mscz', 'mxl', 'mid', 'mp3', 'flac', 'ogg'].

        Args:
            fmt: The export format.
            path: Where to save the export file to.
                The path should not have an extension, because it will be replaced
                by the correct extension for the export format.

        Returns:
            The path to the exported file (with correct extension).

        Raises:
            ValueError, if the format is invalid.
        """

        path = pathlib.Path(path).with_suffix(f".{fmt}")

        if fmt not in EXPORT_FORMATS:
            raise ValueError(f"invalid format {fmt}")

        if fmt == "mscz":
            # save as-is
            path.write_bytes(self.as_mscz())

        else:
            # save to a tempfile because we have to export using musescore
            with tempfile.NamedTemporaryFile(suffix=".mscz") as f:
                f.write(self.as_mscz())

                try:
                    subprocess.run(
                        ["mscore", f.name, "-o", path],
                        check=True,
                    )

                except FileNotFoundError:
                    _log.critical(
                        "musescore is not installed yet (required for export)"
                    )
                    raise

                except subprocess.CalledProcessError as e:
                    _log.error(f"failed to export: {e}")
                    raise

        return path

    @staticmethod
    def from_file(path: Union[str, pathlib.Path]):
        """Open a score from an existing .mscz file.

        Args:
            path: The path to the file.

        Returns:
            The score object.
        """

        with open(path, "rb") as f:
            return Score(f.read())


class OnlineScore(Score):
    """A score hosted on musescore.

    Args:
        url: The url to the score.

    Attributes:
        global_cid (str): The 'global key' used to access the mscz cid.
        mscz_cid (str): The 'mscz key' (specific to each score) used to access the mscz url.
        mscz_url (str): The url to the .mscz file.
        session (requests.Session): The session used to get the CID, as well as the .mscz file.
    """

    def __init__(self, url: str) -> None:
        self.id = int(urlparse(url).path.split("/")[-1])
        self.session = requests.Session()

        _log.info("getting global/score cid (this might take a while)")

        with self.session.get(IPNS_RS_URL) as res:
            self.global_cid = res.json()["Cid"]["/"]

        mscz_cid_url = (
            "https://ipfs.infura.io:5001/api/v0/block/stat?arg="
            f"/ipfs/{self.global_cid}/{self.id % RADIX}/{self.id}.mscz"
        )

        with self.session.get(mscz_cid_url) as res:
            data = res.json()
            self.mscz_cid = data.get("Key")

            if not self.mscz_cid:
                err_msg = data["Message"]
                if "no link named" in err_msg:
                    err_msg = (
                        "Score is not in dataset. "
                        "Please file a bug report in the #dataset-bugs channel "
                        "of the LibreScore Community Discord server: "
                        "https://discord.gg/kTyx6nUjMv"
                    )
                raise RuntimeError(err_msg)

            self.mscz_url = f"https://ipfs.infura.io/ipfs/{self.mscz_cid}"

        _log.info("OK (cid is <%s>, mscz cid is <%s>)", self.global_cid, self.mscz_cid)
        _log.info("downloading .mscz file")

        with self.session.get(self.mscz_url) as response:
            super().__init__(response.content)

        _log.info("downloaded .mscz file")

    def close(self):
        self.session.close()
        self._buffer.close()
        super().close()


def main():
    import argparse

    logging.basicConfig(level=logging.INFO, format=" %(levelname)-8s :: %(message)s")
    parser = argparse.ArgumentParser(prog="musdl", description=__doc__)

    parser.add_argument(
        "-V",
        "--version",
        help="print version",
        action="version",
        version="%(prog)s v{}".format(__version__),
    )

    parser.add_argument("url", help="the score url")

    parser.add_argument(
        "--output",
        "-o",
        help="directory to output score file to (default: %(default)s)",
        default=".",
    )

    parser.add_argument(
        "--format",
        "-f",
        help="export the mscz file to another format (default: %(default)s)",
        choices=EXPORT_FORMATS,
        default="mscz",
    )

    args = parser.parse_args()

    with OnlineScore(args.url) as score:

        filename = pathlib.Path(args.output) / f"{_sanitize(score.meta['workTitle'])}"

        _log.info("saving")

        exported_filename = score.export(args.format, filename)

        _log.info("saved to %s", exported_filename)


if __name__ == "__main__":
    main()
