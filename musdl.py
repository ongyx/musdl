# config: utf8
"""[mus]escore [d]own[l]oader, ported from TypeScript"""

from __future__ import annotations

import io
import logging
import pathlib
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union
from urllib.parse import urlparse

import bs4  # type: ignore
import requests

__author__ = "Ong Yong Xin"
__version__ = "3.1.7"
__copyright__ = "(c) 2020 Ong Yong Xin"
__license__ = "MIT"

_log = logging.getLogger("musdl")

IPNS_KEY = "QmSdXtvzC8v8iTTZuj5cVmiugnzbR1QATYRcGix4bBsioP"
IPNS_RS_URL = f"https://ipfs.io/api/v0/dag/resolve?arg=/ipns/{IPNS_KEY}"
RADIX = 20
INDEX_RADIX = 128

# set for fast lookup
EXPORT_FORMATS = frozenset(["pdf", "mscz", "mxl", "mid", "mp3", "flac", "ogg"])

MSCORE_EXE = shutil.which("musescore3") or shutil.which("musescore")

# This maps Score metadata fields to their meta property (on the musescore webpage).
META_MAP = {
    "arranger": "musescore:author",
    "composer": "musescore:composer",
    "workTitle": "og:title",
    "source": "og:url",
}


def _soup_from_str(content):
    # stop beautifulsoup complaining about parsers
    return bs4.BeautifulSoup(content, "html.parser")


def _sanitize(filename):
    return re.sub(
        "_{2,}", "_", "".join([c if c.isalnum() else "_" for c in filename])
    ).strip("_")


def _normalize(field):
    return re.sub(r"([A-Z]){1}", lambda m: f"_{m.group(1).lower()}", field)


def _get_id(url):
    return int(urlparse(url).path.split("/")[-1])


@dataclass
class Metadata(Mapping):
    """A score's metadata.

    Attributes:

        arranger: Who arranged the score.

        composer: Who composed the score.

        copyright: The copyright statement.

        creation_date: When the score was created.

        lyricist: Who created the lyrics for the score.

        movement_number: Self-explainatory.

        movement_title: Self-explainatory.

        platform: Which OS the score was created on (i.e Microsoft Windows).

        poet: Who created the poem the score's lyrics is based on, if any.

        source: The URL of the score (if it was hosted online).

        translator: Who translated the lyrics of the score, if any.

        work_number: Self-explainatory.

        work_title: Self-explainatory.
    """

    arranger: str
    composer: str
    copyright: str
    creation_date: Optional[datetime]
    lyricist: str
    movement_number: str
    movement_title: str
    platform: str
    poet: str
    source: str
    translator: str
    work_number: str
    work_title: str

    def __getitem__(self, field):
        return self.__dict__[_normalize(field)]

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        return iter(self.__dict__)

    @classmethod
    def from_xml(cls, scorexml: bs4.Tag) -> Metadata:
        metadata = {
            _normalize(tag["name"]): tag.text for tag in scorexml.find_all("metatag")
        }

        created = metadata["creation_date"]

        created_date: Optional[datetime]

        try:
            created_date = datetime.strptime(created, "%Y-%m-%d")
        except ValueError:
            created_date = None

        metadata["creation_date"] = created_date

        return cls(**metadata)


class Score:
    """A score stored on disk (as a .mscz file).

    Args:
        score_data: The score data as bytes.
            It must be in the mscz format.

    Attributes:
        meta (Metadata): A map of metadata tags to their values.
            Attribute-like access is also supported.

        scorexml (bs4.BeautifulSoup): The parsed score (from XML).
    """

    def __init__(self, score_data: bytes) -> None:
        self._buffer = io.BytesIO(score_data)

        with zipfile.ZipFile(self._buffer) as zf:

            container = _soup_from_str(zf.read("META-INF/container.xml"))
            # The 'correct' way to find the .mscx file
            mscx_path = container.rootfiles.rootfile["full-path"]

            self.scorexml = _soup_from_str(zf.read(mscx_path))

        self.meta = Metadata.from_xml(self.scorexml)

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

        temp = tempfile.NamedTemporaryFile(suffix=".mscz", delete=False)
        temp_path = pathlib.Path(temp.name)

        temp.write(self.as_mscz())

        if fmt == "mscz":
            temp.close()
            # renames only work on the same filesystem
            # copy and then delete ensures that it will move across filesystems
            # (shutil does this for us)
            shutil.move(str(temp_path), str(path))

        else:

            if MSCORE_EXE is None:
                raise RuntimeError(
                    "musescore is not installed yet (required for export)"
                )

            # save to a tempfile because we have to export using musescore
            try:
                subprocess.run(
                    [MSCORE_EXE, str(temp_path), "-o", str(path)],
                    check=True,
                )

            except subprocess.CalledProcessError as e:
                _log.error(f"failed to export: {e.output}")
                raise

            finally:
                temp.close()
                temp_path.unlink()

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
        url: See args.
        global_cid (str): The 'global key' used to access the mscz cid.
        mscz_cid (str): The 'mscz key' (specific to each score) used to access the mscz url.
        mscz_url (str): The url to the .mscz file.
        session (requests.Session): The session used to get the CID, as well as the .mscz file.
    """

    def __init__(self, url: str) -> None:
        self.url = url
        self.session = requests.Session()

        self._soup = _soup_from_str(self.session.get(self.url).text)

        self.id = _get_id(self._soup.find("meta", property="al:ios:url")["content"])

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

    def update_meta(self):
        """Update the metadata in this score using the musescore webpage.
        Note that this does not modify the dataset score itself: only the .meta attribute is updated.
        """

        for field, prop in META_MAP.items():
            value = self._soup.find("meta", property=prop)
            if value is None:
                _log.warning("failed to update metadata field %s", field)
            else:
                # setting of metadata fields after creation is not allowed (not a MutableMapping).
                # uUless you go through the instance dict.
                self.meta.__dict__[field] = value["content"]

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

    parser.add_argument("url", help="the score url", nargs="?", default=None)

    parser.add_argument(
        "-o",
        "--output",
        help="directory to output score file(s) to (default: %(default)s)",
        default=".",
    )

    parser.add_argument(
        "-f",
        "--format",
        help="export the mscz file(s) to another format (default: %(default)s)",
        choices=EXPORT_FORMATS,
        default="mscz",
    )

    parser.add_argument(
        "-d",
        "--dont-update",
        help="use the dataset score's workTitle as the filename (may be outdated or empty!)",
        action="store_true",
    )

    parser.add_argument(
        "-b",
        "--batch",
        help="read a score url from each line of a file and download it",
    )

    args = parser.parse_args()

    output = pathlib.Path(args.output)

    if (args.batch and args.url) or (not args.batch and not args.url):
        _log.critical("Only one of url or --batch must be specified.")
        return

    if args.batch:
        # iterate over lines
        urls = open(args.batch, "r")
    else:
        urls = [args.url]

    for url in urls:

        with OnlineScore(url) as score:

            if not args.dont_update:
                _log.info("updating metadata")

                score.update_meta()

            filename = output / f"{_sanitize(score.meta.work_title)}"

            _log.info("saving")

            exported_filename = score.export(args.format, filename)

            _log.info("saved to %s", exported_filename)

    try:
        urls.close()
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
